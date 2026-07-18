#!/usr/bin/env python3
"""Build a deterministic local beta release-candidate bundle manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-candidate-bundle-scenarios.json"

REQUIRED_ARTIFACTS = {
    "verifier": "tests/fixtures/beta-release-verification.json",
    "demoPlan": "docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md",
    "demoBuilder": "scripts/public_demo_walkthrough_video.sh",
}
REQUIRED_VERIFIER_MODE = "beta-local-release-verification-cli"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_DEMO_URLS = ("publicDemoUrl", "videoDemoUrl", "publicVideoUrl")
REQUIRED_DEMO_ROUTES = ("/", "/media/reddiagent-demo-walkthrough.mp4", "/builder-report.html")
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
    "sk-",
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
    "published package",
    "package published",
    "live settlement",
    "settlement completed",
)
UNSAFE_FLAG_FIELDS = (
    "liveRuntimeRequested",
    "liveNetworkEnabled",
    "providerApiAccessRequested",
    "credentialAccessRequested",
    "walletRequested",
    "paymentRequested",
    "paymentRailRequested",
    "paymentAccessRequested",
    "facilitatorRequested",
    "settlementRequested",
    "deploymentRequested",
    "deploymentClaimed",
    "packagePublishingRequested",
    "packagePublished",
    "publicPublishingRequested",
    "devnetRequested",
    "mainnetRequested",
    "mainnetEnabled",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_commit() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True)
    return proc.stdout.strip()


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


def expected_hash_map(scenario: dict[str, Any]) -> dict[str, str]:
    return {
        item["path"]: item.get("sha256", "")
        for item in scenario.get("expectedEvidenceHashes", [])
        if isinstance(item, dict) and item.get("path")
    }


def artifact_paths(scenario: dict[str, Any]) -> dict[str, str]:
    paths = dict(REQUIRED_ARTIFACTS)
    overrides = scenario.get("artifactPathOverrides", {})
    if isinstance(overrides, dict):
        for key, path_text in overrides.items():
            if key in paths and isinstance(path_text, str):
                paths[key] = path_text
    return paths


def collect_artifacts(scenario: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, str]]]:
    expected = expected_hash_map(scenario)
    artifacts: list[dict[str, Any]] = []
    file_texts: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for key, path_text in artifact_paths(scenario).items():
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
        file_texts[key] = path.read_text(errors="replace")
        if not expected_sha:
            findings.append(finding(f"artifacts.{key}.expectedSha256", f"Expected sha256 pin is required for `{path_text}`."))
        elif actual != expected_sha:
            findings.append(finding(f"artifacts.{key}.sha256", f"Artifact `{path_text}` does not match its expected sha256 pin."))
    return artifacts, file_texts, findings


def sensitive_payload_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in UNSAFE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential-like keys are not allowed in release-candidate bundle inputs."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in release-candidate bundle inputs."))
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
            if marker not in lowered:
                continue
            if (
                f"does not claim {marker}" in lowered
                or f"does not enable {marker}" in lowered
                or f"no {marker}" in lowered
                or f"not claim {marker}" in lowered
            ):
                continue
            findings.append(finding(path, f"Release-candidate bundle must not claim `{marker}`."))
    return findings


def unsafe_env_findings(env: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(env, dict):
        return findings
    for key, value in env.items():
        if value not in ("", None, "<redacted>", "${REDACTED}", False):
            findings.append(finding(f"unsafeEnvValues.{key}", "Environment evidence may include names only, not live values."))
    return findings


def load_verifier(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("verifier.json", f"Verifier output must be JSON: {exc}"))
        return {}


def accepted_verifier_result(verifier: dict[str, Any]) -> dict[str, Any] | None:
    for result in verifier.get("results", []):
        if result.get("id") == "full-profile-verification-accept-pass":
            return result
    for result in verifier.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def verifier_findings(verifier: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if verifier.get("mode") != REQUIRED_VERIFIER_MODE:
        findings.append(finding("verifier.mode", "Bundle requires #269 beta release verification output."))
    if verifier.get("status") != "pass":
        findings.append(finding("verifier.status", "Verifier evidence must pass before bundling."))
    if verifier.get("boundaries", {}).get("deterministicLocalOnly") is not True:
        findings.append(finding("verifier.boundaries.deterministicLocalOnly", "Verifier must remain deterministic/local-only."))
    for field in ("serviceStarted", "networkAccess", "credentialAccess", "liveRuntimeActivation", "deploymentPublished", "devnetAccess", "mainnetAccess", "externalSpend"):
        if verifier.get("boundaries", {}).get(field) is not False:
            findings.append(finding(f"verifier.boundaries.{field}", f"{field} must remain false."))
    if accepted_verifier_result(verifier) is None:
        findings.append(finding("verifier.results", "Verifier output must include an accepted passing release result."))
    return findings


def demo_findings(scenario: dict[str, Any], file_texts: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    metadata = scenario.get("publicDemoMetadata", {})
    if not isinstance(metadata, dict):
        return [finding("publicDemoMetadata", "Public demo metadata is required.")]
    for key in REQUIRED_DEMO_URLS:
        value = metadata.get(key)
        if not (isinstance(value, str) and value.startswith("https://")):
            findings.append(finding(f"publicDemoMetadata.{key}", f"{key} must be an https URL metadata value."))
    verified_routes = metadata.get("verifiedRoutes", [])
    for route in REQUIRED_DEMO_ROUTES:
        if route not in verified_routes:
            findings.append(finding("publicDemoMetadata.verifiedRoutes", f"Missing verified public route `{route}`."))
    if metadata.get("videoEvidence", {}).get("mp4Embedded") is not True:
        findings.append(finding("publicDemoMetadata.videoEvidence.mp4Embedded", "Demo metadata must include embedded MP4 evidence."))
    if "Verified public routes" not in file_texts.get("demoPlan", ""):
        findings.append(finding("demoPlan.verifiedRoutes", "Walkthrough plan must record verified public routes."))
    if "ffprobe" not in file_texts.get("demoPlan", ""):
        findings.append(finding("demoPlan.qc", "Walkthrough plan must include video QC evidence."))
    if "reddiagent-demo-walkthrough.mp4" not in file_texts.get("demoBuilder", ""):
        findings.append(finding("demoBuilder.mp4", "Walkthrough build script must emit the MP4 artifact path."))
    for key in ("demoPlan", "demoBuilder"):
        if key in file_texts:
            findings.extend(sensitive_payload_findings(file_texts[key], key))
            findings.extend(unsafe_claim_findings(file_texts[key], key))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    findings.extend(unsafe_claim_findings(scenario.get("operatorNextStep", ""), "operatorNextStep"))
    findings.extend(unsafe_claim_findings(scenario.get("bundleNotes", ""), "bundleNotes"))
    findings.extend(unsafe_env_findings(scenario.get("unsafeEnvValues", {})))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in release-candidate bundle inputs."))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def selected_files(verifier_result: dict[str, Any]) -> tuple[list[str], list[str]]:
    included = sorted(set(verifier_result.get("requiredArtifactPaths", [])) | set(REQUIRED_ARTIFACTS.values()))
    excluded = [
        "live runtime activation outputs",
        "credential values or secret stores",
        "Docker/Surfpool/Coolify runtime logs from this bundle run",
        "devnet/mainnet transaction or settlement artifacts",
        "package publishing outputs",
        "production gateway deployment artifacts",
    ]
    return included, excluded


def next_step_for(verdict: str) -> str:
    if verdict == "accept":
        return "Reviewer may accept this local release-candidate bundle for planning and review only; separate approval is still required before activation, deployment, publishing, payment access, or mainnet."
    if verdict == "reject":
        return "Reject this release candidate and regenerate verifier/demo evidence before any operator activation path is considered."
    return "Hold this release candidate. Fix missing, stale, or unsafe local evidence and rerun the bundle command before any live step."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    artifacts, file_texts, findings = collect_artifacts(scenario)
    verifier_path = artifact_paths(scenario)["verifier"]
    verifier = load_verifier(verifier_path, findings)
    findings.extend(verifier_findings(verifier))
    findings.extend(demo_findings(scenario, file_texts))
    findings.extend(scenario_findings(scenario))
    verifier_result = accepted_verifier_result(verifier) or {}
    included, excluded = selected_files(verifier_result)
    status = "pass" if not findings else "fail"
    verdict = verdict_for(status, scenario.get("requestedVerdict"))
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "verifierSourceCommit": verifier.get("sourceCommit"),
        "publicDemoMetadata": scenario.get("publicDemoMetadata", {}),
        "artifactInventory": artifacts,
        "verifierEvidenceHashes": verifier_result.get("evidenceHashes", []),
        "includedFiles": included,
        "excludedFiles": excluded,
        "operatorNextStep": next_step_for(verdict),
        "boundaries": {
            "deterministicLocalOnly": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "liveRuntimeActivation": False,
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "externalSpend": False,
        },
    }


def build_report(doc: dict[str, Any], commit: str | None = None) -> dict[str, Any]:
    actual_commit = commit or source_commit()
    defaults = doc.get("defaults", {})
    results = [build_result(merge_scenario(defaults, scenario), actual_commit) for scenario in doc.get("scenarios", [])]
    mismatches = [
        finding(f"results[{index}].status", f"{result['id']} produced {result['status']}/{result['verdict']} but expected {result['expectedStatus']}/{result['expectedVerdict']}.")
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"] or result["verdict"] != result["expectedVerdict"]
    ]
    return {
        "mode": "beta-local-release-candidate-bundle",
        "issue": 273,
        "parentEpic": 220,
        "follows": [269, 271],
        "relatedEpic": 247,
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
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
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "externalSpend": False,
        },
        "mainnetStatement": "This release-candidate bundle is local/free/dry-run only. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Release-candidate bundle scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated bundle manifest JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
