#!/usr/bin/env python3
"""Build deterministic local beta runtime activation canary evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-activation-canary-runner-scenarios.json"
PINNED_ACTIVATION_PATH = "tests/fixtures/beta-runtime-activation-evidence-gate.json"
REQUIRED_CANARY_ID = "reddiagent-beta-0-local-runtime-activation-canary"
REQUIRED_ACTIVATION_ID = "reddiagent-beta-0-local-runtime-activation-evidence"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner as smoke  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


UNSAFE_FLAG_FIELDS = gate.UNSAFE_FLAG_FIELDS + (
    "hostedFetchRequested",
    "packageArchivePublishRequested",
    "productionClaimRequested",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


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


def load_activation(path_text: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(finding("activationEvidenceFixture.json", f"Activation evidence must be JSON: {exc}"))
        return {}


def accepted_activation_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "runtime-activation-evidence-accept-pass":
            return result
    for result in doc.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "activate-local":
            return result
    return None


def activation_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-local-runtime-activation-evidence-gate":
        findings.append(finding("activationEvidenceFixture.mode", "Pinned #287 fixture must be the activation evidence gate."))
    if doc.get("issue") != 287 or doc.get("parentEpic") != 220:
        findings.append(finding("activationEvidenceFixture.issue", "Pinned fixture must belong to issue #287 and parent #220."))
    if doc.get("status") != "pass":
        findings.append(finding("activationEvidenceFixture.status", "Pinned #287 fixture must pass."))
    if doc.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("activationEvidenceFixture.releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    boundaries = doc.get("boundaries", {})
    for field in (
        "serviceStarted",
        "networkAccess",
        "credentialAccess",
        "providerApiAccess",
        "liveMcpInvocation",
        "liveRuntimeActivation",
        "dockerStarted",
        "surfpoolStarted",
        "coolifyDeployment",
        "walletAccess",
        "paymentAccess",
        "facilitatorAccess",
        "settlementAccess",
        "devnetAccess",
        "mainnetAccess",
        "deploymentPublished",
        "packagePublished",
        "archivePublished",
        "publicPublished",
        "externalSpend",
    ):
        if boundaries.get(field) is not False:
            findings.append(finding(f"activationEvidenceFixture.boundaries.{field}", f"{field} must remain false."))
    accepted = accepted_activation_result(doc)
    if not accepted:
        findings.append(finding("activationEvidenceFixture.results", "Pinned #287 fixture must include accepted activation evidence."))
        return findings
    if accepted.get("activationEvidenceId") != REQUIRED_ACTIVATION_ID:
        findings.append(finding("activationEvidenceFixture.results.activationEvidenceId", f"Activation id must be `{REQUIRED_ACTIVATION_ID}`."))
    if accepted.get("status") != "pass" or accepted.get("verdict") != "activate-local":
        findings.append(finding("activationEvidenceFixture.results.verdict", "Accepted #287 result must pass with activate-local verdict."))
    selected = accepted.get("selectedRuntimePath", {})
    if selected.get("adlPath") != gate.REQUIRED_ADL_PATH or selected.get("runtimeScenarioId") != "simple-agent-dry-run":
        findings.append(finding("activationEvidenceFixture.results.selectedRuntimePath", "Canary may select only the reviewed simple local ADL runtime path."))
    transcript = accepted.get("localCommandTranscript", {})
    if transcript.get("command") != gate.LOCAL_COMMAND_PREFIX or transcript.get("exitCode") != 0:
        findings.append(finding("activationEvidenceFixture.results.localCommandTranscript", "Accepted #287 transcript must be the simple local ADL command with exit code 0."))
    if transcript.get("traceEvents") != gate.REQUIRED_TRACE_EVENTS:
        findings.append(finding("activationEvidenceFixture.results.localCommandTranscript.traceEvents", "Accepted #287 trace sequence must match reviewed events."))
    summary = accepted.get("traceEvalSummary", {})
    if summary.get("completionStatus") != "pass" or summary.get("requiredGateStatus") != "pass" or summary.get("toolExecution") is not None:
        findings.append(finding("activationEvidenceFixture.results.traceEvalSummary", "Accepted #287 trace/eval summary must pass without tool execution."))
    if accepted.get("operatorControlState", {}).get("runtimeEnabled") is not False:
        findings.append(finding("activationEvidenceFixture.results.operatorControlState.runtimeEnabled", "Accepted #287 evidence must leave runtime disabled."))
    if accepted.get("rollbackDisableProof", {}).get("liveRuntimeEnabledAfterRollback") is not False:
        findings.append(finding("activationEvidenceFixture.results.rollbackDisableProof", "Accepted #287 rollback proof must leave live runtime disabled."))
    findings.extend(smoke.sensitive_payload_findings(accepted, "activationEvidenceFixture.results"))
    findings.extend(smoke.unsafe_claim_findings(accepted, "activationEvidenceFixture.results"))
    findings.extend(gate.command_findings(accepted.get("localCommands", []), "activationEvidenceFixture.results.localCommands"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("canaryId") != REQUIRED_CANARY_ID:
        findings.append(finding("canaryId", f"Canary id must be `{REQUIRED_CANARY_ID}`."))
    if scenario.get("activationEvidenceId") != REQUIRED_ACTIVATION_ID:
        findings.append(finding("activationEvidenceId", f"Activation evidence id must be `{REQUIRED_ACTIVATION_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this local canary runner."))
    findings.extend(smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(smoke.unsafe_claim_findings(scenario.get("nextStepCue", ""), "nextStepCue"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    command_text = "\n".join(command for command in scenario.get("localCommands", []) if isinstance(command, str))
    if gate.LOCAL_COMMAND_PREFIX not in command_text:
        findings.append(finding("localCommands", f"Local canary command `{gate.LOCAL_COMMAND_PREFIX}` is missing."))
    for command in scenario.get("localCommands", []):
        if isinstance(command, str) and "--execute-tools" in command:
            findings.append(finding("localCommands", "Canary runner must select the no-tool simple local runtime path."))
    before = scenario.get("operatorControlStateBefore", {})
    after = scenario.get("operatorControlStateAfter", {})
    for label, control in (("operatorControlStateBefore", before), ("operatorControlStateAfter", after)):
        if not isinstance(control, dict):
            findings.append(finding(label, "Operator control state must be an object."))
            continue
        if control.get("runtimeEnabled") is not False:
            findings.append(finding(f"{label}.runtimeEnabled", "Runtime must remain disabled before and after the canary."))
        if control.get("disableSwitchAvailable") is not True:
            findings.append(finding(f"{label}.disableSwitchAvailable", "Disable control must remain available."))
    rollback = scenario.get("rollbackDisableDryRunProof", {})
    if not isinstance(rollback, dict):
        findings.append(finding("rollbackDisableDryRunProof", "Rollback/disable dry-run proof must be an object."))
    else:
        if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableDryRunProof.disableCommand", "Disable command must be the pinned local dry-run proof."))
        if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
            findings.append(finding("rollbackDisableDryRunProof.rollbackCommand", "Rollback command must be the pinned local dry-run proof."))
        if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
            findings.append(finding("rollbackDisableDryRunProof.liveRuntimeEnabledAfterRollback", "Rollback proof must leave live runtime disabled."))
    return findings


def verdict_for(status: str, requested: str | None) -> str:
    if status == "pass":
        return requested if requested in {"accept-canary", "hold", "reject"} else "accept-canary"
    if requested == "reject":
        return "reject"
    return "hold"


def next_step_for(verdict: str) -> str:
    if verdict == "accept-canary":
        return "Accept this local canary evidence for reviewer/operator handoff only; true live runtime/service activation, deployment, devnet, payments, package/archive publishing, and mainnet remain separate gates."
    if verdict == "reject":
        return "Reject this canary evidence and regenerate accepted #287 activation evidence before any runtime activation handoff."
    return "Hold this canary evidence until stale, missing, unsafe, or overclaiming local inputs are fixed."


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    activation_path = scenario.get("activationEvidenceFixturePath", PINNED_ACTIVATION_PATH)
    activation_binding = gate.artifact_binding(activation_path, hashes.get(activation_path, ""), "activationEvidenceFixture", findings)
    activation = load_activation(activation_path, findings)
    findings.extend(activation_findings(activation))
    accepted = accepted_activation_result(activation) or {}
    canary_transcript = gate.run_selected_runtime()
    if canary_transcript["exitCode"] != 0:
        findings.append(finding("canaryCommandTranscript.exitCode", "Selected local canary command must exit 0."))
    if canary_transcript["traceEvents"] != gate.REQUIRED_TRACE_EVENTS:
        findings.append(finding("canaryCommandTranscript.traceEvents", "Canary transcript must match reviewed trace events."))
    if canary_transcript["completion"].get("status") != "pass":
        findings.append(finding("canaryCommandTranscript.completion", "Canary transcript completion must pass."))
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
        "canaryId": scenario.get("canaryId"),
        "activationEvidenceId": scenario.get("activationEvidenceId"),
        "releaseId": scenario.get("releaseId"),
        "releaseCandidateId": scenario.get("releaseCandidateId"),
        "activationEvidence": {
            "fixture": activation_binding,
            "acceptedResultId": accepted.get("id"),
            "acceptedVerdict": accepted.get("verdict"),
            "acceptedActivationEvidenceSha256": gate.sha256_text(dump_json(accepted)) if accepted else None,
            "acceptedSourceCommit": accepted.get("sourceCommit"),
            "acceptedSourceSmoke": accepted.get("sourceSmoke"),
            "acceptedRuntimePath": accepted.get("selectedRuntimePath"),
        },
        "selectedRuntimePath": {
            "adlPath": gate.REQUIRED_ADL_PATH,
            "reviewedCommand": gate.LOCAL_COMMAND_PREFIX,
            "sourceAcceptedResultId": accepted.get("id"),
        },
        "canaryCommandTranscript": canary_transcript,
        "traceEvalSummary": canary_transcript["evalSummary"],
        "operatorControlStateBefore": scenario.get("operatorControlStateBefore", {}),
        "operatorControlStateAfter": scenario.get("operatorControlStateAfter", {}),
        "rollbackDisableDryRunProof": scenario.get("rollbackDisableDryRunProof", {}),
        "nextStepCue": next_step_for(verdict),
        "boundaries": {
            "deterministicLocalOnly": True,
            "inProcessRuntimeOnly": True,
            "canaryEvidenceWriteRequiresExplicitPath": True,
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
    actual_commit = commit or gate.source_commit()
    defaults = doc.get("defaults", {})
    results = [build_result(merge_scenario(defaults, scenario), actual_commit) for scenario in doc.get("scenarios", [])]
    mismatches = [
        finding(f"results[{index}].status", f"{result['id']} produced {result['status']}/{result['verdict']} but expected {result['expectedStatus']}/{result['expectedVerdict']}.")
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"] or result["verdict"] != result["expectedVerdict"]
    ]
    return {
        "mode": "beta-local-runtime-activation-canary-runner",
        "issue": 289,
        "parentEpic": 220,
        "follows": [287],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "acceptCanaryVerdicts": sum(1 for result in results if result["verdict"] == "accept-canary"),
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rejectVerdicts": sum(1 for result in results if result["verdict"] == "reject"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": {
            "deterministicLocalOnly": True,
            "inProcessRuntimeOnly": True,
            "canaryEvidenceWriteRequiresExplicitPath": True,
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
        "mainnetStatement": "This local canary runner does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def write_canary_evidence(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{result['canaryId']}.json"
    payload = dump_json(
        {
            "canaryId": result["canaryId"],
            "activationEvidenceId": result["activationEvidenceId"],
            "releaseId": result["releaseId"],
            "releaseCandidateId": result["releaseCandidateId"],
            "verdict": result["verdict"],
            "activationEvidence": result["activationEvidence"],
            "selectedRuntimePath": result["selectedRuntimePath"],
            "canaryCommandTranscript": result["canaryCommandTranscript"],
            "traceEvalSummary": result["traceEvalSummary"],
            "operatorControlStateBefore": result["operatorControlStateBefore"],
            "operatorControlStateAfter": result["operatorControlStateAfter"],
            "rollbackDisableDryRunProof": result["rollbackDisableDryRunProof"],
            "nextStepCue": result["nextStepCue"],
            "boundaries": result["boundaries"],
            "sourceCommit": result["sourceCommit"],
        }
    )
    manifest_path.write_text(payload)
    return {"manifestPath": str(manifest_path), "manifestSha256": gate.sha256_text(payload)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Canary scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated canary report JSON.")
    parser.add_argument("--canary-output-dir", type=Path, help="Explicit local directory for the accepted canary evidence artifact.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    if args.canary_output_dir:
        output_dir = args.canary_output_dir if args.canary_output_dir.is_absolute() else ROOT / args.canary_output_dir
        positive = next(result for result in report["results"] if result["id"] == "runtime-activation-canary-accept-pass")
        report["localCanaryEvidenceWrite"] = write_canary_evidence(positive, output_dir)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
