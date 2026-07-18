#!/usr/bin/env python3
"""Build deterministic local beta onboarding quickstart metadata."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart-scenarios.json"

REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_ARCHIVE_MODE = "beta-local-release-archive-assembler"
REQUIRED_ARCHIVE_PATH = "tests/fixtures/beta-release-archive-assembler.json"
REQUIRED_QUICKSTART_ID = "reddiagent-beta-0-local-onboarding-quickstart"
REQUIRED_LOCAL_FILES = {
    "archiveManifest": "tests/fixtures/beta-release-archive-assembler.json",
    "releaseVerification": "tests/fixtures/beta-release-verification.json",
    "betaReviewUi": "tests/fixtures/beta-review-ui.json",
    "surfpoolEvidence": "tests/fixtures/surfpool-validator-lane.json",
    "dockerEvidence": "tests/fixtures/docker-testing-lane.json",
    "coolifyEvidence": "tests/fixtures/coolify-staging-lane.json",
    "pitchPlan": "docs/PITCH-DEMO-REFRESH.md",
    "pitchPage": "docs/public-demo-pitch.html",
    "pitchVideoScript": "scripts/public_demo_pitch_video.sh",
}
REQUIRED_ADLS = (
    "examples/simple-agent.yaml",
    "examples/tool-agent.yaml",
    "examples/payment-agent.yaml",
)
REQUIRED_PUBLIC_DEMO_URL = "https://frosty-prism-5q6j.here.now/"
REQUIRED_PUBLIC_VIDEO_URL = "https://frosty-prism-5q6j.here.now/media/reddiagent-demo-story-cut.mp4"
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
    "docker started",
    "surfpool started",
    "coolify deployed",
    "production gateway enabled",
    "mainnet enabled",
    "deployed to production",
    "deployment completed",
    "published archive",
    "archive published",
    "published package",
    "package published",
    "live settlement",
    "settlement completed",
)
UNSAFE_FLAG_FIELDS = (
    "liveRuntimeRequested",
    "liveNetworkEnabled",
    "dockerStartRequested",
    "surfpoolStartRequested",
    "coolifyDeploymentRequested",
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
UNSAFE_COMMAND_MARKERS = (
    "docker run",
    "docker compose up",
    "docker-compose up",
    "surfpool start",
    "solana-test-validator",
    "coolify",
    "here-publish",
    "npm publish",
    "pnpm publish",
    "yarn publish",
    "openclaw gateway",
    "kubectl apply",
    "vercel deploy",
    "mainnet",
    "devnet",
    "curl http",
    "curl https",
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


def file_paths(scenario: dict[str, Any]) -> dict[str, str]:
    paths = dict(REQUIRED_LOCAL_FILES)
    overrides = scenario.get("localFilePathOverrides", {})
    if isinstance(overrides, dict):
        for key, path_text in overrides.items():
            if key in paths and isinstance(path_text, str):
                paths[key] = path_text
    return paths


def selected_adls(scenario: dict[str, Any]) -> list[str]:
    adls = scenario.get("selectedAdls", list(REQUIRED_ADLS))
    if not isinstance(adls, list):
        return []
    return [str(path) for path in adls]


def sensitive_payload_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in UNSAFE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential-like keys are not allowed in onboarding quickstart inputs."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in onboarding quickstart inputs."))
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
            findings.append(finding(path, f"Quickstart package must not claim `{marker}`."))
    return findings


def unsafe_env_findings(env: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(env, dict):
        return findings
    for key, value in env.items():
        if value not in ("", None, "<redacted>", "${REDACTED}", False):
            findings.append(finding(f"unsafeEnvValues.{key}", "Environment evidence may include names only, not live values."))
    return findings


def command_findings(commands: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(commands, list):
        findings.append(finding("commands", "Reviewer commands must be a list."))
        return findings
    for index, command in enumerate(commands):
        if not isinstance(command, str) or not command.strip():
            findings.append(finding(f"commands[{index}]", "Reviewer command must be a non-empty string."))
            continue
        lowered = command.lower()
        for marker in UNSAFE_COMMAND_MARKERS:
            if marker in lowered:
                findings.append(finding(f"commands[{index}]", f"Reviewer command must not include `{marker}`."))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    findings.extend(unsafe_claim_findings(scenario.get("operatorNextStep", ""), "operatorNextStep"))
    findings.extend(unsafe_claim_findings(scenario.get("quickstartNotes", ""), "quickstartNotes"))
    findings.extend(unsafe_env_findings(scenario.get("unsafeEnvValues", {})))
    findings.extend(command_findings(scenario.get("commands", [])))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in onboarding quickstart inputs."))
    return findings


def inventory_for(paths: dict[str, str], expected: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, str]]]:
    inventory: list[dict[str, Any]] = []
    file_texts: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for key, path_text in sorted(paths.items()):
        path = ROOT / path_text
        exists = path.exists() and path.is_file()
        actual = digest(path) if exists else None
        expected_sha = expected.get(path_text)
        inventory.append(
            {
                "key": key,
                "path": path_text,
                "exists": exists,
                "sizeBytes": path.stat().st_size if exists else None,
                "sha256": actual,
                "expectedSha256": expected_sha,
                "hashMatches": bool(actual and expected_sha and actual == expected_sha),
            }
        )
        if not exists:
            findings.append(finding(f"localFiles.{key}.exists", f"Required quickstart file `{path_text}` is missing."))
            continue
        file_texts[key] = path.read_text(errors="replace")
        if not expected_sha:
            findings.append(finding(f"localFiles.{key}.expectedSha256", f"Expected sha256 pin is required for `{path_text}`."))
        elif actual != expected_sha:
            findings.append(finding(f"localFiles.{key}.sha256", f"Quickstart file `{path_text}` does not match its expected sha256 pin."))
    return inventory, file_texts, findings


def adl_inventory_for(paths: list[str], expected: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    inventory: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    required = set(REQUIRED_ADLS)
    missing = sorted(required - set(paths))
    for path_text in missing:
        findings.append(finding("selectedAdls", f"Required example ADL `{path_text}` is missing from the quickstart."))
    for path_text in sorted(paths):
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
            findings.append(finding(f"selectedAdls.{path_text}.exists", f"Selected example ADL `{path_text}` is missing."))
        elif not expected_sha:
            findings.append(finding(f"selectedAdls.{path_text}.expectedSha256", f"Expected sha256 pin is required for selected ADL `{path_text}`."))
        elif actual != expected_sha:
            findings.append(finding(f"selectedAdls.{path_text}.sha256", f"Selected example ADL `{path_text}` does not match its expected sha256 pin."))
    return inventory, findings


def load_archive(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        findings.append(finding("archiveManifest.exists", f"Archive manifest `{path_text}` is missing."))
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("archiveManifest.json", f"Archive manifest must be JSON: {exc}"))
        return {}


def accepted_archive_result(archive: dict[str, Any]) -> dict[str, Any] | None:
    for result in archive.get("results", []):
        if result.get("id") == "release-archive-assemble-accept-pass":
            return result
    for result in archive.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def archive_findings(archive: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if archive.get("mode") != REQUIRED_ARCHIVE_MODE:
        findings.append(finding("archiveManifest.mode", "Quickstart requires #275 archive assembler output."))
    if archive.get("status") != "pass":
        findings.append(finding("archiveManifest.status", "Archive assembler manifest must pass before onboarding quickstart generation."))
    if archive.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("archiveManifest.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    for field in ("deterministicLocalOnly", "dryRunByDefault"):
        if archive.get("boundaries", {}).get(field) is not True:
            findings.append(finding(f"archiveManifest.boundaries.{field}", f"{field} must remain true."))
    for field in ("serviceStarted", "networkAccess", "credentialAccess", "liveRuntimeActivation", "deploymentPublished", "packagePublished", "archivePublished", "devnetAccess", "mainnetAccess", "externalSpend"):
        if archive.get("boundaries", {}).get(field) is not False:
            findings.append(finding(f"archiveManifest.boundaries.{field}", f"{field} must remain false."))
    result = accepted_archive_result(archive)
    if result is None:
        findings.append(finding("archiveManifest.results", "Archive manifest must include an accepted passing archive result."))
        return findings
    if result.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("archiveManifest.results.releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    return findings


def demo_metadata_findings(metadata: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(metadata, dict):
        return [finding("publicDemoMetadata", "Public demo metadata is required.")]
    if metadata.get("publicDemoUrl") != REQUIRED_PUBLIC_DEMO_URL:
        findings.append(finding("publicDemoMetadata.publicDemoUrl", "Quickstart must point to the refreshed #277 public demo URL as metadata only."))
    if metadata.get("publicVideoUrl") != REQUIRED_PUBLIC_VIDEO_URL:
        findings.append(finding("publicDemoMetadata.publicVideoUrl", "Quickstart must point to the refreshed #277 story MP4 URL as metadata only."))
    for key in ("publicDemoUrl", "publicVideoUrl"):
        value = metadata.get(key, "")
        if not isinstance(value, str) or not value.startswith("https://"):
            findings.append(finding(f"publicDemoMetadata.{key}", f"{key} must be an https URL metadata value."))
    if metadata.get("metadataOnly") is not True:
        findings.append(finding("publicDemoMetadata.metadataOnly", "Public demo URLs must be metadata/proof links only."))
    if metadata.get("fetchedDuringQuickstart") is not False:
        findings.append(finding("publicDemoMetadata.fetchedDuringQuickstart", "Quickstart generation must not fetch hosted demo content."))
    if metadata.get("publishedDuringQuickstart") is not False:
        findings.append(finding("publicDemoMetadata.publishedDuringQuickstart", "Quickstart generation must not publish hosted demo content."))
    return findings


def required_marker_findings(file_texts: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    checks = {
        "pitchPlan": ("Issue: #277", "static/local/dry-run evidence only"),
        "pitchPage": ("ReddiAgent Public Demo", "Three audiences, one contract"),
        "pitchVideoScript": ("reddiagent-demo-story-cut.mp4", "does not activate a runtime"),
    }
    for key, markers in checks.items():
        text = file_texts.get(key, "")
        for marker in markers:
            if marker not in text:
                findings.append(finding(key, f"Required pitch demo marker `{marker}` is missing."))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "accept":
        return "Open the generated local quickstart file and inspect the listed local commands only; runtime activation, hosted publishing, package/archive publishing, payment access, devnet, and mainnet still require separate approval."
    if verdict == "reject":
        return "Reject this onboarding package and regenerate local evidence before any reviewer or operator handoff."
    return "Hold this onboarding package. Fix missing, stale, unsafe, or overclaiming local evidence and rerun before any live step."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    expected_files = expected_hash_map(scenario, "expectedLocalFileHashes")
    expected_adls = expected_hash_map(scenario, "expectedAdlHashes")
    archive_path = scenario.get("archiveManifestPath", REQUIRED_ARCHIVE_PATH)
    archive_expected_hash = expected_files.get(archive_path, "")
    archive_actual_hash = digest(ROOT / archive_path) if (ROOT / archive_path).exists() else None
    if not archive_expected_hash:
        findings.append(finding("archiveManifest.expectedSha256", f"Expected sha256 pin is required for `{archive_path}`."))
    elif archive_actual_hash and archive_actual_hash != archive_expected_hash:
        findings.append(finding("archiveManifest.sha256", f"Archive manifest `{archive_path}` does not match its expected sha256 pin."))
    archive = load_archive(archive_path, findings)
    findings.extend(archive_findings(archive))
    local_inventory, file_texts, local_findings = inventory_for(file_paths(scenario), expected_files)
    findings.extend(local_findings)
    adl_inventory, adl_findings = adl_inventory_for(selected_adls(scenario), expected_adls)
    findings.extend(adl_findings)
    findings.extend(demo_metadata_findings(scenario.get("publicDemoMetadata", {})))
    findings.extend(required_marker_findings(file_texts))
    archive_result = accepted_archive_result(archive) or {}
    package = {
        "quickstartId": scenario.get("quickstartId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "sourceCommit": commit,
        "archiveManifest": {
            "path": archive_path,
            "sha256": archive_actual_hash,
            "expectedSha256": archive_expected_hash,
            "hashMatches": bool(archive_actual_hash and archive_expected_hash and archive_actual_hash == archive_expected_hash),
        },
        "publicDemoMetadata": scenario.get("publicDemoMetadata", {}),
        "localFileInventory": local_inventory,
        "selectedAdls": adl_inventory,
        "commands": scenario.get("commands", []),
        "operatorNextStep": next_step_for("accept"),
    }
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
        "quickstartId": scenario.get("quickstartId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "releaseArchive": {
            "path": archive_path,
            "sha256": archive_actual_hash,
            "expectedSha256": archive_expected_hash,
            "hashMatches": bool(archive_actual_hash and archive_expected_hash and archive_actual_hash == archive_expected_hash),
            "archiveId": archive_result.get("archiveMetadata", {}).get("archiveId"),
            "archiveManifestSha256": archive_result.get("archiveMetadata", {}).get("manifestSha256"),
        },
        "publicDemoMetadata": scenario.get("publicDemoMetadata", {}),
        "localEntrypoint": {
            "format": "html-and-manifest-json",
            "defaultWrite": False,
            "writeRequiresExplicitOutputDir": True,
            "manifestName": f"{scenario.get('quickstartId')}.json",
            "htmlName": f"{scenario.get('quickstartId')}.html",
            "manifestSha256": sha256_text(package_payload),
        },
        "localFileInventory": local_inventory,
        "selectedAdls": adl_inventory,
        "commands": scenario.get("commands", []),
        "expectedOutputs": scenario.get("expectedOutputs", []),
        "excludedSteps": [
            "runtime activation",
            "Docker image pull or container start",
            "Surfpool or solana-test-validator start",
            "Coolify deployment or mutation",
            "hosted content fetch, mutation, or publication",
            "credential lookup or storage",
            "provider/model/API product call",
            "live MCP invocation",
            "wallet/payment/facilitator/settlement access",
            "devnet or mainnet transaction",
            "package or archive publishing",
            "production gateway mutation",
        ],
        "operatorNextStep": next_step_for(verdict),
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunByDefault": True,
            "quickstartWriteRequiresExplicitPath": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "liveRuntimeActivation": False,
            "dockerStarted": False,
            "surfpoolStarted": False,
            "coolifyDeployment": False,
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "archivePublished": False,
            "publicPublished": False,
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
        "mode": "beta-local-onboarding-quickstart-package",
        "issue": 279,
        "parentEpic": 220,
        "follows": [275, 277],
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
            "quickstartWriteRequiresExplicitPath": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "liveRuntimeActivation": False,
            "dockerStarted": False,
            "surfpoolStarted": False,
            "coolifyDeployment": False,
            "walletAccess": False,
            "paymentAccess": False,
            "facilitatorAccess": False,
            "settlementAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
            "packagePublished": False,
            "archivePublished": False,
            "publicPublished": False,
            "externalSpend": False,
        },
        "mainnetStatement": "This onboarding quickstart is local/free/dry-run by default. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def quickstart_html(result: dict[str, Any]) -> str:
    rows = "\n".join(
        f"<li><code>{html.escape(item['path'])}</code> <span>{html.escape(item.get('sha256') or 'missing')}</span></li>"
        for item in result["localFileInventory"] + result["selectedAdls"]
    )
    commands = "\n".join(f"<li><code>{html.escape(command)}</code></li>" for command in result["commands"])
    proof = result["publicDemoMetadata"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ReddiAgent Local Beta Quickstart</title>
  <style>
    body {{ max-width: 960px; margin: 40px auto; padding: 0 20px; font: 16px/1.55 ui-sans-serif, system-ui, sans-serif; color: #17191f; }}
    code {{ background: #f1f3f6; padding: 2px 4px; border-radius: 4px; }}
    li {{ margin: 8px 0; }}
    .boundary {{ border: 1px solid #d9dde5; border-radius: 8px; padding: 16px; background: #fbfcfd; }}
  </style>
</head>
<body>
  <h1>ReddiAgent Local Beta Quickstart</h1>
  <p>Release <code>{html.escape(result['releaseId'])}</code>, candidate <code>{html.escape(result['releaseCandidateId'])}</code>.</p>
  <p>Public proof links are metadata only: <a href="{html.escape(proof.get('publicDemoUrl', '#'))}">demo</a> and <a href="{html.escape(proof.get('publicVideoUrl', '#'))}">story video</a>.</p>
  <h2>Local Commands</h2>
  <ol>{commands}</ol>
  <h2>Local Evidence</h2>
  <ul>{rows}</ul>
  <div class="boundary">
    <strong>Boundary:</strong> this quickstart does not start services, fetch or publish hosted content, access credentials, call providers, invoke live MCP, touch wallets/payments, run devnet/mainnet, deploy, or publish packages/archives.
  </div>
</body>
</html>
"""


