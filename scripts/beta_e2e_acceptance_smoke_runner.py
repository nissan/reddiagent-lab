#!/usr/bin/env python3
"""Build deterministic local beta end-to-end acceptance smoke evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-e2e-acceptance-smoke-scenarios.json"

REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_QUICKSTART_ID = "reddiagent-beta-0-local-onboarding-quickstart"
REQUIRED_CHECKLIST_ID = "reddiagent-beta-0-local-reviewer-acceptance-checklist"
REQUIRED_SMOKE_ID = "reddiagent-beta-0-local-e2e-acceptance-smoke"
REQUIRED_QUICKSTART_PATH = "tests/fixtures/beta-onboarding-quickstart.json"
REQUIRED_CHECKLIST_PATH = "tests/fixtures/beta-reviewer-acceptance-checklist.json"
REQUIRED_QUICKSTART_MODE = "beta-local-onboarding-quickstart-package"
REQUIRED_CHECKLIST_MODE = "beta-local-reviewer-acceptance-checklist-package"
REQUIRED_QUICKSTART_INVENTORY = {
    "archiveManifest": "tests/fixtures/beta-release-archive-assembler.json",
    "betaReviewUi": "tests/fixtures/beta-review-ui.json",
    "coolifyEvidence": "tests/fixtures/coolify-staging-lane.json",
    "dockerEvidence": "tests/fixtures/docker-testing-lane.json",
    "pitchPage": "docs/public-demo-pitch.html",
    "pitchPlan": "docs/PITCH-DEMO-REFRESH.md",
    "pitchVideoScript": "scripts/public_demo_pitch_video.sh",
    "releaseVerification": "tests/fixtures/beta-release-verification.json",
    "surfpoolEvidence": "tests/fixtures/surfpool-validator-lane.json",
}
REQUIRED_CHECKLIST_ITEMS = (
    "quickstart-fixture-current",
    "local-file-inventory-hashes",
    "reviewer-command-boundaries",
    "operator-next-step-cue",
    "mainnet-remains-blocked",
)
REQUIRED_LOCAL_COMMANDS = (
    "scripts/beta_onboarding_quickstart_package.py",
    "scripts/beta_reviewer_acceptance_checklist_package.py",
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
    "liveMcpRequested",
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
UNSAFE_COMMAND_MARKERS = {
    "coolify",
    "devnet",
    "here-publish",
    "mainnet",
    "mcp",
    "solana-test-validator",
}
UNSAFE_DOCKER_SUBCOMMANDS = {"compose", "container", "pull", "run", "start"}
UNSAFE_PACKAGE_PUBLISH_COMMANDS = {
    ("gh", "release", "upload"),
    ("npm", "publish"),
    ("pnpm", "publish"),
    ("yarn", "publish"),
    ("vercel", "deploy"),
    ("kubectl", "apply"),
    ("openclaw", "gateway"),
}
HOSTED_FETCH_COMMANDS = {"curl", "wget"}


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


def sensitive_payload_findings(value: Any, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in UNSAFE_KEYS_NORMALIZED:
                findings.append(finding(child_path, "Credential-like keys are not allowed in e2e smoke inputs."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in e2e smoke inputs."))
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
            findings.append(finding(path, f"E2E smoke must not claim `{marker}`."))
    return findings


def command_findings(commands: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(commands, list):
        return [finding("localCommands", "Local commands must be a list.")]
    for index, command in enumerate(commands):
        if not isinstance(command, str) or not command.strip():
            findings.append(finding(f"localCommands[{index}]", "Local command must be a non-empty string."))
            continue
        lowered = command.lower()
        for marker in UNSAFE_COMMAND_MARKERS:
            if marker in lowered:
                findings.append(finding(f"localCommands[{index}]", f"Local command must not include `{marker}`."))
        try:
            tokens = [token.lower() for token in shlex.split(command)]
        except ValueError:
            tokens = lowered.split()
        if not tokens:
            continue
        if tokens[0] == "docker" and any(token in UNSAFE_DOCKER_SUBCOMMANDS for token in tokens[1:]):
            findings.append(finding(f"localCommands[{index}]", "Local command must not pull, start, run, or compose Docker containers."))
        if tokens[0] == "docker-compose" and "up" in tokens[1:]:
            findings.append(finding(f"localCommands[{index}]", "Local command must not start Docker Compose services."))
        if tokens[0] in HOSTED_FETCH_COMMANDS and any(token.startswith(("http://", "https://")) for token in tokens[1:]):
            findings.append(finding(f"localCommands[{index}]", "Local command must not fetch hosted content."))
        for unsafe in UNSAFE_PACKAGE_PUBLISH_COMMANDS:
            if len(tokens) >= len(unsafe) and tuple(tokens[: len(unsafe)]) == unsafe:
                findings.append(finding(f"localCommands[{index}]", f"Local command must not run `{' '.join(unsafe)}`."))
    command_text = "\n".join(command for command in commands if isinstance(command, str))
    for required in REQUIRED_LOCAL_COMMANDS:
        if required not in command_text:
            findings.append(finding("localCommands", f"Required local command `{required}` is missing."))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("smokeId") != REQUIRED_SMOKE_ID:
        findings.append(finding("smokeId", f"Smoke id must be `{REQUIRED_SMOKE_ID}`."))
    if scenario.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    if scenario.get("checklistId") != REQUIRED_CHECKLIST_ID:
        findings.append(finding("checklistId", f"Checklist id must be `{REQUIRED_CHECKLIST_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    findings.extend(unsafe_claim_findings(scenario.get("smokeNotes", ""), "smokeNotes"))
    findings.extend(unsafe_claim_findings(scenario.get("nextStepCue", ""), "nextStepCue"))
    findings.extend(command_findings(scenario.get("localCommands", [])))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in e2e smoke inputs."))
    return findings


def load_artifact(path_text: str, label: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        findings.append(finding(f"{label}.exists", f"Artifact `{path_text}` is missing."))
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding(f"{label}.json", f"Artifact must be JSON: {exc}"))
        return {}


def accepted_quickstart_result(quickstart: dict[str, Any]) -> dict[str, Any] | None:
    for result in quickstart.get("results", []):
        if result.get("id") == "quickstart-assemble-accept-pass":
            return result
    for result in quickstart.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def accepted_checklist_result(checklist: dict[str, Any]) -> dict[str, Any] | None:
    for result in checklist.get("results", []):
        if result.get("id") == "reviewer-checklist-accept-pass":
            return result
    for result in checklist.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def boundary_findings(doc: dict[str, Any], label: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field in ("deterministicLocalOnly", "dryRunByDefault"):
        if doc.get("boundaries", {}).get(field) is not True:
            findings.append(finding(f"{label}.boundaries.{field}", f"{field} must remain true."))
    for field in ("serviceStarted", "networkAccess", "credentialAccess", "providerApiAccess", "liveRuntimeActivation", "dockerStarted", "surfpoolStarted", "coolifyDeployment", "walletAccess", "paymentAccess", "facilitatorAccess", "settlementAccess", "devnetAccess", "mainnetAccess", "deploymentPublished", "packagePublished", "archivePublished", "publicPublished", "externalSpend"):
        if doc.get("boundaries", {}).get(field) is not False:
            findings.append(finding(f"{label}.boundaries.{field}", f"{field} must remain false."))
    return findings


def quickstart_findings(quickstart: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if quickstart.get("mode") != REQUIRED_QUICKSTART_MODE:
        findings.append(finding("quickstartFixture.mode", "E2E smoke requires #279 onboarding quickstart output."))
    if quickstart.get("status") != "pass":
        findings.append(finding("quickstartFixture.status", "Onboarding quickstart fixture must pass before e2e smoke."))
    if quickstart.get("issue") != 279:
        findings.append(finding("quickstartFixture.issue", "Onboarding quickstart fixture must be issue #279 evidence."))
    if quickstart.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("quickstartFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    findings.extend(boundary_findings(quickstart, "quickstartFixture"))
    result = accepted_quickstart_result(quickstart)
    if result is None:
        findings.append(finding("quickstartFixture.results", "Quickstart fixture must include an accepted passing quickstart result."))
        return findings
    if result.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("quickstartFixture.results.quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    if result.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("quickstartFixture.results.releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    inventory = result.get("localFileInventory", [])
    if not inventory or not all(item.get("hashMatches") for item in inventory):
        findings.append(finding("quickstartFixture.results.localFileInventory", "Accepted quickstart must include matching local file inventory hashes."))
    inventory_paths_by_key = {item.get("key"): item.get("path") for item in inventory if isinstance(item, dict) and item.get("key")}
    for key, required_path in REQUIRED_QUICKSTART_INVENTORY.items():
        if inventory_paths_by_key.get(key) != required_path:
            findings.append(finding("quickstartFixture.results.localFileInventory", f"Accepted quickstart must include `{key}` at `{required_path}`."))
    if len(result.get("selectedAdls", [])) < 3:
        findings.append(finding("quickstartFixture.results.selectedAdls", "Accepted quickstart must include selected ADL hashes."))
    if not result.get("commands"):
        findings.append(finding("quickstartFixture.results.commands", "Accepted quickstart must include local commands."))
    return findings


def checklist_findings(checklist: dict[str, Any], quickstart_hash: str | None) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if checklist.get("mode") != REQUIRED_CHECKLIST_MODE:
        findings.append(finding("checklistFixture.mode", "E2E smoke requires #283 reviewer checklist output."))
    if checklist.get("status") != "pass":
        findings.append(finding("checklistFixture.status", "Reviewer checklist fixture must pass before e2e smoke."))
    if checklist.get("issue") != 283:
        findings.append(finding("checklistFixture.issue", "Reviewer checklist fixture must be issue #283 evidence."))
    if checklist.get("follows") != [279]:
        findings.append(finding("checklistFixture.follows", "Reviewer checklist fixture must follow #279."))
    if checklist.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("checklistFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    findings.extend(boundary_findings(checklist, "checklistFixture"))
    result = accepted_checklist_result(checklist)
    if result is None:
        findings.append(finding("checklistFixture.results", "Reviewer checklist fixture must include an accepted passing checklist result."))
        return findings
    if result.get("checklistId") != REQUIRED_CHECKLIST_ID:
        findings.append(finding("checklistFixture.results.checklistId", f"Checklist id must be `{REQUIRED_CHECKLIST_ID}`."))
    if result.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("checklistFixture.results.quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    if result.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("checklistFixture.results.releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    quickstart_fixture = result.get("quickstartFixture", {})
    if quickstart_fixture.get("path") != REQUIRED_QUICKSTART_PATH:
        findings.append(finding("checklistFixture.results.quickstartFixture.path", f"Checklist must point to `{REQUIRED_QUICKSTART_PATH}`."))
    if quickstart_hash and quickstart_fixture.get("sha256") != quickstart_hash:
        findings.append(finding("checklistFixture.results.quickstartFixture.sha256", "Checklist quickstart sha256 must match the consumed quickstart artifact."))
    if quickstart_fixture.get("hashMatches") is not True:
        findings.append(finding("checklistFixture.results.quickstartFixture.hashMatches", "Checklist quickstart fixture hash must match."))
    checklist_ids = {item.get("id") for item in result.get("checklistItems", []) if isinstance(item, dict)}
    for item_id in REQUIRED_CHECKLIST_ITEMS:
        if item_id not in checklist_ids:
            findings.append(finding("checklistFixture.results.checklistItems", f"Required checklist item `{item_id}` is missing."))
    if not result.get("reviewerCommands"):
        findings.append(finding("checklistFixture.results.reviewerCommands", "Checklist must include reviewer commands."))
    if REQUIRED_QUICKSTART_PATH not in result.get("evidencePaths", []):
        findings.append(finding("checklistFixture.results.evidencePaths", f"Checklist evidence paths must include `{REQUIRED_QUICKSTART_PATH}`."))
    return findings


def artifact_binding(path_text: str, expected_hash: str, label: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    actual_hash = digest(path) if path.exists() else None
    if not expected_hash:
        findings.append(finding(f"{label}.expectedSha256", f"Expected sha256 pin is required for `{path_text}`."))
    elif actual_hash and actual_hash != expected_hash:
        findings.append(finding(f"{label}.sha256", f"Artifact `{path_text}` does not match its expected sha256 pin."))
    return {
        "path": path_text,
        "sha256": actual_hash,
        "expectedSha256": expected_hash,
        "hashMatches": bool(actual_hash and expected_hash and actual_hash == expected_hash),
    }


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold", "reject"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "accept":
        return "Accept this local e2e smoke evidence for reviewer/operator handoff only; runtime activation, hosted publishing, package/archive publishing, payment access, devnet, and mainnet remain separate gates."
    if verdict == "reject":
        return "Reject this e2e smoke evidence and regenerate #279/#283 local artifacts before any runtime activation handoff."
    return "Hold this e2e smoke evidence. Fix missing, stale, unsafe, or overclaiming local evidence and rerun before any live step."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    quickstart_path = scenario.get("quickstartFixturePath", REQUIRED_QUICKSTART_PATH)
    checklist_path = scenario.get("checklistFixturePath", REQUIRED_CHECKLIST_PATH)
    expected_quickstart_hash = expected_hash_map(scenario, "expectedArtifactHashes").get(quickstart_path, "")
    expected_checklist_hash = expected_hash_map(scenario, "expectedArtifactHashes").get(checklist_path, "")
    quickstart_binding = artifact_binding(quickstart_path, expected_quickstart_hash, "quickstartFixture", findings)
    checklist_binding = artifact_binding(checklist_path, expected_checklist_hash, "checklistFixture", findings)
    quickstart = load_artifact(quickstart_path, "quickstartFixture", findings)
    checklist = load_artifact(checklist_path, "checklistFixture", findings)
    findings.extend(quickstart_findings(quickstart))
    findings.extend(checklist_findings(checklist, quickstart_binding["sha256"]))
    quickstart_result = accepted_quickstart_result(quickstart) or {}
    checklist_result = accepted_checklist_result(checklist) or {}
    status = "pass" if not findings else "fail"
    verdict = verdict_for(status, scenario.get("requestedVerdict"))
    evidence_payload = {
        "smokeId": scenario.get("smokeId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "verdict": verdict,
        "quickstartFixture": quickstart_binding,
        "checklistFixture": checklist_binding,
        "localCommands": scenario.get("localCommands", []),
        "expectedOutputs": scenario.get("expectedOutputs", []),
        "requiredEvidencePaths": scenario.get("requiredEvidencePaths", []),
        "nextStepCue": next_step_for(verdict),
    }
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "smokeId": scenario.get("smokeId"),
        "quickstartId": scenario.get("quickstartId"),
        "checklistId": scenario.get("checklistId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "quickstartFixture": quickstart_binding,
        "checklistFixture": checklist_binding,
        "quickstartAcceptedResult": {
            "id": quickstart_result.get("id"),
            "status": quickstart_result.get("status"),
            "verdict": quickstart_result.get("verdict"),
            "localFileCount": len(quickstart_result.get("localFileInventory", [])),
            "selectedAdlCount": len(quickstart_result.get("selectedAdls", [])),
            "commandCount": len(quickstart_result.get("commands", [])),
        },
        "reviewerChecklistAcceptedResult": {
            "id": checklist_result.get("id"),
            "status": checklist_result.get("status"),
            "verdict": checklist_result.get("verdict"),
            "checklistItemCount": len(checklist_result.get("checklistItems", [])),
            "reviewerCommandCount": len(checklist_result.get("reviewerCommands", [])),
            "evidencePathCount": len(checklist_result.get("evidencePaths", [])),
        },
        "localCommands": scenario.get("localCommands", []),
        "expectedOutputs": scenario.get("expectedOutputs", []),
        "requiredEvidencePaths": scenario.get("requiredEvidencePaths", []),
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
        "nextStepCue": next_step_for(verdict),
        "evidenceSha256": sha256_text(dump_json(evidence_payload)),
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunByDefault": True,
            "evidenceWriteRequiresExplicitPath": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "liveMcpInvocation": False,
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
        "mode": "beta-local-e2e-acceptance-smoke-runner",
        "issue": 285,
        "parentEpic": 220,
        "follows": [279, 283],
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
            "evidenceWriteRequiresExplicitPath": True,
            "serviceStarted": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "liveMcpInvocation": False,
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
        "mainnetStatement": "This e2e acceptance smoke runner is local/free/dry-run by default. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_evidence(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{result['smokeId']}.json"
    payload = dump_json(
        {
            "smokeId": result["smokeId"],
            "quickstartId": result["quickstartId"],
            "checklistId": result["checklistId"],
            "releaseId": result["releaseId"],
            "releaseCandidateId": result["releaseCandidateId"],
            "verdict": result["verdict"],
            "quickstartFixture": result["quickstartFixture"],
            "checklistFixture": result["checklistFixture"],
            "quickstartAcceptedResult": result["quickstartAcceptedResult"],
            "reviewerChecklistAcceptedResult": result["reviewerChecklistAcceptedResult"],
            "localCommands": result["localCommands"],
            "expectedOutputs": result["expectedOutputs"],
            "requiredEvidencePaths": result["requiredEvidencePaths"],
            "excludedSteps": result["excludedSteps"],
            "nextStepCue": result["nextStepCue"],
            "boundaries": result["boundaries"],
            "sourceCommit": result["sourceCommit"],
        }
    )
    manifest_path.write_text(payload)
    return {"manifestPath": str(manifest_path), "manifestSha256": sha256_text(payload)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="E2E smoke scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated e2e smoke report JSON.")
    parser.add_argument("--evidence-output-dir", type=Path, help="Explicit local directory for the accepted e2e smoke evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.evidence_output_dir:
        output_dir = args.evidence_output_dir if args.evidence_output_dir.is_absolute() else ROOT / args.evidence_output_dir
        positive = next(result for result in report["results"] if result["id"] == "e2e-acceptance-smoke-accept-pass")
        report["localEvidenceWrite"] = write_evidence(positive, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
