#!/usr/bin/env python3
"""Assemble deterministic local beta release archive metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-archive-assembler-scenarios.json"

REQUIRED_RC_MANIFEST = "tests/fixtures/beta-release-candidate-bundle.json"
REQUIRED_RC_MODE = "beta-local-release-candidate-bundle"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_ARCHIVE_ID = "reddiagent-beta-0-rc-local-1-local-review-archive"
REQUIRED_EVIDENCE = {
    "tests/fixtures/beta-release-verification.json",
    "docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md",
    "scripts/public_demo_walkthrough_video.sh",
}
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
    "archive published",
    "published archive",
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
    "archivePublishingRequested",
    "archivePublished",
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


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


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


def expected_hash_map(scenario: dict[str, Any], field: str) -> dict[str, str]:
    return {
        item["path"]: item.get("sha256", "")
        for item in scenario.get(field, [])
        if isinstance(item, dict) and item.get("path")
    }


def rc_manifest_path(scenario: dict[str, Any]) -> str:
    return str(scenario.get("releaseCandidateManifestPath", REQUIRED_RC_MANIFEST))


def sensitive_payload_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in UNSAFE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential-like keys are not allowed in archive assembler inputs."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in archive assembler inputs."))
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
            findings.append(finding(path, f"Archive assembler must not claim `{marker}`."))
    return findings


def unsafe_env_findings(env: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(env, dict):
        return findings
    for key, value in env.items():
        if value not in ("", None, "<redacted>", "${REDACTED}", False):
            findings.append(finding(f"unsafeEnvValues.{key}", "Environment evidence may include names only, not live values."))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("archiveId") != REQUIRED_ARCHIVE_ID:
        findings.append(finding("archiveId", f"Archive id must be `{REQUIRED_ARCHIVE_ID}`."))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    findings.extend(unsafe_claim_findings(scenario.get("operatorNextStep", ""), "operatorNextStep"))
    findings.extend(unsafe_claim_findings(scenario.get("archiveNotes", ""), "archiveNotes"))
    findings.extend(unsafe_env_findings(scenario.get("unsafeEnvValues", {})))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in archive assembler inputs."))
    return findings


def load_rc_manifest(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        findings.append(finding("releaseCandidateManifest.exists", f"Release-candidate manifest `{path_text}` is missing."))
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("releaseCandidateManifest.json", f"Release-candidate manifest must be JSON: {exc}"))
        return {}


def accepted_rc_result(rc_manifest: dict[str, Any]) -> dict[str, Any] | None:
    for result in rc_manifest.get("results", []):
        if result.get("id") == "release-candidate-bundle-accept-pass":
            return result
    for result in rc_manifest.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def rc_manifest_findings(rc_manifest: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if rc_manifest.get("mode") != REQUIRED_RC_MODE:
        findings.append(finding("releaseCandidateManifest.mode", "Archive assembler requires #273 release-candidate bundle output."))
    if rc_manifest.get("status") != "pass":
        findings.append(finding("releaseCandidateManifest.status", "Release-candidate manifest must pass before archive assembly."))
    if rc_manifest.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseCandidateManifest.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if rc_manifest.get("boundaries", {}).get("deterministicLocalOnly") is not True:
        findings.append(finding("releaseCandidateManifest.boundaries.deterministicLocalOnly", "RC manifest must remain deterministic/local-only."))
    for field in ("serviceStarted", "networkAccess", "credentialAccess", "liveRuntimeActivation", "deploymentPublished", "packagePublished", "devnetAccess", "mainnetAccess", "externalSpend"):
        if rc_manifest.get("boundaries", {}).get(field) is not False:
            findings.append(finding(f"releaseCandidateManifest.boundaries.{field}", f"{field} must remain false."))
    rc_result = accepted_rc_result(rc_manifest)
    if rc_result is None:
        findings.append(finding("releaseCandidateManifest.results", "RC manifest must include an accepted passing release-candidate result."))
        return findings
    if rc_result.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateManifest.results.releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    missing = sorted(REQUIRED_EVIDENCE - set(rc_result.get("includedFiles", [])))
    for path_text in missing:
        findings.append(finding("releaseCandidateManifest.includedFiles", f"Required evidence `{path_text}` is missing from RC manifest."))
    return findings


def expected_archive_paths(scenario: dict[str, Any], rc_result: dict[str, Any], rc_path: str) -> list[str]:
    if isinstance(scenario.get("archiveFiles"), list):
        return sorted(str(path) for path in scenario["archiveFiles"])
    return sorted(set(rc_result.get("includedFiles", [])) | {rc_path})


def inventory_for(paths: list[str], expected: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    inventory: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for path_text in paths:
        path = ROOT / path_text
        exists = path.exists() and path.is_file()
        actual = digest(path) if exists else None
        expected_sha = expected.get(path_text)
        inventory.append(
            {
                "path": path_text,
                "exists": exists,
                "sizeBytes": path.stat().st_size if exists else None,
                "sha256": actual,
                "expectedSha256": expected_sha,
                "hashMatches": bool(actual and expected_sha and actual == expected_sha),
            }
        )
        if not exists:
            findings.append(finding(f"contentAddressedInventory.{path_text}.exists", f"Included archive file `{path_text}` is missing."))
        elif not expected_sha:
            findings.append(finding(f"contentAddressedInventory.{path_text}.expectedSha256", f"Expected sha256 pin is required for included file `{path_text}`."))
        elif actual != expected_sha:
            findings.append(finding(f"contentAddressedInventory.{path_text}.sha256", f"Included archive file `{path_text}` does not match its expected sha256 pin."))
    return inventory, findings


def extra_artifact_findings(scenario: dict[str, Any], expected_paths: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    extras = sorted(set(scenario.get("observedArchiveFiles", expected_paths)) - set(expected_paths))
    for path_text in extras:
        findings.append(finding("observedArchiveFiles", f"Unexpected archive artifact `{path_text}` is not part of the release-candidate manifest."))
    return findings


def archive_evidence_findings(archive_paths: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path_text in sorted(REQUIRED_EVIDENCE - set(archive_paths)):
        findings.append(finding("archiveFiles", f"Required evidence `{path_text}` is missing from the local archive file list."))
    return findings


def manifest_package(inventory: list[dict[str, Any]], scenario: dict[str, Any], rc_path: str, commit: str) -> dict[str, Any]:
    return {
        "archiveId": scenario.get("archiveId"),
        "archiveName": f"{scenario.get('archiveId')}.manifest.json",
        "archivePath": str(Path(scenario.get("archiveRoot", "local-artifacts")) / f"{scenario.get('archiveId')}.manifest.json"),
        "checksumPath": str(Path(scenario.get("archiveRoot", "local-artifacts")) / f"{scenario.get('archiveId')}.manifest.sha256"),
        "format": "manifest-and-sha256-only",
        "releaseCandidateManifestPath": rc_path,
        "sourceCommit": commit,
        "deterministicInputs": ["path", "sizeBytes", "sha256"],
        "contentAddressedInventory": inventory,
    }


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "accept":
        return "Reviewer may inspect this local manifest/checksum archive package only; publishing, deployment, activation, payment access, and mainnet still require separate approval."
    if verdict == "reject":
        return "Reject this archive assembly and regenerate the release-candidate evidence before any operator activation path is considered."
    return "Hold this archive assembly. Fix missing, stale, extra, or unsafe local evidence and rerun the assembler before any live step."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    rc_path = rc_manifest_path(scenario)
    rc_expected_hash = expected_hash_map(scenario, "expectedReleaseCandidateHashes").get(rc_path, "")
    rc_actual_hash = digest(ROOT / rc_path) if (ROOT / rc_path).exists() else None
    if not rc_expected_hash:
        findings.append(finding("releaseCandidateManifest.expectedSha256", f"Expected sha256 pin is required for `{rc_path}`."))
    elif rc_actual_hash and rc_actual_hash != rc_expected_hash:
        findings.append(finding("releaseCandidateManifest.sha256", f"Release-candidate manifest `{rc_path}` does not match its expected sha256 pin."))
    rc_manifest = load_rc_manifest(rc_path, findings)
    findings.extend(rc_manifest_findings(rc_manifest))
    rc_result = accepted_rc_result(rc_manifest) or {}
    archive_paths = expected_archive_paths(scenario, rc_result, rc_path)
    findings.extend(archive_evidence_findings(archive_paths))
    inventory, inventory_findings = inventory_for(archive_paths, expected_hash_map(scenario, "expectedIncludedFileHashes"))
    findings.extend(inventory_findings)
    findings.extend(extra_artifact_findings(scenario, archive_paths))
    package = manifest_package(inventory, scenario, rc_path, commit)
    package_payload = dump_json(package)
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
        "releaseCandidateManifest": {
            "path": rc_path,
            "sha256": rc_actual_hash,
            "expectedSha256": rc_expected_hash,
            "hashMatches": bool(rc_actual_hash and rc_expected_hash and rc_actual_hash == rc_expected_hash),
        },
        "archiveMetadata": {
            "archiveId": scenario.get("archiveId"),
            "archiveName": package["archiveName"],
            "archivePath": package["archivePath"],
            "checksumPath": package["checksumPath"],
            "format": package["format"],
            "manifestSha256": sha256_text(package_payload),
        },
        "contentAddressedInventory": inventory,
        "includedFiles": archive_paths,
        "excludedFiles": [
            "live runtime activation outputs",
            "credential values or secret stores",
            "Docker/Surfpool/Coolify runtime logs from this archive run",
            "devnet/mainnet transaction or settlement artifacts",
            "package publishing outputs",
            "archive publishing outputs",
            "production gateway deployment artifacts",
        ],
        "evidenceHashes": rc_result.get("verifierEvidenceHashes", []),
        "publicDemoMetadata": rc_result.get("publicDemoMetadata", {}),
        "operatorNextStep": next_step_for(verdict),
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunByDefault": True,
            "archiveWriteRequiresExplicitPath": True,
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
            "archivePublished": False,
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
        "mode": "beta-local-release-archive-assembler",
        "issue": 275,
        "parentEpic": 220,
        "follows": [273],
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
            "dryRunByDefault": True,
            "archiveWriteRequiresExplicitPath": True,
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
            "archivePublished": False,
            "externalSpend": False,
        },
        "mainnetStatement": "This archive assembler is local/free/dry-run by default. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_archive_package(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    positive = next(result for result in report["results"] if result["id"] == "release-archive-assemble-accept-pass")
    archive_id = positive["archiveMetadata"]["archiveId"]
    manifest_path = output_dir / f"{archive_id}.manifest.json"
    checksum_path = output_dir / f"{archive_id}.manifest.sha256"
    package = {
        "archiveMetadata": positive["archiveMetadata"],
        "contentAddressedInventory": positive["contentAddressedInventory"],
        "excludedFiles": positive["excludedFiles"],
        "releaseCandidateManifest": positive["releaseCandidateManifest"],
        "sourceCommit": positive["sourceCommit"],
    }
    payload = dump_json(package)
    manifest_path.write_text(payload)
    checksum_path.write_text(f"{sha256_text(payload)}  {manifest_path.name}\n")
    return {"manifestPath": str(manifest_path), "checksumPath": str(checksum_path)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Archive assembler scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated archive assembly report JSON.")
    parser.add_argument("--archive-output-dir", type=Path, help="Explicit local directory for the manifest/checksum archive package.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.archive_output_dir:
        output_dir = args.archive_output_dir if args.archive_output_dir.is_absolute() else ROOT / args.archive_output_dir
        report["localArchiveWrite"] = write_archive_package(report, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