def write_quickstart(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / result["localEntrypoint"]["manifestName"]
    html_path = output_dir / result["localEntrypoint"]["htmlName"]
    manifest = {
        "quickstartId": result["quickstartId"],
        "releaseId": result["releaseId"],
        "releaseCandidateId": result["releaseCandidateId"],
        "releaseArchive": result["releaseArchive"],
        "publicDemoMetadata": result["publicDemoMetadata"],
        "localFileInventory": result["localFileInventory"],
        "selectedAdls": result["selectedAdls"],
        "commands": result["commands"],
        "expectedOutputs": result["expectedOutputs"],
        "excludedSteps": result["excludedSteps"],
        "operatorNextStep": result["operatorNextStep"],
        "boundaries": result["boundaries"],
        "sourceCommit": result["sourceCommit"],
    }
    payload = dump_json(manifest)
    manifest_path.write_text(payload)
    html_path.write_text(quickstart_html(result))
    return {
        "manifestPath": str(manifest_path),
        "manifestSha256": sha256_text(payload),
        "htmlPath": str(html_path),
        "htmlSha256": digest(html_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Quickstart scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated quickstart report JSON.")
    parser.add_argument("--quickstart-output-dir", type=Path, help="Explicit local directory for the quickstart manifest and HTML entrypoint.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.quickstart_output_dir:
        output_dir = args.quickstart_output_dir if args.quickstart_output_dir.is_absolute() else ROOT / args.quickstart_output_dir
        positive = next(result for result in report["results"] if result["id"] == "quickstart-assemble-accept-pass")
        report["localQuickstartWrite"] = write_quickstart(positive, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
