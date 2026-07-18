#!/usr/bin/env python3
"""Build deterministic Coolify staging/operator UI lane evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "coolify-staging-lane-scenarios.json"

ALLOWED_LANE_MODES = {"local-only", "coolify-staging-required"}
ALLOWED_BOUNDARY = {"static-ui-artifact", "coolify-app", "coolify-service"}
SHA_REF = re.compile(r"^[0-9a-f]{40}$")
IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED_BOUNDARY_FALSE = (
    "coolifyMutated",
    "hostedServiceUsed",
    "deploymentPublished",
    "publicExposure",
    "credentialAccess",
    "credentialPersisted",
    "walletAccess",
    "paymentRailAccess",
    "facilitatorAccess",
    "settlementAccess",
    "liveMcpInvocation",
    "providerApiAccess",
    "devnetAccess",
    "mainnetAccess",
    "packagePublished",
    "externalSpend",
)
SENSITIVE_KEYS_NORMALIZED = {
    "accesstoken",
    "apikey",
    "authorization",
    "bearertoken",
    "credential",
    "credentialpayload",
    "coolifytoken",
    "facilitatorkey",
    "mnemonic",
    "password",
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
    "password=",
    "token=",
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
        if value == {}:
            merged[key] = {}
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
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
                findings.append(finding(child_path, "Credential, wallet, Coolify token, facilitator, or secret-like keys are not allowed in Coolify lane evidence."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential, wallet, Coolify token, facilitator, or secret-like values are not allowed in Coolify lane evidence."))
    return findings


def source_pinned(source: dict[str, Any]) -> bool:
    commit = source.get("commit", "")
    return isinstance(commit, str) and bool(SHA_REF.fullmatch(commit))


def image_pinned(image: dict[str, Any]) -> bool:
    reference = image.get("reference", "")
    digest = image.get("digest", "")
    if not isinstance(reference, str) or not isinstance(digest, str):
        return False
    if not IMAGE_DIGEST.fullmatch(digest):
        return False
    _, separator, reference_digest = reference.rpartition("@")
    return bool(separator) and reference_digest == digest


def commands(scenario: dict[str, Any], status: str) -> list[dict[str, Any]]:
    exit_code = 0 if status == "pass" else 4
    lane_mode = scenario.get("laneMode")
    source = scenario.get("source", {})
    return [
        {
            "step": 1,
            "command": f"coolify lane decide --mode {lane_mode} --local-first --no-mutate",
            "event": "coolify.selection_recorded",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 2,
            "command": f"coolify evidence render --source {source.get('commit', 'missing')} --no-deploy --no-secrets",
            "event": "coolify.static_evidence_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 3,
            "command": "coolify teardown --dry-run --verify-volumes --retain-redacted-logs",
            "event": "coolify.teardown_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
    ]


def collect_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    lane_mode = scenario.get("laneMode")
    selection = scenario.get("selectionCriteria", {})
    boundary = scenario.get("serviceBoundary", {})
    source = scenario.get("source", {})
    image = scenario.get("image", {})
    env_contract = scenario.get("envContract", [])
    network = scenario.get("network", {})
    access = scenario.get("accessControls", {})
    health = scenario.get("healthChecks", {})
    logs = scenario.get("logs", {})
    storage = scenario.get("storage", {})
    teardown = scenario.get("teardown", {})
    rollback = scenario.get("rollback", {})
    operator_ui = scenario.get("operatorUiEvidence", {})
    boundaries = scenario.get("boundaryStatus", {})

    require(lane_mode in ALLOWED_LANE_MODES, "laneMode", "Coolify lane must be local-only or Coolify-staging-required.")
    require(bool(selection.get("useLocalWhen")), "selectionCriteria.useLocalWhen", "Local-only decision criteria are required.")
    require(bool(selection.get("useCoolifyWhen")), "selectionCriteria.useCoolifyWhen", "Coolify-use criteria are required.")
    require(bool(selection.get("selectedBecause")), "selectionCriteria.selectedBecause", "Selected lane rationale is required.")
    require(boundary.get("type") in ALLOWED_BOUNDARY, "serviceBoundary.type", "Service boundary must be static UI artifact, Coolify app, or Coolify service.")
    require(bool(boundary.get("appName")), "serviceBoundary.appName", "A stable app/service name is required.")
    require(source_pinned(source), "source.commit", "Source must be pinned to a full 40-character commit SHA.")
    if image:
        require(image_pinned(image), "image.digest", "Image references must include an exact sha256 digest when an image is used.")
        require(image.get("pullAllowed") is False, "image.pullAllowed", "This evidence lane must not pull images.")
    require(bool(env_contract), "envContract", "Environment-variable contract is required.")
    for index, item in enumerate(env_contract):
        require("value" not in item, f"envContract[{index}].value", "Environment contract must list names and requirements without values.")
        require(item.get("secretHandling") in {False, "provided-out-of-band"}, f"envContract[{index}].secretHandling", "Secret env vars must be marked as provided out of band, never stored.")
    require(network.get("publicExposure") is False, "network.publicExposure", "Public exposure is denied by default.")
    require(network.get("ingress") in {"none", "private-vpn", "operator-ip-allowlist"}, "network.ingress", "Ingress must be none, private VPN, or operator IP allowlist.")
    require(access.get("authenticationRequired") is True, "accessControls.authenticationRequired", "Hosted operator UI evidence requires authentication.")
    require(access.get("operatorAllowlistRequired") is True, "accessControls.operatorAllowlistRequired", "Operator allowlist evidence is required.")
    require(access.get("anonymousAccessAllowed") is False, "accessControls.anonymousAccessAllowed", "Anonymous operator UI access is not allowed.")
    require(bool(health), "healthChecks", "Hosted staging evidence must include health-check expectations.")
    require(health.get("requiredWhenHosted") is True, "healthChecks.requiredWhenHosted", "Hosted staging evidence requires health checks.")
    require(health.get("endpoint") in {"/healthz", "/api/health"}, "healthChecks.endpoint", "Health-check endpoint must be explicit and non-sensitive.")
    require(health.get("expectedStatus") == 200, "healthChecks.expectedStatus", "Health-check expected status must be 200.")
    require(health.get("requiresAuthentication") is True, "healthChecks.requiresAuthentication", "Health checks must use authenticated or private access.")
    require(health.get("publicProbeAllowed") is False, "healthChecks.publicProbeAllowed", "Public health probes are denied by default.")
    require(health.get("retainedEvidence") in {"redacted-status", "redacted-status-and-timing"}, "healthChecks.retainedEvidence", "Health-check evidence must retain only redacted status/timing.")
    require(logs.get("retained") is True, "logs.retained", "Redacted log-retention evidence is required.")
    require(logs.get("redacted") is True, "logs.redacted", "Logs must be redacted before retention.")
    require(storage.get("persistentVolume") is False, "storage.persistentVolume", "Persistent volumes are denied by default.")
    require(storage.get("cleanupVerified") is True, "storage.cleanupVerified", "Volume/storage cleanup verification is required.")
    require(teardown.get("captured") is True, "teardown.captured", "Teardown evidence must be captured.")
    require(teardown.get("coolifyResourcesRemoved") is True, "teardown.coolifyResourcesRemoved", "Coolify resource cleanup evidence is required.")
    require(rollback.get("available") is True, "rollback.available", "Rollback path must be available.")
    require(rollback.get("cleanupVerified") is True, "rollback.cleanupVerified", "Rollback cleanup evidence is required.")
    require(operator_ui.get("requiredWhenHosted") is True, "operatorUiEvidence.requiredWhenHosted", "Operator UI evidence expectations are required.")
    require(operator_ui.get("screenshotRequired") is True, "operatorUiEvidence.screenshotRequired", "Operator UI screenshot evidence is required when hosted.")
    require(operator_ui.get("accessLogRequired") is True, "operatorUiEvidence.accessLogRequired", "Operator UI access-log evidence is required when hosted.")
    require(operator_ui.get("liveSettlementClaimed") is False, "operatorUiEvidence.liveSettlementClaimed", "Operator UI evidence must not claim live settlement.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet is denied by default for Coolify lane evidence.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet remains blocked without fresh approval.")
    require(scenario.get("liveNetworkEnabled") is False, "liveNetworkEnabled", "Live network flags must be disabled by default.")
    require(scenario.get("productionClaimed") is False, "productionClaimed", "Coolify lane evidence must not claim production enablement.")
    require(scenario.get("deploymentClaimed") is False, "deploymentClaimed", "Coolify lane evidence must not claim deployment occurred.")
    require(scenario.get("walletRequested") is False, "walletRequested", "Wallet access is not allowed for Coolify lane evidence.")
    require(scenario.get("paymentRequested") is False, "paymentRequested", "Payment access is not allowed for Coolify lane evidence.")
    require(scenario.get("paymentRailRequested") is False, "paymentRailRequested", "Payment rail access is not allowed for Coolify lane evidence.")
    require(scenario.get("paymentAccessRequested") is False, "paymentAccessRequested", "Payment access is not allowed for Coolify lane evidence.")
    require(scenario.get("facilitatorRequested") is False, "facilitatorRequested", "Facilitator access is not allowed for Coolify lane evidence.")
    require(scenario.get("settlementRequested") is False, "settlementRequested", "Settlement access is not allowed for Coolify lane evidence.")
    require(scenario.get("settlementClaimed") is False, "settlementClaimed", "The lane must not claim live settlement.")
    for field in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(field) is False, f"boundaryStatus.{field}", f"{field} must be false.")
    findings.extend(sensitive_findings(scenario))
    return findings


def build_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = collect_findings(scenario)
    status = "pass" if not findings else "fail"
    trace_id = stable_id(scenario.get("id", ""), scenario.get("laneMode", ""), "coolify-lane")
    return {
        "id": scenario.get("id"),
        "status": status,
        "laneMode": scenario.get("laneMode"),
        "serviceBoundary": scenario.get("serviceBoundary"),
        "selectionCriteria": scenario.get("selectionCriteria"),
        "evidence": {
            "traceId": trace_id,
            "source": scenario.get("source"),
            "image": scenario.get("image"),
            "envContract": scenario.get("envContract"),
            "network": scenario.get("network"),
            "accessControls": scenario.get("accessControls"),
            "healthChecks": scenario.get("healthChecks"),
            "logs": scenario.get("logs"),
            "storage": scenario.get("storage"),
            "teardown": scenario.get("teardown"),
            "rollback": scenario.get("rollback"),
            "operatorUiEvidence": scenario.get("operatorUiEvidence"),
            "commands": commands(scenario, status),
        },
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
        "mode": "coolify-staging-operator-ui-lane",
        "status": report_status,
        "issue": 250,
        "parentEpic": 247,
        "relatedEpic": 220,
        "selectionPolicy": {
            "preferred": "local-only",
            "useCoolifyOnlyFor": [
                "persistent operator UI review that local HTML cannot prove",
                "reachable staging evidence after local Docker validation passes",
                "end-to-end beta review requiring stable hosted uptime",
            ],
        },
        "boundaries": {
            "deterministicLocalEvidenceOnly": True,
            "coolifyMutatedByThisScript": False,
            "hostedServiceUsedByThisScript": False,
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
        "mainnetStatement": "Coolify lane evidence does not enable production, live settlement, or Mainnet; Mainnet remains blocked until fresh Nissan approval.",
        "summary": {
            "positiveScenarios": len(positive),
            "negativeScenarios": len(negative),
            "failClosedScenarios": len([scenario for scenario in negative if scenario["status"] == "fail"]),
            "localOnlyPassScenarios": len([scenario for scenario in positive if scenario["laneMode"] == "local-only"]),
            "coolifyStagingRequiredPassScenarios": len([scenario for scenario in positive if scenario["laneMode"] == "coolify-staging-required"]),
        },
        "results": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(load_json(args.scenarios))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
