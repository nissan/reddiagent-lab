#!/usr/bin/env python3
"""Verify local beta release evidence before any live activation or deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-verification-scenarios.json"

PROFILE_REQUIREMENTS = {
    "local-only": (),
    "local-validator": ("surfpool",),
    "docker": ("docker",),
    "coolify": ("coolify",),
    "full": ("surfpool", "docker", "coolify"),
}
REQUIRED_CORE_ARTIFACTS = {
    "handoff": "tests/fixtures/beta-release-handoff.json",
    "readiness": "tests/fixtures/beta-release-readiness.json",
    "runtimeRc": "tests/fixtures/beta-local-runtime-rc-gate.json",
    "runtimePackage": "tests/fixtures/beta-operator-dry-run-package.json",
    "reviewUi": "tests/fixtures/beta-review-ui.json",
    "decisionPackage": "tests/fixtures/beta-operator-decision-package.json",
    "preflight": "tests/fixtures/beta-activation-preflight.json",
    "rehearsal": "tests/fixtures/beta-activation-rehearsal.json",
    "acceptance": "tests/fixtures/beta-activation-acceptance.json",
}
OPTIONAL_ENV_ARTIFACTS = {
    "surfpool": "tests/fixtures/surfpool-validator-lane.json",
    "docker": "tests/fixtures/docker-testing-lane.json",
    "coolify": "tests/fixtures/coolify-staging-lane.json",
}
REQUIRED_BOUNDARY_FALSE = (
    "liveRuntimeActivation",
    "networkAccess",
    "networkAccessUsed",
    "credentialAccess",
    "credentialAccessUsed",
    "credentialPersisted",
    "mcpInvocation",
    "paymentAccess",
    "providerApiAccess",
    "providerApiAccessUsed",
    "devnetAccess",
    "devnetAccessUsed",
    "productionGatewayAccess",
    "mainnetAccess",
    "mainnetAccessUsed",
    "externalSpend",
    "deploymentPublished",
    "packagePublished",
    "hostedServiceUsed",
    "hostedServiceUsedByThisScript",
    "publicExposure",
    "walletAccess",
    "walletAccessUsed",
    "paymentRailAccess",
    "paymentRailAccessUsed",
    "facilitatorAccess",
    "facilitatorAccessUsed",
    "settlementAccess",
    "settlementAccessUsed",
    "liveMcpInvocation",
    "liveMcpInvocationUsed",
    "validatorStartedByThisScript",
    "containerStarted",
    "containerStartedByThisScript",
    "dockerPulledByThisScript",
    "coolifyMutated",
    "coolifyMutatedByThisScript",
    "dependenciesInstalled",
    "dependencyPulls",
    "vpsMutation",
    "vpsMutatedByThisScript",
)
UNSAFE_KEYS_NORMALIZED = {
    "apikey",
    "authorization",
    "bearertoken",
    "credential",
    "credentialpayload",
    "deploymentsecret",
    "facilitatorkey",
    "mnemonic",
    "password",
    "privatekey",
    "secret",
    "seedphrase",
    "token",
    "walletprivatekey",
}
UNSAFE_VALUE_MARKERS = (
    "bearer ",
    "private key",
    "seed phrase",
    "mnemonic",
    "api key",
    "password=",
    "token=",
)
UNSAFE_CLAIM_MARKERS = (
    "runtime activation completed",
    "runtime activation occurred",
    "runtime activation succeeded",
    "live runtime enabled",
    "production gateway enabled",
    "mainnet enabled",
    "deployed to production",
    "deployment completed",
    "live settlement",
    "settlement completed",
    "published package",
)
UNSAFE_FLAG_FIELDS = (
    "liveRuntimeRequested",
    "devnetRequested",
    "mainnetRequested",
    "liveNetworkEnabled",
    "walletRequested",
    "paymentRequested",
    "paymentRailRequested",
    "paymentAccessRequested",
    "facilitatorRequested",
    "settlementRequested",
    "settlementClaimed",
    "deploymentRequested",
    "deploymentClaimed",
    "productionClaimed",
    "productionEnabled",
    "mainnetEnabled",
)
ALLOWED_TOP_LEVEL_STATUS = {
    "pass",
    "beta-candidate",
    "ready",
    "review-ready",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def source_commit() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def merge_scenario(defaults: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def expected_hash_map(scenario: dict[str, Any]) -> dict[str, str]:
    return {
        item["path"]: item.get("sha256", "")
        for item in scenario.get("expectedArtifactHashes", [])
        if isinstance(item, dict) and item.get("path")
    }


def required_artifacts_for(profile: str, scenario: dict[str, Any] | None = None) -> dict[str, str]:
    artifacts = dict(REQUIRED_CORE_ARTIFACTS)
    for key in PROFILE_REQUIREMENTS[profile]:
        artifacts[key] = OPTIONAL_ENV_ARTIFACTS[key]
    overrides = (scenario or {}).get("artifactPathOverrides", {})
    if isinstance(overrides, dict):
        for key, path_text in overrides.items():
            if key in artifacts and isinstance(path_text, str):
                artifacts[key] = path_text
    return artifacts


def collect_artifacts(scenario: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, str]]]:
    profile = scenario.get("profile")
    expected = expected_hash_map(scenario)
    artifacts: list[dict[str, Any]] = []
    docs: dict[str, dict[str, Any]] = {}
    findings: list[dict[str, str]] = []
    if profile not in PROFILE_REQUIREMENTS:
        return artifacts, docs, [finding("profile", "Verification profile must be local-only, local-validator, docker, coolify, or full.")]

    for key, path_text in required_artifacts_for(profile, scenario).items():
        path = ROOT / path_text
        exists = path.exists() and path.is_file()
        actual = digest(path) if exists else None
        expected_sha = expected.get(path_text)
        artifacts.append(
            {
                "key": key,
                "path": path_text,
                "exists": exists,
                "sha256": actual,
                "expectedSha256": expected_sha,
                "hashMatches": bool(actual and expected_sha and actual == expected_sha),
            }
        )
        if not exists:
            findings.append(finding(f"artifacts.{key}.exists", f"Required artifact `{path_text}` is missing."))
            continue
        if not expected_sha:
            findings.append(finding(f"artifacts.{key}.expectedSha256", f"Expected sha256 pin is required for `{path_text}`."))
        elif actual != expected_sha:
            findings.append(finding(f"artifacts.{key}.sha256", f"Artifact `{path_text}` does not match its expected sha256 pin."))
        try:
            docs[key] = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding(f"artifacts.{key}.json", f"Artifact `{path_text}` must be valid JSON: {exc}"))
    return artifacts, docs, findings


def sensitive_payload_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in UNSAFE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential-like keys are not allowed in release verification inputs or passing evidence."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in release verification inputs or passing evidence."))
    return findings


def unsafe_claim_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(unsafe_claim_findings(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(unsafe_claim_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in UNSAFE_CLAIM_MARKERS:
            if marker in lowered:
                if (
                    f"does not claim {marker}" in lowered
                    or f"does not enable {marker}" in lowered
                    or ("does not enable" in lowered and marker in lowered)
                    or f"no {marker}" in lowered
                    or f"not claim {marker}" in lowered
                ):
                    continue
                findings.append(finding(path, f"Passing evidence must not claim `{marker}`."))
    return findings


def passing_results(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [result for result in doc.get("results", []) if isinstance(result, dict) and result.get("status") == "pass"]


def failed_negative_results(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        result
        for result in doc.get("results", [])
        if isinstance(result, dict) and result.get("status") == "fail"
    ]


def boundary_findings(boundaries: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(boundaries, dict):
        return findings
    for field in REQUIRED_BOUNDARY_FALSE:
        if field in boundaries and boundaries.get(field) is not False:
            findings.append(finding(f"{path}.{field}", f"{field} must be false."))
    return findings


def evidence_guardrail_findings(key: str, doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("status") not in ALLOWED_TOP_LEVEL_STATUS:
        findings.append(finding(f"{key}.status", "Required evidence artifact must have a passing or candidate-ready top-level status."))
    findings.extend(boundary_findings(doc.get("boundaries", {}), f"{key}.boundaries"))

    for field in UNSAFE_FLAG_FIELDS:
        if doc.get(field) not in (None, False):
            findings.append(finding(f"{key}.{field}", f"{field} must be false or absent."))
    findings.extend(sensitive_payload_findings({"topLevel": {k: v for k, v in doc.items() if k != "results"}}, key))
    findings.extend(unsafe_claim_findings({"topLevel": {k: v for k, v in doc.items() if k != "results"}}, key))

    for index, result in enumerate(passing_results(doc)):
        for field in UNSAFE_FLAG_FIELDS:
            if result.get(field) not in (None, False):
                findings.append(finding(f"{key}.results[{index}].{field}", f"{field} must be false or absent in passing evidence."))
        findings.extend(boundary_findings(result.get("boundaryStatus", {}), f"{key}.results[{index}].boundaryStatus"))
        findings.extend(boundary_findings(result.get("boundaries", {}), f"{key}.results[{index}].boundaries"))
        findings.extend(sensitive_payload_findings(result, f"{key}.results[{index}]"))
        findings.extend(unsafe_claim_findings(result, f"{key}.results[{index}]"))
    return findings


def chain_findings(docs: dict[str, dict[str, Any]], profile: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    handoff = docs.get("handoff", {})
    release_id = handoff.get("releaseId")
    if release_id != "reddiagent-beta-0":
        findings.append(finding("handoff.releaseId", "Release verifier currently requires reddiagent-beta-0 handoff evidence."))

    required_keys = list(REQUIRED_CORE_ARTIFACTS)
    required_keys.extend(PROFILE_REQUIREMENTS.get(profile, ()))
    for key in required_keys:
        if key in docs:
            findings.extend(evidence_guardrail_findings(key, docs[key]))

    if not any(result.get("handoffOutcome") == "accepted" and result.get("status") == "pass" for result in passing_results(handoff)):
        findings.append(finding("handoff.results", "At least one accepted handoff result must pass."))
    if not any(result.get("handoffOutcome") == "rollback-required" and result.get("status") == "pass" for result in passing_results(handoff)):
        findings.append(finding("handoff.rollback", "Rollback-required handoff evidence must pass."))
    if not any(result.get("kind") == "negative" and result.get("status") == "fail" for result in failed_negative_results(handoff)):
        findings.append(finding("handoff.failClosed", "Handoff archive must include fail-closed negative evidence."))
    for env_key in PROFILE_REQUIREMENTS.get(profile, ()):
        doc = docs.get(env_key, {})
        if not failed_negative_results(doc):
            findings.append(finding(f"{env_key}.failClosed", f"{env_key} lane evidence must include fail-closed negative cases."))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str, profile: str) -> str:
    if verdict == "accept":
        return f"Reviewer may accept the {profile} beta evidence bundle for planning only; separate approval is still required before live runtime activation or deployment."
    if verdict == "reject":
        return "Reject this beta release candidate and regenerate the failing evidence before any operator activation path is considered."
    return "Hold before activation or hosted deployment; fix missing, stale, or unsafe evidence and rerun this local verifier."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    artifacts, docs, findings = collect_artifacts(scenario)
    profile = scenario.get("profile")
    if profile in PROFILE_REQUIREMENTS:
        findings.extend(chain_findings(docs, profile))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in verification scenario inputs."))
    findings.extend(unsafe_claim_findings(scenario.get("operatorFacingNextStep", ""), "operatorFacingNextStep"))
    status = "pass" if not findings else "fail"
    verdict = verdict_for(status, scenario.get("requestedVerdict"))
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "profile": profile,
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "releaseId": scenario.get("releaseId"),
        "requiredArtifactPaths": [artifact["path"] for artifact in artifacts],
        "evidenceHashes": artifacts,
        "operatorNextStep": next_step_for(verdict, profile or "unknown"),
        "boundaries": {
            "deterministicLocalOnly": True,
            "liveRuntimeActivation": False,
            "networkAccess": False,
            "credentialAccess": False,
            "walletAccess": False,
            "paymentAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "externalSpend": False,
        },
    }


def build_report(doc: dict[str, Any], commit: str | None = None) -> dict[str, Any]:
    actual_commit = commit or source_commit()
    defaults = doc.get("defaults", {})
    results = [
        build_result(merge_scenario(defaults, scenario), actual_commit)
        for scenario in doc.get("scenarios", [])
    ]
    mismatches = [
        finding(f"results[{index}].status", f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}.")
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"] or result["verdict"] != result["expectedVerdict"]
    ]
    return {
        "mode": "beta-local-release-verification-cli",
        "issue": 269,
        "parentEpic": 220,
        "relatedEpic": 247,
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "findings": mismatches,
        "profiles": sorted(PROFILE_REQUIREMENTS),
        "summary": {
            "acceptVerdicts": sum(1 for result in results if result["verdict"] == "accept"),
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rejectVerdicts": sum(1 for result in results if result["verdict"] == "reject"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": {
            "deterministicLocalOnly": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "liveRuntimeActivation": False,
            "deploymentPublished": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "externalSpend": False,
        },
        "mainnetStatement": "This verifier is local/free/dry-run only. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Verification scenario JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
