#!/usr/bin/env python3
"""Build deterministic local beta runtime activation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-activation-evidence-gate-scenarios.json"
PINNED_E2E_PATH = "tests/fixtures/beta-e2e-acceptance-smoke.json"
PINNED_RUNTIME_PATH = "tests/fixtures/local-executable-runtime-prototype.json"
REQUIRED_ACTIVATION_ID = "reddiagent-beta-0-local-runtime-activation-evidence"
REQUIRED_SMOKE_ID = "reddiagent-beta-0-local-e2e-acceptance-smoke"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_ADL_PATH = "examples/simple-agent.yaml"
REQUIRED_RUNTIME_MODE = "local-executable-adl-runtime-prototype"
REQUIRED_E2E_MODE = "beta-local-e2e-acceptance-smoke-runner"
REQUIRED_TRACE_EVENTS = [
    "session.started",
    "model.resolved",
    "tools.registered",
    "policies.loaded",
    "evals.loaded",
    "task.dry_run_completed",
]
LOCAL_COMMAND_PREFIX = f"python scripts/run_local_agent.py {REQUIRED_ADL_PATH}"
UNSAFE_FLAG_FIELDS = (
    "liveRuntimeRequested",
    "liveNetworkEnabled",
    "serviceStartRequested",
    "dockerStartRequested",
    "surfpoolStartRequested",
    "coolifyDeploymentRequested",
    "providerApiAccessRequested",
    "credentialAccessRequested",
    "liveMcpRequested",
    "walletRequested",
    "paymentRequested",
    "facilitatorRequested",
    "settlementRequested",
    "deploymentRequested",
    "packagePublishingRequested",
    "archivePublishingRequested",
    "publicPublishingRequested",
    "devnetRequested",
    "mainnetRequested",
    "mainnetEnabled",
)
OPERATOR_CONTROL_FLAGS = (
    "manualApprovalRecorded",
    "disableSwitchAvailable",
    "rollbackCommandDryRun",
    "activationCanaryLocalOnly",
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
HOSTED_FETCH_COMMANDS = {"curl", "wget"}
UNSAFE_PACKAGE_PUBLISH_COMMANDS = {
    ("gh", "release", "upload"),
    ("npm", "publish"),
    ("pnpm", "publish"),
    ("yarn", "publish"),
    ("vercel", "deploy"),
    ("kubectl", "apply"),
    ("openclaw", "gateway"),
}

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner as smoke  # noqa: E402


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


def expected_hash_map(scenario: dict[str, Any]) -> dict[str, str]:
    return {
        item["path"]: item.get("sha256", "")
        for item in scenario.get("expectedArtifactHashes", [])
        if isinstance(item, dict) and item.get("path")
    }


def artifact_binding(path_text: str, expected_hash: str, label: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    actual_hash = digest(path) if path.exists() else None
    if not path.exists():
        findings.append(finding(f"{label}.exists", f"Artifact `{path_text}` is missing."))
    elif not expected_hash:
        findings.append(finding(f"{label}.expectedSha256", f"Expected sha256 pin is required for `{path_text}`."))
    elif actual_hash != expected_hash:
        findings.append(finding(f"{label}.sha256", f"Artifact `{path_text}` does not match its expected sha256 pin."))
    return {
        "path": path_text,
        "sha256": actual_hash,
        "expectedSha256": expected_hash,
        "hashMatches": bool(actual_hash and expected_hash and actual_hash == expected_hash),
    }


def load_artifact(path_text: str, label: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding(f"{label}.json", f"Artifact must be JSON: {exc}"))
        return {}


def accepted_smoke_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "e2e-acceptance-smoke-accept-pass":
            return result
    for result in doc.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "accept":
            return result
    return None


def selected_runtime_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("scenarios", []):
        if result.get("adl") == REQUIRED_ADL_PATH and result.get("id") == "simple-agent-dry-run":
            return result
    return None


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("activationEvidenceId") != REQUIRED_ACTIVATION_ID:
        findings.append(finding("activationEvidenceId", f"Activation evidence id must be `{REQUIRED_ACTIVATION_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("selectedAdlPath") != REQUIRED_ADL_PATH:
        findings.append(finding("selectedAdlPath", f"Selected ADL path must be `{REQUIRED_ADL_PATH}`."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this local evidence gate."))
    findings.extend(smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(smoke.unsafe_claim_findings(scenario.get("nextStepCue", ""), "nextStepCue"))
    findings.extend(smoke.unsafe_claim_findings(scenario.get("operatorControlState", {}), "operatorControlState"))
    findings.extend(command_findings(scenario.get("localCommands", []), "localCommands"))
    command_text = "\n".join(command for command in scenario.get("localCommands", []) if isinstance(command, str))
    if LOCAL_COMMAND_PREFIX not in command_text:
        findings.append(finding("localCommands", f"Local runtime command `{LOCAL_COMMAND_PREFIX}` is missing."))
    for command in scenario.get("localCommands", []):
        if isinstance(command, str) and "--execute-tools" in command:
            findings.append(finding("localCommands", "Activation evidence gate must select the no-tool simple local runtime path."))
    control = scenario.get("operatorControlState", {})
    if not isinstance(control, dict):
        findings.append(finding("operatorControlState", "Operator control state must be an object."))
    else:
        for field in OPERATOR_CONTROL_FLAGS:
            if control.get(field) is not True:
                findings.append(finding(f"operatorControlState.{field}", f"{field} must be true."))
        if control.get("runtimeEnabled") is not False:
            findings.append(finding("operatorControlState.runtimeEnabled", "Runtime enabled state must remain false."))
    rollback = scenario.get("rollbackDisableProof", {})
    if not isinstance(rollback, dict):
        findings.append(finding("rollbackDisableProof", "Rollback/disable proof must be an object."))
    else:
        if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableProof.disableCommand", "Disable command must be the pinned local dry-run proof."))
        if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableProof.rollbackCommand", "Rollback command must be the pinned local dry-run proof."))
        if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
            findings.append(finding("rollbackDisableProof.liveRuntimeEnabledAfterRollback", "Rollback proof must leave live runtime disabled."))
    return findings


def command_findings(commands: Any, field: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(commands, list):
        return [finding(field, "Commands must be a list.")]
    for index, command in enumerate(commands):
        if not isinstance(command, str) or not command.strip():
            findings.append(finding(f"{field}[{index}]", "Command must be a non-empty string."))
            continue
        lowered = command.lower()
        for marker in UNSAFE_COMMAND_MARKERS:
            if marker in lowered:
                findings.append(finding(f"{field}[{index}]", f"Command must not include `{marker}`."))
        try:
            tokens = [token.lower() for token in smoke.shlex.split(command)]
        except ValueError:
            tokens = lowered.split()
        if not tokens:
            continue
        if tokens[0] == "docker" and any(token in UNSAFE_DOCKER_SUBCOMMANDS for token in tokens[1:]):
            findings.append(finding(f"{field}[{index}]", "Command must not pull, start, run, or compose Docker containers."))
        if tokens[0] == "docker-compose" and "up" in tokens[1:]:
            findings.append(finding(f"{field}[{index}]", "Command must not start Docker Compose services."))
        if tokens[0] in HOSTED_FETCH_COMMANDS and any(token.startswith(("http://", "https://")) for token in tokens[1:]):
            findings.append(finding(f"{field}[{index}]", "Command must not fetch hosted content."))
        for unsafe in UNSAFE_PACKAGE_PUBLISH_COMMANDS:
            if len(tokens) >= len(unsafe) and tuple(tokens[: len(unsafe)]) == unsafe:
                findings.append(finding(f"{field}[{index}]", f"Command must not run `{' '.join(unsafe)}`."))
    return findings


def e2e_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != REQUIRED_E2E_MODE:
        findings.append(finding("e2eSmokeFixture.mode", "Pinned #285 fixture must be the beta e2e smoke runner."))
    if doc.get("issue") != 285 or doc.get("parentEpic") != 220:
        findings.append(finding("e2eSmokeFixture.issue", "Pinned #285 fixture must belong to issue #285 and parent #220."))
    if doc.get("status") != "pass":
        findings.append(finding("e2eSmokeFixture.status", "Pinned #285 fixture must pass."))
    if doc.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("e2eSmokeFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    findings.extend(smoke.boundary_findings(doc, "e2eSmokeFixture"))
    accepted = accepted_smoke_result(doc)
    if not accepted:
        findings.append(finding("e2eSmokeFixture.results", "Pinned #285 fixture must include an accepted smoke result."))
        return findings
    if accepted.get("smokeId") != REQUIRED_SMOKE_ID:
        findings.append(finding("e2eSmokeFixture.results.smokeId", f"Accepted smoke id must be `{REQUIRED_SMOKE_ID}`."))
    if accepted.get("verdict") != "accept" or accepted.get("status") != "pass":
        findings.append(finding("e2eSmokeFixture.results.verdict", "Accepted #285 smoke result must pass with accept verdict."))
    findings.extend(smoke.sensitive_payload_findings(accepted, "e2eSmokeFixture.results"))
    findings.extend(smoke.unsafe_claim_findings(accepted, "e2eSmokeFixture.results"))
    findings.extend(command_findings(accepted.get("localCommands", []), "e2eSmokeFixture.results.localCommands"))
    return findings


def runtime_findings(doc: dict[str, Any], selected_adl_path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != REQUIRED_RUNTIME_MODE:
        findings.append(finding("runtimeFixture.mode", "Runtime evidence must be the reviewed local executable runtime prototype."))
    if doc.get("issue") != 224 or doc.get("status") != "pass":
        findings.append(finding("runtimeFixture.status", "Runtime fixture must be passing issue #224 evidence."))
    boundaries = doc.get("boundaries", {})
    if boundaries.get("localRuntimeExecutionAllowed") is not True or boundaries.get("deterministicLocalFixturesOnly") is not True:
        findings.append(finding("runtimeFixture.boundaries", "Runtime fixture must be local and deterministic."))
    for field in ("networkAccess", "paymentAccess", "credentialAccess", "mcpInvocation", "mainnetAccess", "externalExecutionAllowed"):
        if boundaries.get(field) is not False:
            findings.append(finding(f"runtimeFixture.boundaries.{field}", f"{field} must remain false."))
    result = selected_runtime_result(doc)
    if not result:
        findings.append(finding("runtimeFixture.scenarios", f"Runtime fixture must include `{selected_adl_path}`."))
        return findings
    if result.get("adl") != selected_adl_path or result.get("status") != "pass" or result.get("exitCode") != 0:
        findings.append(finding("runtimeFixture.scenarios.simple-agent-dry-run", "Selected runtime path must pass with exit code 0."))
    if result.get("traceEvents") != REQUIRED_TRACE_EVENTS:
        findings.append(finding("runtimeFixture.scenarios.traceEvents", "Selected runtime path trace sequence must match the reviewed dry-run path."))
    completion = result.get("completion") or {}
    if completion.get("status") != "pass" or completion.get("requiredGateStatus") != "pass":
        findings.append(finding("runtimeFixture.scenarios.completion", "Selected runtime path eval gates must pass."))
    if result.get("toolExecution") is not None:
        findings.append(finding("runtimeFixture.scenarios.toolExecution", "Selected runtime path must not execute tools."))
    return findings


def run_selected_runtime() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "scripts/run_local_agent.py", REQUIRED_ADL_PATH],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        stdout_json = json.loads(proc.stdout)
    except json.JSONDecodeError:
        stdout_json = {}
    trace_events = [event.get("event") for event in stdout_json.get("trace", [])]
    completion = stdout_json.get("completion") or {}
    return {
        "command": LOCAL_COMMAND_PREFIX,
        "exitCode": proc.returncode,
        "stdoutSha256": sha256_text(proc.stdout),
        "stderrSha256": sha256_text(proc.stderr),
        "traceEvents": trace_events,
        "completion": completion,
        "evalSummary": {
            "completionStatus": completion.get("status"),
            "requiredGateStatus": completion.get("requiredGateStatus"),
            "traceEventCount": len(trace_events),
            "toolExecution": None,
        },
    }


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"activate-local", "hold", "reject"} else "activate-local"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "activate-local":
        return "Accept this local in-process activation evidence only; true live runtime/service activation, deployment, devnet, payments, and mainnet remain separate gates."
    if verdict == "reject":
        return "Reject this activation evidence and regenerate #285/local runtime fixtures before any runtime activation step."
    return "Hold this activation evidence until stale, missing, unsafe, or overclaiming local inputs are fixed."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    e2e_path = scenario.get("e2eSmokeFixturePath", PINNED_E2E_PATH)
    runtime_path = scenario.get("runtimeFixturePath", PINNED_RUNTIME_PATH)
    e2e_binding = artifact_binding(e2e_path, hashes.get(e2e_path, ""), "e2eSmokeFixture", findings)
    runtime_binding = artifact_binding(runtime_path, hashes.get(runtime_path, ""), "runtimeFixture", findings)
    e2e = load_artifact(e2e_path, "e2eSmokeFixture", findings)
    runtime = load_artifact(runtime_path, "runtimeFixture", findings)
    findings.extend(e2e_findings(e2e))
    findings.extend(runtime_findings(runtime, scenario.get("selectedAdlPath", "")))
    runtime_transcript = run_selected_runtime()
    if runtime_transcript["exitCode"] != 0:
        findings.append(finding("runtimeTranscript.exitCode", "Selected local runtime command must exit 0."))
    if runtime_transcript["traceEvents"] != REQUIRED_TRACE_EVENTS:
        findings.append(finding("runtimeTranscript.traceEvents", "Live local transcript must match reviewed trace events."))
    if runtime_transcript["completion"].get("status") != "pass":
        findings.append(finding("runtimeTranscript.completion", "Live local transcript completion must pass."))
    status = "pass" if not findings else "fail"
    verdict = verdict_for(status, scenario.get("requestedVerdict"))
    accepted = accepted_smoke_result(e2e) or {}
    selected = selected_runtime_result(runtime) or {}
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "activationEvidenceId": scenario.get("activationEvidenceId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "sourceSmoke": {
            "fixture": e2e_binding,
            "acceptedResultId": accepted.get("id"),
            "acceptedEvidenceSha256": accepted.get("evidenceSha256"),
            "acceptedVerdict": accepted.get("verdict"),
        },
        "selectedRuntimePath": {
            "adlPath": scenario.get("selectedAdlPath"),
            "runtimeFixture": runtime_binding,
            "runtimeScenarioId": selected.get("id"),
            "reviewedCommand": selected.get("command"),
        },
        "localCommandTranscript": runtime_transcript,
        "traceEvalSummary": runtime_transcript["evalSummary"],
        "operatorControlState": scenario.get("operatorControlState", {}),
        "rollbackDisableProof": scenario.get("rollbackDisableProof", {}),
        "nextStepCue": next_step_for(verdict),
        "boundaries": {
            "deterministicLocalOnly": True,
            "inProcessRuntimeOnly": True,
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
        "mode": "beta-local-runtime-activation-evidence-gate",
        "issue": 287,
        "parentEpic": 220,
        "follows": [285, 224],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "activateLocalVerdicts": sum(1 for result in results if result["verdict"] == "activate-local"),
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rejectVerdicts": sum(1 for result in results if result["verdict"] == "reject"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": {
            "deterministicLocalOnly": True,
            "inProcessRuntimeOnly": True,
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
        "mainnetStatement": "This local activation evidence gate does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_evidence(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{result['activationEvidenceId']}.json"
    payload = dump_json(
        {
            "activationEvidenceId": result["activationEvidenceId"],
            "releaseId": result["releaseId"],
            "releaseCandidateId": result["releaseCandidateId"],
            "verdict": result["verdict"],
            "sourceSmoke": result["sourceSmoke"],
            "selectedRuntimePath": result["selectedRuntimePath"],
            "localCommandTranscript": result["localCommandTranscript"],
            "traceEvalSummary": result["traceEvalSummary"],
            "operatorControlState": result["operatorControlState"],
            "rollbackDisableProof": result["rollbackDisableProof"],
            "nextStepCue": result["nextStepCue"],
            "boundaries": result["boundaries"],
            "sourceCommit": result["sourceCommit"],
        }
    )
    manifest_path.write_text(payload)
    return {"manifestPath": str(manifest_path), "manifestSha256": sha256_text(payload)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Activation evidence scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated activation evidence report JSON.")
    parser.add_argument("--evidence-output-dir", type=Path, help="Explicit local directory for the accepted activation evidence artifact.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.evidence_output_dir:
        output_dir = args.evidence_output_dir if args.evidence_output_dir.is_absolute() else ROOT / args.evidence_output_dir
        positive = next(result for result in report["results"] if result["id"] == "runtime-activation-evidence-accept-pass")
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
