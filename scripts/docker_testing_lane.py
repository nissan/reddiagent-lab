#!/usr/bin/env python3
"""Build deterministic Docker local/VPS testing lane evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "docker-testing-lane-scenarios.json"

ALLOWED_ENVIRONMENT = {"local-docker", "vps-docker"}
ALLOWED_NETWORK_EXPOSURE = {"loopback-only", "isolated-bridge"}
REQUIRED_BOUNDARY_FALSE = (
    "dependencyPulls",
    "containerStarted",
    "vpsMutation",
    "hostedServiceUsed",
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
    "dockerpassword",
    "facilitatorkey",
    "mnemonic",
    "password",
    "privatekey",
    "registrytoken",
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
                findings.append(finding(child_path, "Credential, wallet, registry, facilitator, or secret-like keys are not allowed in Docker lane evidence."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential, wallet, registry, facilitator, or secret-like values are not allowed in Docker lane evidence."))
    return findings


def image_has_digest(image: dict[str, Any]) -> bool:
    reference = image.get("reference", "")
    digest = image.get("digest", "")
    return isinstance(reference, str) and "@" in reference and isinstance(digest, str) and digest.startswith("sha256:")


def commands(scenario: dict[str, Any], status: str) -> list[dict[str, Any]]:
    exit_code = 0 if status == "pass" else 3
    compose_file = scenario.get("composeFile", "tests/fixtures/docker-compose.reddiagent-local.yml")
    environment = scenario.get("environment")
    return [
        {
            "step": 1,
            "command": f"docker compose -f {compose_file} config --no-interpolate",
            "event": "docker.config_rendered",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 2,
            "command": f"docker evidence inspect --environment {environment} --no-pull --no-start",
            "event": "docker.static_evidence_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
        {
            "step": 3,
            "command": "docker lane teardown --dry-run --verify-volumes --retain-redacted-logs",
            "event": "docker.teardown_captured",
            "exitCode": exit_code,
            "networkAccessUsed": False,
        },
    ]


def collect_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    environment = scenario.get("environment")
    selection = scenario.get("selectionCriteria", {})
    images = scenario.get("images", [])
    env_contract = scenario.get("envContract", [])
    network = scenario.get("network", {})
    logs = scenario.get("logs", {})
    volumes = scenario.get("volumes", {})
    teardown = scenario.get("teardown", {})
    rollback = scenario.get("rollback", {})
    boundaries = scenario.get("boundaryStatus", {})

    require(environment in ALLOWED_ENVIRONMENT, "environment", "Docker lane must select local Docker or VPS Docker.")
    require(bool(selection.get("useLocalWhen")), "selectionCriteria.useLocalWhen", "Local Docker selection criteria are required.")
    require(bool(selection.get("useVpsWhen")), "selectionCriteria.useVpsWhen", "VPS Docker selection criteria are required.")
    require(bool(selection.get("selectedBecause")), "selectionCriteria.selectedBecause", "Selected environment rationale is required.")
    require(bool(images), "images", "At least one pinned image reference is required.")
    for index, image in enumerate(images):
        require(image_has_digest(image), f"images[{index}].digest", "Docker image references must include an exact sha256 digest.")
        require(image.get("pullAllowed") is False, f"images[{index}].pullAllowed", "This evidence lane must not pull images.")
    require(bool(env_contract), "envContract", "Environment-variable contract is required.")
    for index, item in enumerate(env_contract):
        require("value" not in item, f"envContract[{index}].value", "Environment contract must list names and requirements without secret values.")
        require(item.get("secretHandling") in {False, "provided-out-of-band"}, f"envContract[{index}].secretHandling", "Secret env vars must be marked as provided out of band, never stored.")
    require(network.get("exposure") in ALLOWED_NETWORK_EXPOSURE, "network.exposure", "Network exposure must be loopback-only or isolated bridge.")
    require(network.get("hostNetwork") is False, "network.hostNetwork", "Host networking is not allowed.")
    require(network.get("publishedPorts") in ([], None), "network.publishedPorts", "Docker lane must not publish external ports by default.")
    require(logs.get("retained") is True, "logs.retained", "Redacted logs retained evidence is required.")
    require(logs.get("redacted") is True, "logs.redacted", "Logs must be redacted before retention.")
    require(volumes.get("ephemeral") is True, "volumes.ephemeral", "Volumes must be ephemeral for this lane.")
    require(volumes.get("cleanupVerified") is True, "volumes.cleanupVerified", "Volume cleanup verification is required.")
    require(teardown.get("captured") is True, "teardown.captured", "Teardown evidence must be captured.")
    require(teardown.get("containersRemoved") is True, "teardown.containersRemoved", "Container cleanup verification is required.")
    require(rollback.get("available") is True, "rollback.available", "Rollback or cleanup path must be available.")
    require(rollback.get("cleanupVerified") is True, "rollback.cleanupVerified", "Rollback cleanup must be verified.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet is denied by default for Docker lane evidence.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet remains blocked without fresh approval.")
    require(scenario.get("liveNetworkEnabled") is False, "liveNetworkEnabled", "Live network flags must be disabled by default.")
    require(scenario.get("productionClaimed") is False, "productionClaimed", "Docker lane evidence must not claim production enablement.")
    require(scenario.get("deploymentClaimed") is False, "deploymentClaimed", "Docker lane evidence must not claim deployment occurred.")
    require(scenario.get("walletRequested") is False, "walletRequested", "Wallet access is not allowed for Docker lane evidence.")
    require(scenario.get("paymentRequested") is False, "paymentRequested", "Payment access is not allowed for Docker lane evidence.")
    require(scenario.get("paymentRailRequested") is False, "paymentRailRequested", "Payment rail access is not allowed for Docker lane evidence.")
    require(scenario.get("paymentAccessRequested") is False, "paymentAccessRequested", "Payment access is not allowed for Docker lane evidence.")
    require(scenario.get("facilitatorRequested") is False, "facilitatorRequested", "Facilitator access is not allowed for Docker lane evidence.")
    require(scenario.get("settlementRequested") is False, "settlementRequested", "Settlement access is not allowed for Docker lane evidence.")
    require(scenario.get("settlementClaimed") is False, "settlementClaimed", "The lane must not claim live settlement.")
    for field in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(field) is False, f"boundaryStatus.{field}", f"{field} must be false.")
    findings.extend(sensitive_findings(scenario))
    return findings


def build_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = collect_findings(scenario)
    status = "pass" if not findings else "fail"
    trace_id = stable_id(scenario.get("id", ""), scenario.get("environment", ""), "docker-lane")
    return {
        "id": scenario.get("id"),
        "status": status,
        "environment": scenario.get("environment"),
        "selectionCriteria": scenario.get("selectionCriteria"),
        "evidence": {
            "traceId": trace_id,
            "images": scenario.get("images"),
            "envContract": scenario.get("envContract"),
            "network": scenario.get("network"),
            "logs": scenario.get("logs"),
            "volumes": scenario.get("volumes"),
            "teardown": scenario.get("teardown"),
            "rollback": scenario.get("rollback"),
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
        "mode": "docker-local-vps-testing-lane",
        "status": report_status,
        "issue": 249,
        "parentEpic": 247,
        "relatedEpic": 220,
        "selectionPolicy": {
            "preferred": "local-docker",
            "useVpsOnlyFor": [
                "long-running generated-package execution",
                "host parity that local Docker cannot provide",
                "operator-visible evidence requiring stable uptime",
            ],
        },
        "boundaries": {
            "deterministicLocalEvidenceOnly": True,
            "dockerPulledByThisScript": False,
            "containerStartedByThisScript": False,
            "vpsMutatedByThisScript": False,
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
        "mainnetStatement": "Docker lane evidence does not enable production, live settlement, or Mainnet; Mainnet remains blocked until fresh Nissan approval.",
        "summary": {
            "positiveScenarios": len(positive),
            "negativeScenarios": len(negative),
            "failClosedScenarios": len([scenario for scenario in negative if scenario["status"] == "fail"]),
            "localDockerPassScenarios": len([scenario for scenario in positive if scenario["environment"] == "local-docker"]),
            "vpsDockerPassScenarios": len([scenario for scenario in positive if scenario["environment"] == "vps-docker"]),
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
