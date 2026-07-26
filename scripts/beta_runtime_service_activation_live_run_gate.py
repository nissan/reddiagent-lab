#!/usr/bin/env python3
"""Build deterministic bounded beta runtime service activation live-run gate output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-live-run-gate-scenarios.json"
PINNED_293_MERGE_COMMIT = "2f956e536cdfa39b443a08709c1d7ea41ab0f8d0"
PINNED_293_FIXTURE_PATH = "tests/fixtures/beta-runtime-service-activation-evidence-gate.json"
PINNED_293_FIXTURE_SHA256 = "f757357a79cf253ea238e6e0fda286912da0bb02da3a362e7bb253607a133524"
PINNED_293_REPORT_PATH = "tests/BETA-RUNTIME-SERVICE-ACTIVATION-EVIDENCE-GATE-REPORT.md"
PINNED_293_REPORT_SHA256 = "0a90b83e5ef992faa1bba8c898f380066a70e300a42f4589b63feb2ee0129a56"
PINNED_291_APPROVAL_PACKET_SHA256 = "e86cc4fbb030521c969e7bb833a96c14ad1baf2bf9242e516065b3666dccd452"
REQUIRED_RUN_ID = "reddiagent-beta-0-runtime-service-activation-live-run-gate"
REQUIRED_PRIOR_RUN_ID = "reddiagent-beta-0-runtime-service-activation-evidence-gate"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_NEXT_STEP_CUE = (
    "Hold after this bounded local live-run gate; actual service activation remains blocked until a fresh "
    "bounded operator run explicitly starts the service with audited rollback and no mainnet risk."
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
        "boundedDryRunSubstituteOnly": True,
        "actualServiceMutation": False,
        "liveRuntimeActivation": False,
        "serviceStarted": False,
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


def accepted_prior_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "runtime-service-activation-evidence-hold-pass":
            return result
    for result in doc.get("results", []):
        if result.get("status") == "pass" and result.get("verdict") == "hold-for-live-run":
            return result
    return None


def false_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in boundary_values().items():
        if field == "boundedDryRunSubstituteOnly":
            continue
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def prior_evidence_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-runtime-service-activation-evidence-gate":
        findings.append(finding("prior293Fixture.mode", "Pinned #293 fixture must be the service activation evidence gate."))
    if doc.get("issue") != 293 or doc.get("parentEpic") != 220:
        findings.append(finding("prior293Fixture.issue", "Pinned #293 fixture must belong to issue #293 and parent #220."))
    if doc.get("follows") != [291, 289, 287, 285]:
        findings.append(finding("prior293Fixture.follows", "Pinned #293 fixture must preserve #291/#289/#287/#285 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior293Fixture.status", "Pinned #293 fixture must pass."))
    findings.extend(false_boundary_findings(doc.get("boundaries", {}), "prior293Fixture.boundaries"))
    result = accepted_prior_result(doc)
    if not result:
        findings.append(finding("prior293Fixture.results", "Pinned #293 fixture must include accepted hold-for-live-run evidence."))
        return findings
    if result.get("status") != "pass" or result.get("verdict") != "hold-for-live-run":
        findings.append(finding("prior293Fixture.results.verdict", "Accepted #293 result must pass with hold-for-live-run verdict."))
    evidence = result.get("runEvidence", {})
    if not isinstance(evidence, dict):
        findings.append(finding("prior293Fixture.results.runEvidence", "Accepted #293 run evidence must be an object."))
        return findings
    if evidence.get("runEvidenceId") != REQUIRED_PRIOR_RUN_ID:
        findings.append(finding("prior293Fixture.results.runEvidenceId", f"Prior run id must be `{REQUIRED_PRIOR_RUN_ID}`."))
    approval_fixture = evidence.get("approvalPacketEvidence", {}).get("fixture", {})
    if approval_fixture.get("sha256") != PINNED_291_APPROVAL_PACKET_SHA256 or approval_fixture.get("hashMatches") is not True:
        findings.append(finding("prior293Fixture.results.approvalPacketEvidence.fixture", "Accepted #293 evidence must preserve the pinned #291 approval-packet hash."))
    selected = evidence.get("selectedRuntimePath", {})
    if selected.get("adlPath") != gate.REQUIRED_ADL_PATH or selected.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX:
        findings.append(finding("prior293Fixture.results.selectedRuntimePath", "Accepted #293 evidence may select only examples/simple-agent.yaml."))
    approvals = evidence.get("operatorApprovalsRecorded", {})
    for name in REQUIRED_OPERATOR_APPROVALS:
        if approvals.get(name) is not True:
            findings.append(finding(f"prior293Fixture.results.operatorApprovalsRecorded.{name}", f"{name} must be recorded true."))
    checklist = " ".join(item for item in evidence.get("preflightChecklist", []) if isinstance(item, str)).lower()
    for marker in ("operator approval", "rollback", "trace/eval", "mainnet"):
        if marker not in checklist:
            findings.append(finding("prior293Fixture.results.preflightChecklist", f"Accepted #293 preflight must mention {marker}."))
    trace = evidence.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("prior293Fixture.results.traceEvalSummary", "Accepted #293 trace/eval summary must pass without tool execution."))
    rollback = evidence.get("rollbackDisableVerification", {})
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False or not rollback.get("disableCommand") or not rollback.get("rollbackCommand"):
        findings.append(finding("prior293Fixture.results.rollbackDisableVerification", "Accepted #293 evidence must preserve rollback/disable proof."))
    if evidence.get("activationDecision", {}).get("liveActionAuthorized") is not False:
        findings.append(finding("prior293Fixture.results.activationDecision.liveActionAuthorized", "Accepted #293 evidence must stop before live activation."))
    if evidence.get("boundedRunTranscript", {}).get("mode") != "dry-run-substitute":
        findings.append(finding("prior293Fixture.results.boundedRunTranscript.mode", "Accepted #293 transcript must remain a dry-run substitute."))
    if evidence.get("riskVerdict") != "hold-for-separate-live-run":
        findings.append(finding("prior293Fixture.results.riskVerdict", "Accepted #293 risk verdict must hold before live activation."))
    findings.extend(false_boundary_findings(evidence.get("boundaries", {}), "prior293Fixture.results.boundaries"))
    findings.extend(smoke.sensitive_payload_findings(evidence, "prior293Fixture.results.runEvidence"))
    findings.extend(smoke.unsafe_claim_findings(evidence, "prior293Fixture.results.runEvidence"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("runEvidenceId") != REQUIRED_RUN_ID:
        findings.append(finding("runEvidenceId", f"Run evidence id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_293_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_293_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_293_FIXTURE_PATH or hashes.get(PINNED_293_FIXTURE_PATH) != PINNED_293_FIXTURE_SHA256:
        findings.append(finding("prior293Fixture.expectedSha256", "Prior #293 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_293_REPORT_PATH or hashes.get(PINNED_293_REPORT_PATH) != PINNED_293_REPORT_SHA256:
        findings.append(finding("prior293Report.expectedSha256", "Prior #293 report path and sha256 must be pinned from the merge commit."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this bounded local gate."))
    approvals = scenario.get("currentOperatorApprovalState", {})
    if not isinstance(approvals, dict):
        findings.append(finding("currentOperatorApprovalState", "Current operator approval state must be an object."))
    else:
        for name in REQUIRED_OPERATOR_APPROVALS:
            if approvals.get(name) is not True:
                findings.append(finding(f"currentOperatorApprovalState.{name}", f"{name} must be recorded true for this bounded gate."))
    scope = scenario.get("activationScope", {})
    if scope.get("adlPath") != gate.REQUIRED_ADL_PATH or scope.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX or scope.get("liveMutation") is not False:
        findings.append(finding("activationScope", "Activation scope must be examples/simple-agent.yaml with no live mutation."))
    transcript = scenario.get("boundedTranscript", {})
    if transcript.get("mode") != "bounded-local-live-run-substitute" or transcript.get("exitCode") != 0:
        findings.append(finding("boundedTranscript", "Bounded transcript must be the local live-run substitute and exit 0."))
    trace = scenario.get("traceEvalSummary", {})
    if trace.get("completionStatus") != "pass" or trace.get("requiredGateStatus") != "pass" or trace.get("toolExecution") is not None:
        findings.append(finding("traceEvalSummary", "Trace/eval summary must pass without tool execution."))
    rollback = scenario.get("rollbackDisableVerification", {})
    if rollback.get("disableCommand") != "local-runtime:disable --target simple-agent --dry-run":
        findings.append(finding("rollbackDisableVerification.disableCommand", "Disable verification must use the pinned dry-run command."))
    if rollback.get("rollbackCommand") != "local-runtime:rollback --target simple-agent --dry-run":
        findings.append(finding("rollbackDisableVerification.rollbackCommand", "Rollback verification must use the pinned dry-run command."))
    if rollback.get("liveRuntimeEnabledAfterRollback") is not False:
        findings.append(finding("rollbackDisableVerification.liveRuntimeEnabledAfterRollback", "Rollback verification must leave live runtime disabled."))
    decision = scenario.get("operatorDecision", {})
    if decision.get("decision") not in {"hold", "rollback"} or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("operatorDecision", "Decision must be hold or rollback with no live action authorization."))
    if scenario.get("riskVerdict") != "hold-before-actual-service-activation":
        findings.append(finding("riskVerdict", "Risk verdict must hold before actual service activation."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must stop before actual service activation."))
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
    prior = accepted_prior_result(prior_doc) or {}
    prior_evidence = prior.get("runEvidence", {}) if isinstance(prior.get("runEvidence", {}), dict) else {}
    return {
        "runEvidenceId": scenario.get("runEvidenceId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior293Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": prior.get("id"),
            "acceptedVerdict": prior.get("verdict"),
            "approvalPacketFixture": prior_evidence.get("approvalPacketEvidence", {}).get("fixture", {}),
            "selectedRuntimePath": prior_evidence.get("selectedRuntimePath", {}),
            "priorRiskVerdict": prior_evidence.get("riskVerdict"),
        },
        "currentOperatorApprovalState": scenario.get("currentOperatorApprovalState", {}),
        "activationScope": scenario.get("activationScope", {}),
        "boundedTranscript": scenario.get("boundedTranscript", {}),
        "traceEvalSummary": scenario.get("traceEvalSummary", {}),
        "operatorDecision": scenario.get("operatorDecision", {}),
        "rollbackDisableVerification": scenario.get("rollbackDisableVerification", {}),
        "riskVerdict": scenario.get("riskVerdict"),
        "nextStepCue": scenario.get("nextStepCue"),
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_293_FIXTURE_PATH, hashes.get(PINNED_293_FIXTURE_PATH, ""), "prior293Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_293_REPORT_PATH, hashes.get(PINNED_293_REPORT_PATH, ""), "prior293Report", findings)
    prior_doc: dict[str, Any] = {}
    prior_path = ROOT / PINNED_293_FIXTURE_PATH
    if prior_path.exists():
        try:
            prior_doc = load_json(prior_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding("prior293Fixture.json", f"Prior #293 evidence must be JSON: {exc}"))
    findings.extend(prior_evidence_findings(prior_doc))
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
        "mode": "beta-runtime-service-activation-live-run-gate",
        "issue": 295,
        "parentEpic": 220,
        "follows": [293, 291, 289, 287, 285],
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
        "mainnetStatement": "This live-run gate does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Live-run gate scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated live-run gate JSON.")
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
