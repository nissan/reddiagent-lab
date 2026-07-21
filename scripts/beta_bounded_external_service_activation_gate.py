#!/usr/bin/env python3
"""Build deterministic bounded external-service activation gate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-bounded-external-service-activation-gate-scenarios.json"
PINNED_299_MERGE_COMMIT = "9d6f8d3a2f1a637420808ea60350f578dde0a26f"
PINNED_299_FIXTURE_PATH = "tests/fixtures/beta-runtime-service-wrapper-operator-run-package.json"
PINNED_299_FIXTURE_SHA256 = "0cea2841bd90af6d3acf51b13f4ac352cf11ef531d2768203a662e34f901c73b"
PINNED_299_REPORT_PATH = "tests/BETA-RUNTIME-SERVICE-WRAPPER-OPERATOR-RUN-PACKAGE-REPORT.md"
PINNED_299_REPORT_SHA256 = "095db81a36cd1c606003c2b9aa7dc3ddc7abe89b8528aec0ea8b9838e8749e73"
REQUIRED_RUN_ID = "reddiagent-beta-0-bounded-external-service-activation-gate"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_NEXT_STEP_CUE = (
    "Hold after this bounded external-service activation gate; create a separate Nissan-approved "
    "micro-gate before any real external service, provider, devnet, or mainnet mutation."
)
REQUIRED_TRANSCRIPT_COMMAND = (
    "python scripts/beta_bounded_external_service_activation_gate.py "
    "--output tests/fixtures/beta-bounded-external-service-activation-gate.json"
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
    "persistentMutation",
    "unboundedMutation",
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_wrapper_operator_run_package as operator_run  # noqa: E402


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
        "localTemporaryRepresentationOnly": True,
        "leastPrivilege": True,
        "reversible": True,
        "audited": True,
        "bounded": True,
        "failClosed": True,
        "actualServiceMutation": False,
        "liveRuntimeActivation": False,
        "serviceStarted": False,
        "externalProcessStarted": False,
        "hostProcessMutated": False,
        "persistentMutation": False,
        "unboundedMutation": False,
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


def accepted_299_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "service-wrapper-hold-pass":
            return result
    return None


def prior_299_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-runtime-service-wrapper-operator-run-package":
        findings.append(finding("prior299Fixture.mode", "Pinned #299 fixture must be the service-wrapper operator run package."))
    if doc.get("issue") != 299 or doc.get("parentEpic") != 220:
        findings.append(finding("prior299Fixture.issue", "Pinned #299 fixture must belong to issue #299 and parent #220."))
    if doc.get("follows") != [297, 295, 293, 291, 289, 287, 285]:
        findings.append(finding("prior299Fixture.follows", "Pinned #299 fixture must preserve #297/#295/#293/#291 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior299Fixture.status", "Pinned #299 fixture must pass."))
    findings.extend(operator_run.false_boundary_findings(doc.get("boundaries", {}), "prior299Fixture.boundaries"))
    result = accepted_299_result(doc)
    if not result:
        findings.append(finding("prior299Fixture.results", "Pinned #299 fixture must include service-wrapper-hold-pass."))
        return findings
    if result.get("status") != "pass" or result.get("verdict") != "hold":
        findings.append(finding("prior299Fixture.results.verdict", "Accepted #299 result must pass with hold verdict."))
    evidence = result.get("runEvidence", {})
    if not isinstance(evidence, dict):
        findings.append(finding("prior299Fixture.results.runEvidence", "Accepted #299 run evidence must be an object."))
        return findings
    prior297 = evidence.get("prior297Evidence", {})
    fixture297 = prior297.get("fixture", {})
    if (
        fixture297.get("path") != operator_run.PINNED_297_FIXTURE_PATH
        or fixture297.get("sha256") != operator_run.PINNED_297_FIXTURE_SHA256
        or fixture297.get("hashMatches") is not True
    ):
        findings.append(finding("prior299Fixture.results.prior297Evidence.fixture", "Accepted #299 evidence must consume pinned #297 evidence by path and sha256."))
    if prior297.get("prior295Fixture", {}).get("sha256") != operator_run.PINNED_295_FIXTURE_SHA256:
        findings.append(finding("prior299Fixture.results.prior297Evidence.prior295Fixture", "Accepted #299 evidence must preserve pinned #295 evidence."))
    if prior297.get("prior293Fixture", {}).get("sha256") != operator_run.PINNED_293_FIXTURE_SHA256:
        findings.append(finding("prior299Fixture.results.prior297Evidence.prior293Fixture", "Accepted #299 evidence must preserve pinned #293 evidence."))
    if prior297.get("approvalPacketFixture", {}).get("sha256") != operator_run.PINNED_291_APPROVAL_PACKET_SHA256:
        findings.append(finding("prior299Fixture.results.prior297Evidence.approvalPacketFixture", "Accepted #299 evidence must preserve pinned #291 approval-packet evidence."))
    scope = evidence.get("activationScope", {})
    if scope.get("adlPath") != gate.REQUIRED_ADL_PATH or scope.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX:
        findings.append(finding("prior299Fixture.results.activationScope", "Accepted #299 may select only examples/simple-agent.yaml."))
    approvals = evidence.get("currentOperatorApprovalState", {})
    for name in REQUIRED_OPERATOR_APPROVALS:
        if approvals.get(name) is not True:
            findings.append(finding(f"prior299Fixture.results.currentOperatorApprovalState.{name}", f"{name} must be recorded true."))
    trace = evidence.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("prior299Fixture.results.traceEvalSummary", "Accepted #299 trace/eval summary must pass without tool execution."))
    decision = evidence.get("operatorDecision", {})
    if decision.get("decision") != "hold" or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("prior299Fixture.results.operatorDecision", "Accepted #299 must hold before external mutation."))
    rollback = evidence.get("rollbackDisableVerification", {})
    if rollback.get("wrapperEnabledAfterRollback") is not False or rollback.get("externalProcessStarted") is not False:
        findings.append(finding("prior299Fixture.results.rollbackDisableVerification", "Accepted #299 must preserve rollback/disable proof."))
    if evidence.get("riskVerdict") != "hold-before-external-service-mutation":
        findings.append(finding("prior299Fixture.results.riskVerdict", "Accepted #299 risk verdict must hold before external mutation."))
    findings.extend(operator_run.false_boundary_findings(evidence.get("boundaries", {}), "prior299Fixture.results.boundaries"))
    findings.extend(operator_run.smoke.sensitive_payload_findings(evidence, "prior299Fixture.results.runEvidence"))
    findings.extend(operator_run.smoke.unsafe_claim_findings(evidence, "prior299Fixture.results.runEvidence"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("runEvidenceId") != REQUIRED_RUN_ID:
        findings.append(finding("runEvidenceId", f"Run evidence id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_299_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_299_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_299_FIXTURE_PATH or hashes.get(PINNED_299_FIXTURE_PATH) != PINNED_299_FIXTURE_SHA256:
        findings.append(finding("prior299Fixture.expectedSha256", "Prior #299 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_299_REPORT_PATH or hashes.get(PINNED_299_REPORT_PATH) != PINNED_299_REPORT_SHA256:
        findings.append(finding("prior299Report.expectedSha256", "Prior #299 report path and sha256 must be pinned from the merge commit."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this bounded activation gate."))
    approvals = scenario.get("currentOperatorApprovalState", {})
    for name in REQUIRED_OPERATOR_APPROVALS:
        if not isinstance(approvals, dict) or approvals.get(name) is not True:
            findings.append(finding(f"currentOperatorApprovalState.{name}", f"{name} must be recorded true for this bounded gate."))
    scope = scenario.get("activationScope", {})
    if (
        scope.get("adlPath") != gate.REQUIRED_ADL_PATH
        or scope.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX
        or scope.get("serviceWrapper") != "local-ephemeral-json-state"
        or scope.get("representedActivation") != "local-temporary-json-gate"
        or scope.get("liveMutation") is not False
        or scope.get("networkExposure") != "none"
    ):
        findings.append(finding("activationScope", "Activation scope must be a local temporary simple-agent gate with no live mutation or network exposure."))
    state = scenario.get("serviceWrapperState", {})
    if (
        state.get("storage") != "ephemeral-local-json"
        or state.get("before", {}).get("enabled") is not False
        or state.get("before", {}).get("externalProcessPid") is not None
        or state.get("afterRepresentedActivation", {}).get("enabled") is not True
        or state.get("afterRepresentedActivation", {}).get("externalProcessPid") is not None
        or state.get("afterRepresentedActivation", {}).get("mutationScope") != "local-temporary-state-only"
        or state.get("afterHold", {}).get("enabled") is not False
        or state.get("afterHold", {}).get("externalProcessPid") is not None
        or state.get("afterRollback", {}).get("enabled") is not False
        or state.get("afterRollback", {}).get("externalProcessPid") is not None
    ):
        findings.append(finding("serviceWrapperState", "Service-wrapper state must represent only temporary local enable, hold-disable, and rollback with no external process."))
    transcript = scenario.get("commandTranscript", {})
    if transcript.get("mode") != "bounded-external-service-activation-gate" or transcript.get("exitCode") != 0:
        findings.append(finding("commandTranscript", "Command transcript must be this local bounded activation gate and exit 0."))
    if transcript.get("command") != REQUIRED_TRANSCRIPT_COMMAND:
        findings.append(finding("commandTranscript.command", "Command transcript must record the pinned local gate generator command."))
    findings.extend(gate.command_findings([transcript.get("command")], "commandTranscript.command"))
    trace = scenario.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("traceEvalSummary", "Trace/eval summary must pass without tool execution."))
    decision = scenario.get("activationDecision", {})
    if decision.get("decision") not in {"hold", "rollback"} or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("activationDecision", "Activation decision must be hold or rollback with no live action authorization."))
    rollback = scenario.get("rollbackDisableVerification", {})
    if rollback.get("disableCommand") != "external-service:disable --target simple-agent --state ephemeral --dry-run":
        findings.append(finding("rollbackDisableVerification.disableCommand", "Disable verification must use the pinned external-service dry-run command."))
    if rollback.get("rollbackCommand") != "external-service:rollback --target simple-agent --state ephemeral --dry-run":
        findings.append(finding("rollbackDisableVerification.rollbackCommand", "Rollback verification must use the pinned external-service dry-run command."))
    if rollback.get("wrapperEnabledAfterRollback") is not False or rollback.get("externalProcessStarted") is not False or rollback.get("persistentMutation") is not False:
        findings.append(finding("rollbackDisableVerification.wrapperEnabledAfterRollback", "Rollback must prove disabled local state, no process start, and no persistence."))
    risk = scenario.get("riskVerdict")
    if risk != "hold-fail-closed-before-real-external-service-activation":
        findings.append(finding("riskVerdict", "Risk verdict must fail closed before real external-service activation."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must require a separate approved micro-gate before real mutation or mainnet."))
    audit = scenario.get("auditTrail", [])
    if audit != ["load-pinned-299-evidence", "record-before-disabled", "represent-local-temporary-activation", "hold-disable-local-state", "rollback-local-state"]:
        findings.append(finding("auditTrail", "Audit trail must record pinned load, before, represented activation, hold-disable, and rollback exactly."))
    findings.extend(operator_run.smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(operator_run.smoke.unsafe_claim_findings(scenario, "scenario"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    return findings


def build_run_evidence(
    scenario: dict[str, Any],
    prior_doc: dict[str, Any],
    fixture_binding: dict[str, Any],
    report_binding: dict[str, Any],
    commit: str,
) -> dict[str, Any]:
    prior = accepted_299_result(prior_doc) or {}
    prior_evidence = prior.get("runEvidence", {}) if isinstance(prior.get("runEvidence", {}), dict) else {}
    prior_297 = prior_evidence.get("prior297Evidence", {})
    return {
        "runEvidenceId": scenario.get("runEvidenceId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior299Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": prior.get("id"),
            "acceptedVerdict": prior.get("verdict"),
            "prior297Fixture": prior_297.get("fixture", {}),
            "prior295Fixture": prior_297.get("prior295Fixture", {}),
            "prior293Fixture": prior_297.get("prior293Fixture", {}),
            "approvalPacketFixture": prior_297.get("approvalPacketFixture", {}),
            "selectedRuntimePath": prior_evidence.get("activationScope", {}),
            "priorRiskVerdict": prior_evidence.get("riskVerdict"),
        },
        "currentOperatorApprovalState": scenario.get("currentOperatorApprovalState", {}),
        "activationScope": scenario.get("activationScope", {}),
        "commandTranscript": scenario.get("commandTranscript", {}),
        "traceEvalSummary": scenario.get("traceEvalSummary", {}),
        "serviceWrapperState": scenario.get("serviceWrapperState", {}),
        "activationDecision": scenario.get("activationDecision", {}),
        "rollbackDisableVerification": scenario.get("rollbackDisableVerification", {}),
        "auditTrail": scenario.get("auditTrail", []),
        "riskVerdict": scenario.get("riskVerdict"),
        "nextStepCue": scenario.get("nextStepCue"),
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_299_FIXTURE_PATH, hashes.get(PINNED_299_FIXTURE_PATH, ""), "prior299Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_299_REPORT_PATH, hashes.get(PINNED_299_REPORT_PATH, ""), "prior299Report", findings)
    prior_doc: dict[str, Any] = {}
    prior_path = ROOT / PINNED_299_FIXTURE_PATH
    if prior_path.exists():
        try:
            prior_doc = load_json(prior_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding("prior299Fixture.json", f"Prior #299 evidence must be JSON: {exc}"))
    findings.extend(prior_299_findings(prior_doc))
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
        "mode": "beta-bounded-external-service-activation-gate",
        "issue": 301,
        "parentEpic": 220,
        "follows": [299, 297, 295, 293, 291, 289, 287, 285],
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
        "mainnetStatement": "This bounded external-service activation gate does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Bounded activation gate scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated bounded activation gate JSON.")
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
