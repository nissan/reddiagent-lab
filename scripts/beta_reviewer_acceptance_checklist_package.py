#!/usr/bin/env python3
"""Build deterministic local beta reviewer acceptance checklist metadata."""

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
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-reviewer-acceptance-checklist-scenarios.json"

REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_QUICKSTART_ID = "reddiagent-beta-0-local-onboarding-quickstart"
REQUIRED_CHECKLIST_ID = "reddiagent-beta-0-local-reviewer-acceptance-checklist"
REQUIRED_QUICKSTART_PATH = "tests/fixtures/beta-onboarding-quickstart.json"
REQUIRED_QUICKSTART_MODE = "beta-local-onboarding-quickstart-package"
REQUIRED_CHECKLIST_ITEMS = (
    "quickstart-fixture-current",
    "local-file-inventory-hashes",
    "reviewer-command-boundaries",
    "operator-next-step-cue",
    "mainnet-remains-blocked",
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
                findings.append(finding(child_path, "Credential-like keys are not allowed in reviewer checklist inputs."))
            findings.extend(sensitive_payload_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_payload_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like values are not allowed in reviewer checklist inputs."))
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
            findings.append(finding(path, f"Reviewer checklist must not claim `{marker}`."))
    return findings


def command_findings(commands: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(commands, list):
        return [finding("reviewerCommands", "Reviewer commands must be a list.")]
    for index, command in enumerate(commands):
        if not isinstance(command, str) or not command.strip():
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer command must be a non-empty string."))
            continue
        lowered = command.lower()
        for marker in UNSAFE_COMMAND_MARKERS:
            if marker in lowered:
                findings.append(finding(f"reviewerCommands[{index}]", f"Reviewer command must not include `{marker}`."))
        try:
            tokens = [token.lower() for token in shlex.split(command)]
        except ValueError:
            tokens = lowered.split()
        if not tokens:
            continue
        if tokens[0] == "docker" and any(token in UNSAFE_DOCKER_SUBCOMMANDS for token in tokens[1:]):
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer command must not pull, start, run, or compose Docker containers."))
        if tokens[0] == "docker-compose" and "up" in tokens[1:]:
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer command must not start Docker Compose services."))
        if tokens[0] in HOSTED_FETCH_COMMANDS and any(token.startswith(("http://", "https://")) for token in tokens[1:]):
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer command must not fetch hosted content."))
        for unsafe in UNSAFE_PACKAGE_PUBLISH_COMMANDS:
            if len(tokens) >= len(unsafe) and tuple(tokens[: len(unsafe)]) == unsafe:
                findings.append(finding(f"reviewerCommands[{index}]", f"Reviewer command must not run `{' '.join(unsafe)}`."))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("checklistId") != REQUIRED_CHECKLIST_ID:
        findings.append(finding("checklistId", f"Checklist id must be `{REQUIRED_CHECKLIST_ID}`."))
    if scenario.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    checklist_ids = {item.get("id") for item in scenario.get("checklistItems", []) if isinstance(item, dict)}
    for item_id in REQUIRED_CHECKLIST_ITEMS:
        if item_id not in checklist_ids:
            findings.append(finding("checklistItems", f"Required checklist item `{item_id}` is missing."))
    findings.extend(sensitive_payload_findings(scenario, "scenario"))
    findings.extend(unsafe_claim_findings(scenario.get("reviewerNotes", ""), "reviewerNotes"))
    findings.extend(unsafe_claim_findings(scenario.get("nextStepCue", ""), "nextStepCue"))
    findings.extend(command_findings(scenario.get("reviewerCommands", [])))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in reviewer checklist inputs."))
    return findings


def load_quickstart(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        findings.append(finding("quickstartFixture.exists", f"Quickstart fixture `{path_text}` is missing."))
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("quickstartFixture.json", f"Quickstart fixture must be JSON: {exc}"))
        return {}


def accepted_quickstart_result(quickstart: dict[str, Any]) -> dict[str, Any] | None:
    for result in quickstart.get("results", []):
        if result.get("id") == "quickstart-assemble-accept-pass":
            return result
    for result in quickstart.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def quickstart_findings(quickstart: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if quickstart.get("mode") != REQUIRED_QUICKSTART_MODE:
        findings.append(finding("quickstartFixture.mode", "Reviewer checklist requires #279 onboarding quickstart output."))
    if quickstart.get("status") != "pass":
        findings.append(finding("quickstartFixture.status", "Onboarding quickstart fixture must pass before reviewer checklist generation."))
    if quickstart.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("quickstartFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    for field in ("deterministicLocalOnly", "dryRunByDefault"):
        if quickstart.get("boundaries", {}).get(field) is not True:
            findings.append(finding(f"quickstartFixture.boundaries.{field}", f"{field} must remain true."))
    for field in ("serviceStarted", "networkAccess", "credentialAccess", "providerApiAccess", "liveRuntimeActivation", "dockerStarted", "surfpoolStarted", "coolifyDeployment", "walletAccess", "paymentAccess", "facilitatorAccess", "settlementAccess", "devnetAccess", "mainnetAccess", "deploymentPublished", "packagePublished", "archivePublished", "publicPublished", "externalSpend"):
        if quickstart.get("boundaries", {}).get(field) is not False:
            findings.append(finding(f"quickstartFixture.boundaries.{field}", f"{field} must remain false."))
    result = accepted_quickstart_result(quickstart)
    if result is None:
        findings.append(finding("quickstartFixture.results", "Quickstart fixture must include an accepted passing quickstart result."))
        return findings
    if result.get("quickstartId") != REQUIRED_QUICKSTART_ID:
        findings.append(finding("quickstartFixture.results.quickstartId", f"Quickstart id must be `{REQUIRED_QUICKSTART_ID}`."))
    if result.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("quickstartFixture.results.releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if not result.get("localFileInventory") or not all(item.get("hashMatches") for item in result.get("localFileInventory", [])):
        findings.append(finding("quickstartFixture.results.localFileInventory", "Accepted quickstart must include matching local file inventory hashes."))
    if not result.get("commands"):
        findings.append(finding("quickstartFixture.results.commands", "Accepted quickstart must include local reviewer/operator commands."))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept", "hold", "reject"} else "accept"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "accept":
        return "Accept this local reviewer checklist as evidence for human review only; runtime activation, hosted publishing, package/archive publishing, payment access, devnet, and mainnet remain separate gates."
    if verdict == "reject":
        return "Reject this reviewer checklist package and regenerate local quickstart evidence before any runtime or operator handoff."
    return "Hold this reviewer checklist package. Fix missing, stale, unsafe, or overclaiming local evidence and rerun before any live step."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    quickstart_path = scenario.get("quickstartFixturePath", REQUIRED_QUICKSTART_PATH)
    expected_quickstart_hash = expected_hash_map(scenario, "expectedQuickstartHashes").get(quickstart_path, "")
    actual_quickstart_hash = digest(ROOT / quickstart_path) if (ROOT / quickstart_path).exists() else None
    if not expected_quickstart_hash:
        findings.append(finding("quickstartFixture.expectedSha256", f"Expected sha256 pin is required for `{quickstart_path}`."))
    elif actual_quickstart_hash and actual_quickstart_hash != expected_quickstart_hash:
        findings.append(finding("quickstartFixture.sha256", f"Quickstart fixture `{quickstart_path}` does not match its expected sha256 pin."))
    quickstart = load_quickstart(quickstart_path, findings)
    findings.extend(quickstart_findings(quickstart))
    quickstart_result = accepted_quickstart_result(quickstart) or {}
    checklist_payload = {
        "checklistId": scenario.get("checklistId"),
        "quickstartId": scenario.get("quickstartId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "quickstartFixture": {
            "path": quickstart_path,
            "sha256": actual_quickstart_hash,
            "expectedSha256": expected_quickstart_hash,
            "hashMatches": bool(actual_quickstart_hash and expected_quickstart_hash and actual_quickstart_hash == expected_quickstart_hash),
        },
        "checklistItems": scenario.get("checklistItems", []),
        "reviewerCommands": scenario.get("reviewerCommands", []),
        "evidencePaths": scenario.get("evidencePaths", []),
        "nextStepCue": scenario.get("nextStepCue", ""),
    }
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
        "checklistId": scenario.get("checklistId"),
        "quickstartId": scenario.get("quickstartId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "quickstartFixture": checklist_payload["quickstartFixture"],
        "quickstartAcceptedResult": {
            "id": quickstart_result.get("id"),
            "status": quickstart_result.get("status"),
            "verdict": quickstart_result.get("verdict"),
            "localFileCount": len(quickstart_result.get("localFileInventory", [])),
            "selectedAdlCount": len(quickstart_result.get("selectedAdls", [])),
            "commandCount": len(quickstart_result.get("commands", [])),
            "publicDemoMetadata": quickstart_result.get("publicDemoMetadata", {}),
        },
        "checklistItems": scenario.get("checklistItems", []),
        "reviewerCommands": scenario.get("reviewerCommands", []),
        "evidencePaths": scenario.get("evidencePaths", []),
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
        "nextStepCue": next_step_for(verdict),
        "manifestSha256": sha256_text(dump_json(checklist_payload)),
        "boundaries": {
            "deterministicLocalOnly": True,
            "dryRunByDefault": True,
            "checklistWriteRequiresExplicitPath": True,
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
        "mode": "beta-local-reviewer-acceptance-checklist-package",
        "issue": 283,
        "parentEpic": 220,
        "follows": [279],
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
            "checklistWriteRequiresExplicitPath": True,
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
        "mainnetStatement": "This reviewer checklist package is local/free/dry-run by default. It does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_checklist(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{result['checklistId']}.json"
    payload = dump_json(
        {
            "checklistId": result["checklistId"],
            "quickstartId": result["quickstartId"],
            "releaseId": result["releaseId"],
            "releaseCandidateId": result["releaseCandidateId"],
            "quickstartFixture": result["quickstartFixture"],
            "quickstartAcceptedResult": result["quickstartAcceptedResult"],
            "checklistItems": result["checklistItems"],
            "reviewerCommands": result["reviewerCommands"],
            "evidencePaths": result["evidencePaths"],
            "expectedOutputs": result["expectedOutputs"],
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
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Reviewer checklist scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated reviewer checklist report JSON.")
    parser.add_argument("--checklist-output-dir", type=Path, help="Explicit local directory for the accepted checklist manifest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.checklist_output_dir:
        output_dir = args.checklist_output_dir if args.checklist_output_dir.is_absolute() else ROOT / args.checklist_output_dir
        positive = next(result for result in report["results"] if result["id"] == "reviewer-checklist-accept-pass")
        report["localChecklistWrite"] = write_checklist(positive, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
