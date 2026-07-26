#!/usr/bin/env python3
"""Build deterministic bounded beta runtime service-wrapper activation smoke output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-wrapper-activation-smoke-scenarios.json"
PINNED_295_MERGE_COMMIT = "b759ae7ef0742a65baa9a8e18e7fe88d920ee16c"
PINNED_295_FIXTURE_PATH = "tests/fixtures/beta-runtime-service-activation-live-run-gate.json"
PINNED_295_FIXTURE_SHA256 = "49d21d28a4b7575ab3263983a97539082dd6812be30084ec2ac834f727d96d61"
PINNED_295_REPORT_PATH = "tests/BETA-RUNTIME-SERVICE-ACTIVATION-LIVE-RUN-GATE-REPORT.md"
PINNED_295_REPORT_SHA256 = "a00c1bfbefec944d974dc0b7d6448a0d34efb77c33e2efdd903ea83a7c3965a2"
PINNED_293_FIXTURE_PATH = "tests/fixtures/beta-runtime-service-activation-evidence-gate.json"
PINNED_293_FIXTURE_SHA256 = "f757357a79cf253ea238e6e0fda286912da0bb02da3a362e7bb253607a133524"
PINNED_291_APPROVAL_PACKET_SHA256 = "e86cc4fbb030521c969e7bb833a96c14ad1baf2bf9242e516065b3666dccd452"
REQUIRED_RUN_ID = "reddiagent-beta-0-runtime-service-wrapper-activation-smoke"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_NEXT_STEP_CUE = (
    "Hold after this local service-wrapper activation smoke; a separate bounded operator run is still "
    "required before any external service mutation, provider access, devnet run, or mainnet action."
)
REQUIRED_OPERATOR_APPROVALS = (
    "runtime_owner_approval",
    "rollback_owner_approval",
    "security_reviewer_approval",
    "separate_live_activation_run_approval",
)
UNSAFE_FLAG_FIELDS = (
    "actualServiceMutation",
    "liveRuntimeActivation",
    "serviceStarted",
    "externalProcessStarted",
    "hostProcessMutated",
    "networkAccess",
    "credentialAccess",
    "providerApiAccess",
    "hostedFetch",
    "liveMcpInvocation",
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
    "serviceStartRequested",
    "externalProcessStartRequested",
    "hostMutationRequested",
    "dockerStartRequested",
    "surfpoolStartRequested",
    "coolifyDeploymentRequested",
    "providerApiAccessRequested",
    "credentialAccessRequested",
    "hostedFetchRequested",
    "liveMcpRequested",
    "walletRequested",
    "paymentRequested",
    "facilitatorRequested",
    "settlementRequested",
    "deploymentRequested",
    "packagePublishingRequested",
    "archivePublishingRequested",
    "packageArchivePublishRequested",
    "publicPublishingRequested",
    "productionClaimRequested",
    "devnetRequested",
    "mainnetRequested",
    "mainnetEnabled",
    "activationCompleted",
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner as smoke  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_activation_live_run_gate as live_gate  # noqa: E402


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


def boundary_values() -> dict[str, bool]:
    return {
        "deterministicLocalOnly": True,
        "ephemeralLocalWrapperStateOnly": True,
        "leastPrivilege": True,
        "reversible": True,
        "audited": True,
        "bounded": True,
        "actualServiceMutation": False,
        "liveRuntimeActivation": False,
        "serviceStarted": False,
        "externalProcessStarted": False,
        "hostProcessMutated": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
        "hostedFetch": False,
        "liveMcpInvocation": False,
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
    }


def false_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in boundary_values().items():
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def prior_295_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in live_gate.boundary_values().items():
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def accepted_295_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "bounded-live-run-hold-pass":
            return result
    return None


def prior_295_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-runtime-service-activation-live-run-gate":
        findings.append(finding("prior295Fixture.mode", "Pinned #295 fixture must be the activation live-run gate."))
    if doc.get("issue") != 295 or doc.get("parentEpic") != 220:
        findings.append(finding("prior295Fixture.issue", "Pinned #295 fixture must belong to issue #295 and parent #220."))
    if doc.get("follows") != [293, 291, 289, 287, 285]:
        findings.append(finding("prior295Fixture.follows", "Pinned #295 fixture must preserve #293/#291 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior295Fixture.status", "Pinned #295 fixture must pass."))
    findings.extend(prior_295_boundary_findings(doc.get("boundaries", {}), "prior295Fixture.boundaries"))
    result = accepted_295_result(doc)
    if not result:
        findings.append(finding("prior295Fixture.results", "Pinned #295 fixture must include bounded-live-run-hold-pass."))
        return findings
    if result.get("status") != "pass" or result.get("verdict") != "hold":
        findings.append(finding("prior295Fixture.results.verdict", "Accepted #295 result must pass with hold verdict."))
    evidence = result.get("runEvidence", {})
    if not isinstance(evidence, dict):
        findings.append(finding("prior295Fixture.results.runEvidence", "Accepted #295 run evidence must be an object."))
        return findings
    prior293 = evidence.get("prior293Evidence", {})
    fixture = prior293.get("fixture", {})
    if fixture.get("path") != PINNED_293_FIXTURE_PATH or fixture.get("sha256") != PINNED_293_FIXTURE_SHA256 or fixture.get("hashMatches") is not True:
        findings.append(finding("prior295Fixture.results.prior293Evidence.fixture", "Accepted #295 evidence must consume pinned #293 evidence by path and sha256."))
    approval = prior293.get("approvalPacketFixture", {})
    if approval.get("sha256") != PINNED_291_APPROVAL_PACKET_SHA256:
        findings.append(finding("prior295Fixture.results.prior293Evidence.approvalPacketFixture", "Accepted #295 evidence must preserve the pinned #291 approval-packet hash."))
    selected = prior293.get("selectedRuntimePath", {})
    scope = evidence.get("activationScope", {})
    if selected.get("adlPath") != gate.REQUIRED_ADL_PATH or scope.get("adlPath") != gate.REQUIRED_ADL_PATH:
        findings.append(finding("prior295Fixture.results.activationScope", "Accepted #295 may select only examples/simple-agent.yaml."))
    approvals = evidence.get("currentOperatorApprovalState", {})
    for name in REQUIRED_OPERATOR_APPROVALS:
        if approvals.get(name) is not True:
            findings.append(finding(f"prior295Fixture.results.currentOperatorApprovalState.{name}", f"{name} must be recorded true."))
    trace = evidence.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("prior295Fixture.results.traceEvalSummary", "Accepted #295 trace/eval summary must pass without tool execution."))
    decision = evidence.get("operatorDecision", {})
    if decision.get("decision") != "hold" or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("prior295Fixture.results.operatorDecision", "Accepted #295 must hold before external mutation."))
    rollback = evidence.get("rollbackDisableVerification", {})
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False or not rollback.get("disableCommand") or not rollback.get("rollbackCommand"):
        findings.append(finding("prior295Fixture.results.rollbackDisableVerification", "Accepted #295 must preserve rollback/disable proof."))
    if evidence.get("riskVerdict") != "hold-before-actual-service-activation":
        findings.append(finding("prior295Fixture.results.riskVerdict", "Accepted #295 risk verdict must hold before actual activation."))
    findings.extend(prior_295_boundary_findings(evidence.get("boundaries", {}), "prior295Fixture.results.boundaries"))
    findings.extend(smoke.sensitive_payload_findings(evidence, "prior295Fixture.results.runEvidence"))
    findings.extend(smoke.unsafe_claim_findings(evidence, "prior295Fixture.results.runEvidence"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("runEvidenceId") != REQUIRED_RUN_ID:
        findings.append(finding("runEvidenceId", f"Run evidence id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_295_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_295_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_295_FIXTURE_PATH or hashes.get(PINNED_295_FIXTURE_PATH) != PINNED_295_FIXTURE_SHA256:
        findings.append(finding("prior295Fixture.expectedSha256", "Prior #295 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_295_REPORT_PATH or hashes.get(PINNED_295_REPORT_PATH) != PINNED_295_REPORT_SHA256:
        findings.append(finding("prior295Report.expectedSha256", "Prior #295 report path and sha256 must be pinned from the merge commit."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this local service-wrapper smoke."))
    approvals = scenario.get("currentOperatorApprovalState", {})
    for name in REQUIRED_OPERATOR_APPROVALS:
        if not isinstance(approvals, dict) or approvals.get(name) is not True:
            findings.append(finding(f"currentOperatorApprovalState.{name}", f"{name} must be recorded true for this bounded smoke."))
    scope = scenario.get("activationScope", {})
    if scope.get("adlPath") != gate.REQUIRED_ADL_PATH or scope.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX or scope.get("serviceWrapper") != "local-ephemeral-json-state":
        findings.append(finding("activationScope", "Activation scope must be the simple-agent local ephemeral service-wrapper state."))
    state = scenario.get("serviceWrapperState", {})
    if state.get("storage") != "ephemeral-local-json" or state.get("before", {}).get("enabled") is not False:
        findings.append(finding("serviceWrapperState.before", "Service-wrapper state must start disabled in ephemeral local JSON."))
    if state.get("afterEnable", {}).get("enabled") is not True or state.get("afterEnable", {}).get("externalProcessPid") is not None:
        findings.append(finding("serviceWrapperState.afterEnable", "Enable transition may only flip local wrapper state and must not start a process."))
    if state.get("afterEnable", {}).get("mutationScope") != "local-state-only":
        findings.append(finding("serviceWrapperState.afterEnable.mutationScope", "Enable transition mutation scope must remain local-state-only."))
    if state.get("afterDisable", {}).get("enabled") is not False or state.get("afterRollback", {}).get("enabled") is not False:
        findings.append(finding("serviceWrapperState.afterDisable", "Disable and rollback transitions must leave the wrapper disabled."))
    if state.get("afterDisable", {}).get("externalProcessPid") is not None:
        findings.append(finding("serviceWrapperState.afterDisable.externalProcessPid", "Disable transition must not preserve an external process PID."))
    if state.get("afterRollback", {}).get("externalProcessPid") is not None:
        findings.append(finding("serviceWrapperState.afterRollback.externalProcessPid", "Rollback transition must not preserve an external process PID."))
    audit = scenario.get("auditTrail", [])
    if not isinstance(audit, list) or audit != ["state-before-disabled", "enable-local-wrapper-state", "disable-local-wrapper-state", "rollback-local-wrapper-state"]:
        findings.append(finding("auditTrail", "Audit trail must record before/enable/disable/rollback state transitions exactly."))
    transcript = scenario.get("boundedTranscript", {})
    if transcript.get("mode") != "local-service-wrapper-state-smoke" or transcript.get("exitCode") != 0:
        findings.append(finding("boundedTranscript", "Bounded transcript must be the local service-wrapper state smoke and exit 0."))
    trace = scenario.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("traceEvalSummary", "Trace/eval summary must pass without tool execution."))
    rollback = scenario.get("rollbackDisableVerification", {})
    if rollback.get("disableCommand") != "service-wrapper:disable --target simple-agent --state ephemeral --dry-run":
        findings.append(finding("rollbackDisableVerification.disableCommand", "Disable verification must use the pinned service-wrapper dry-run command."))
    if rollback.get("rollbackCommand") != "service-wrapper:rollback --target simple-agent --state ephemeral --dry-run":
        findings.append(finding("rollbackDisableVerification.rollbackCommand", "Rollback verification must use the pinned service-wrapper dry-run command."))
    if rollback.get("wrapperEnabledAfterRollback") is not False or rollback.get("externalProcessStarted") is not False:
        findings.append(finding("rollbackDisableVerification.wrapperEnabledAfterRollback", "Rollback must leave wrapper disabled and prove no external process start."))
    decision = scenario.get("operatorDecision", {})
    if decision.get("decision") not in {"hold", "rollback"} or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("operatorDecision", "Decision must be hold or rollback with no live action authorization."))
    if scenario.get("riskVerdict") != "hold-before-external-service-mutation":
        findings.append(finding("riskVerdict", "Risk verdict must hold before external service mutation."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must stop before external service mutation and mainnet."))
    findings.extend(smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(smoke.unsafe_claim_findings(scenario, "scenario"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    return findings


def build_run_evidence(
    scenario: dict[str, Any],
    prior_doc: dict[str, Any],
    fixture_binding: dict[str, Any],
    report_binding: dict[str, Any],
    commit: str,
) -> dict[str, Any]:
    prior = accepted_295_result(prior_doc) or {}
    prior_evidence = prior.get("runEvidence", {}) if isinstance(prior.get("runEvidence", {}), dict) else {}
    return {
        "runEvidenceId": scenario.get("runEvidenceId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior295Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": prior.get("id"),
            "acceptedVerdict": prior.get("verdict"),
            "prior293Fixture": prior_evidence.get("prior293Evidence", {}).get("fixture", {}),
            "approvalPacketFixture": prior_evidence.get("prior293Evidence", {}).get("approvalPacketFixture", {}),
            "selectedRuntimePath": prior_evidence.get("activationScope", {}),
            "priorRiskVerdict": prior_evidence.get("riskVerdict"),
        },
        "currentOperatorApprovalState": scenario.get("currentOperatorApprovalState", {}),
        "activationScope": scenario.get("activationScope", {}),
        "serviceWrapperState": scenario.get("serviceWrapperState", {}),
        "boundedTranscript": scenario.get("boundedTranscript", {}),
        "traceEvalSummary": scenario.get("traceEvalSummary", {}),
        "operatorDecision": scenario.get("operatorDecision", {}),
        "rollbackDisableVerification": scenario.get("rollbackDisableVerification", {}),
        "auditTrail": scenario.get("auditTrail", []),
        "riskVerdict": scenario.get("riskVerdict"),
        "nextStepCue": scenario.get("nextStepCue"),
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_295_FIXTURE_PATH, hashes.get(PINNED_295_FIXTURE_PATH, ""), "prior295Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_295_REPORT_PATH, hashes.get(PINNED_295_REPORT_PATH, ""), "prior295Report", findings)
    prior_doc: dict[str, Any] = {}
    prior_path = ROOT / PINNED_295_FIXTURE_PATH
    if prior_path.exists():
        try:
            prior_doc = load_json(prior_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding("prior295Fixture.json", f"Prior #295 evidence must be JSON: {exc}"))
    findings.extend(prior_295_findings(prior_doc))
    status = "pass" if not findings else "fail"
    verdict = scenario.get("requestedVerdict", "hold") if status == "pass" else scenario.get("expectedVerdict", "hold")
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedVerdict"],
        "findings": findings,
        "sourceCommit": commit,
        "runEvidence": build_run_evidence(scenario, prior_doc, fixture_binding, report_binding, commit),
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
        "mode": "beta-runtime-service-wrapper-activation-smoke",
        "issue": 297,
        "parentEpic": 220,
        "follows": [295, 293, 291, 289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "holdVerdicts": sum(1 for result in results if result["verdict"] == "hold"),
            "rollbackVerdicts": sum(1 for result in results if result["verdict"] == "rollback"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": boundary_values(),
        "mainnetStatement": "This service-wrapper smoke does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Service-wrapper smoke scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated service-wrapper smoke JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(load_json(Path(args.scenarios)))
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
