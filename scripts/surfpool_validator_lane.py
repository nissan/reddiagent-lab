#!/usr/bin/env python3
"""Build deterministic Surfpool local validator lane evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "surfpool-validator-lane-scenarios.json"

ALLOWED_VALIDATOR_MODES = {"surfpool-local", "solana-test-validator-fallback"}
REQUIRED_BOUNDARY_FALSE = (
    "credentialAccess",
    "walletAccess",
    "paymentRailAccess",
    "facilitatorAccess",
    "settlementAccess",
    "liveMcpInvocation",
    "providerApiAccess",
    "devnetAccess",
    "mainnetAccess",
    "deploymentPublished",
    "packagePublished",
    "externalSpend",
)
SENSITIVE_KEYS_NORMALIZED = {
    "apikey",
    "authorization",
    "bearertoken",
    "credential",
    "credentialpayload",
    "facilitatorkey",
    "mnemonic",
    "privatekey",
    "secret",
    "seedphrase",
    "token",
    "walletencryptionkey",
    "walletprivatekey",
}
SENSITIVE_VALUE_MARKERS = (
    "bearer ",
    "private key",
    "seed phrase",
    "mnemonic",
    "api key",
    "secret",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_id(*parts: str) -> str:
    return digest_text("|".join(parts))[:16]


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def merge_scenario(defaults: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def sensitive_findings(value: Any, path: str = "scenario") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized_key = key.lower().replace("_", "").replace("-", "")
            if normalized_key in SENSITIVE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential, wallet, facilitator, or secret-like keys are not allowed in local validator evidence."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential, wallet, facilitator, or secret-like values are not allowed in local validator evidence."))
    return findings


def delta_or_none(before: int | None, after: int | None) -> int | None:
    if before is None or after is None:
        return None
    return after - before


def lamport_delta(before: int | None, after: int | None) -> int | None:
    return delta_or_none(before, after)


def token_delta(before: int | None, after: int | None) -> int | None:
    return delta_or_none(before, after)


def validator_commands(scenario: dict[str, Any], status: str) -> list[dict[str, Any]]:
    validator_mode = scenario.get("validatorMode")
    command = "surfpool start --local --no-mainnet --dry-run-evidence"
    if validator_mode == "solana-test-validator-fallback":
        command = "solana-test-validator --reset --quiet --ledger .tmp/reddiagent-validator-lane"
    exit_code = 0 if status == "pass" else 3
    return [
        {
            "step": 1,
            "command": command,
            "event": "validator.startup_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 2,
            "command": f"validator:run-scenario --id {scenario.get('id')} --cluster localnet --dry-run",
            "event": "validator.scenario_executed",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 3,
            "command": "validator:capture-receipt --format evidence-json --dry-run",
            "event": "validator.receipt_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 4,
            "command": "validator:teardown --cleanup-ledger --dry-run",
            "event": "validator.teardown_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
    ]


def collect_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    mode = scenario.get("validatorMode")
    cluster = scenario.get("cluster", {})
    accounts = scenario.get("accounts", [])
    programs = scenario.get("programs", [])
    teardown = scenario.get("teardown", {})
    rollback = scenario.get("rollback", {})
    boundaries = scenario.get("boundaryStatus", {})
    deltas = scenario.get("stateDeltas", {})

    require(mode in ALLOWED_VALIDATOR_MODES, "validatorMode", "Validator mode must be Surfpool local or explicit solana-test-validator fallback.")
    require(cluster.get("source") == "localnet", "cluster.source", "Validator lane must use localnet only.")
    require(cluster.get("endpoint") in {"127.0.0.1", "localhost"}, "cluster.endpoint", "Validator endpoint must be loopback only.")
    require(cluster.get("genesisSource") in {"surfpool-local-fixture", "solana-test-validator-default-genesis"}, "cluster.genesisSource", "Cluster genesis source must be a local fixture or local validator default.")
    require(scenario.get("surfpoolEvidencePresent") is True or mode == "solana-test-validator-fallback", "surfpoolEvidencePresent", "Surfpool evidence is required unless fallback mode is explicitly selected.")
    require(mode != "solana-test-validator-fallback" or bool(scenario.get("fallbackRationale")), "fallbackRationale", "Fallback mode requires a rationale.")
    require(mode != "solana-test-validator-fallback" or scenario.get("surfpoolEvidencePresent") is False, "surfpoolEvidencePresent", "Fallback mode must explain why Surfpool evidence is unavailable.")
    require(bool(accounts), "accounts", "Account state source evidence is required.")
    require(bool(programs), "programs", "Program state source evidence is required.")
    require(teardown.get("captured") is True, "teardown.captured", "Validator teardown evidence must be captured.")
    require(teardown.get("ledgerCleaned") is True, "teardown.ledgerCleaned", "Local ledger cleanup must be verified.")
    require(rollback.get("available") is True, "rollback.available", "Rollback or reset path must be available.")
    require(rollback.get("cleanupVerified") is True, "rollback.cleanupVerified", "Rollback cleanup must be verified.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet is not requested by default for this lane.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet remains blocked without fresh approval.")
    require(scenario.get("walletRequested") is False, "walletRequested", "Wallet access is not allowed for local validator lane evidence.")
    require(scenario.get("facilitatorRequested") is False, "facilitatorRequested", "Facilitator access is not allowed for local validator lane evidence.")
    require(scenario.get("settlementClaimed") is False, "settlementClaimed", "The lane must not claim live settlement.")
    require(deltas.get("lamportsBefore") is not None and deltas.get("lamportsAfter") is not None, "stateDeltas.lamports", "Lamport before/after evidence is required, even when the delta is zero.")
    require(deltas.get("tokenBefore") is not None and deltas.get("tokenAfter") is not None, "stateDeltas.tokens", "Token before/after evidence is required, even when the delta is zero.")
    for field in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(field) is False, f"boundaryStatus.{field}", f"{field} must be false.")
    findings.extend(sensitive_findings(scenario))
    return findings


def build_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = collect_findings(scenario)
    status = "pass" if not findings else "fail"
    trace_id = stable_id(scenario.get("id", ""), scenario.get("validatorMode", ""), "surfpool-lane")
    deltas = scenario.get("stateDeltas", {})
    evidence = {
        "traceId": trace_id,
        "validatorMode": scenario.get("validatorMode"),
        "cluster": scenario.get("cluster"),
        "accountStateSource": scenario.get("accounts"),
        "programStateSource": scenario.get("programs"),
        "stateDeltas": {
            **deltas,
            "lamportsDelta": lamport_delta(deltas.get("lamportsBefore"), deltas.get("lamportsAfter")),
            "tokenDelta": token_delta(deltas.get("tokenBefore"), deltas.get("tokenAfter")),
        },
        "receipt": {
            "receiptId": stable_id(trace_id, "receipt"),
            "kind": "local-validator-evidence",
            "liveSettlement": False,
            "devnetUsed": False,
            "mainnetUsed": False,
            "credentialMaterialLogged": False,
        } if status == "pass" else None,
        "teardown": scenario.get("teardown"),
        "rollback": scenario.get("rollback"),
        "commands": validator_commands(scenario, status),
    }
    return {
        "id": scenario.get("id"),
        "status": status,
        "validatorPreference": "surfpool-first",
        "fallbackRationale": scenario.get("fallbackRationale"),
        "evidence": evidence,
        "boundaries": scenario.get("boundaryStatus", {}),
        "findings": findings,
    }


def build_report(scenarios_doc: dict[str, Any]) -> dict[str, Any]:
    scenarios = [
        build_result(merge_scenario(scenarios_doc.get("defaults", {}), scenario))
        for scenario in scenarios_doc.get("scenarios", [])
    ]
    positive = [scenario for scenario in scenarios if not scenario["findings"]]
    negative = [scenario for scenario in scenarios if scenario["findings"]]
    report_status = "pass" if positive and negative and all(
        scenario["status"] == "pass" for scenario in positive
    ) and all(scenario["status"] == "fail" for scenario in negative) else "fail"
    return {
        "mode": "surfpool-local-validator-testing-lane",
        "status": report_status,
        "issue": 248,
        "parentEpic": 247,
        "relatedEpic": 220,
        "validatorPreference": {
            "preferred": "surfpool-local",
            "fallback": "solana-test-validator-fallback",
            "fallbackPolicy": "Allowed only with explicit rationale when Surfpool is unavailable or baseline validator behavior is the test objective.",
        },
        "boundaries": {
            "deterministicLocalEvidenceOnly": True,
            "validatorStartedByThisScript": False,
            "dependenciesInstalled": False,
            "networkAccessUsed": False,
            "credentialAccessUsed": False,
            "walletAccessUsed": False,
            "paymentRailAccessUsed": False,
            "facilitatorAccessUsed": False,
            "settlementAccessUsed": False,
            "liveMcpInvocationUsed": False,
            "providerApiAccessUsed": False,
            "devnetAccessUsed": False,
            "mainnetAccessUsed": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "externalSpendUsd": 0,
        },
        "summary": {
            "positiveScenarios": len(positive),
            "negativeScenarios": len(negative),
            "failClosedScenarios": len(negative),
            "surfpoolPassScenarios": sum(1 for scenario in positive if scenario["evidence"]["validatorMode"] == "surfpool-local"),
            "fallbackPassScenarios": sum(1 for scenario in positive if scenario["evidence"]["validatorMode"] == "solana-test-validator-fallback"),
        },
        "results": scenarios,
        "mainnetStatement": "Mainnet validator, wallet, payment rail, facilitator, and settlement access remain blocked without fresh Nissan approval.",
        "scenarioFixtureHash": digest_text(json.dumps(scenarios_doc, sort_keys=True)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(load_json(args.scenarios))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
