#!/usr/bin/env python3
"""Build deterministic Nissan approval micro-gate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-activation-micro-gate-scenarios.json"
PINNED_301_MERGE_COMMIT = "290af941f49bdfc219b14c0f805b25f8b553954e"
PINNED_301_FIXTURE_PATH = "tests/fixtures/beta-bounded-external-service-activation-gate.json"
PINNED_301_FIXTURE_SHA256 = "493c219fd0c56c74544040cb3f4cfa7aef7d1e2cdd35b5444dc72ebb8e451611"
PINNED_301_REPORT_PATH = "tests/BETA-BOUNDED-EXTERNAL-SERVICE-ACTIVATION-GATE-REPORT.md"
PINNED_301_REPORT_SHA256 = "cf19f0f1464100ee607ee5d19b4618ecdee716da492a187f06a48c31ea46499c"
REQUIRED_RUN_ID = "reddiagent-beta-0-external-service-activation-micro-gate"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_TRANSCRIPT_COMMAND = (
    "python scripts/beta_external_service_activation_micro_gate.py "
    "--output tests/fixtures/beta-external-service-activation-micro-gate.json"
)
REQUIRED_DECISION = "ask-nissan-and-hold"
REQUIRED_RISK_VERDICT = "hold-fail-closed-until-nissan-approval"
REQUIRED_NEXT_STEP_CUE = (
    "Ask Nissan to approve the exact bounded local/free external-service activation scope; hold before "
    "any real service, provider, devnet, or mainnet mutation until that approval is explicit and fresh."
)
REQUIRED_APPROVAL_PROMPT = (
    "Approve exactly this local/free bounded external-service activation scope for examples/simple-agent.yaml, "
    "with no provider/devnet/mainnet escalation?"
)
REQUIRED_AUDIT_TRAIL = [
    "load-pinned-301-evidence",
    "verify-301-consumed-299",
    "verify-297-295-293-291-lineage",
    "record-proposed-run-scope",
    "record-nissan-approval-fields",
    "hold-before-real-mutation",
]
UNSAFE_FLAG_FIELDS = tuple(
    field
    for field in (
        *(
            name
            for name in (
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
                "persistentMutation",
                "unboundedMutation",
                "productionEscalation",
                "legalRiskAccepted",
                "privacyRiskAccepted",
                "unboundedCostAccepted",
            )
        ),
        *(
            name
            for name in (
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
        ),
    )
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_bounded_external_service_activation_gate as bounded_gate  # noqa: E402
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
    boundaries = bounded_gate.boundary_values()
    boundaries.update(
        {
            "approvalPacketOnly": True,
            "nissanApprovalRequired": True,
            "realMutationAuthorized": False,
            "productionEscalation": False,
            "legalRiskAccepted": False,
            "privacyRiskAccepted": False,
            "unboundedCostAccepted": False,
        }
    )
    return boundaries


def false_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in boundary_values().items():
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def accepted_301_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "bounded-external-activation-hold-pass":
            return result
    return None


def prior_301_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-bounded-external-service-activation-gate":
        findings.append(finding("prior301Fixture.mode", "Pinned #301 fixture must be the bounded activation gate."))
    if doc.get("issue") != 301 or doc.get("parentEpic") != 220:
        findings.append(finding("prior301Fixture.issue", "Pinned #301 fixture must belong to issue #301 and parent #220."))
    if doc.get("follows") != [299, 297, 295, 293, 291, 289, 287, 285]:
        findings.append(finding("prior301Fixture.follows", "Pinned #301 fixture must preserve #299/#297/#295/#293/#291 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior301Fixture.status", "Pinned #301 fixture must pass."))
    findings.extend(bounded_gate.false_boundary_findings(doc.get("boundaries", {}), "prior301Fixture.boundaries"))
    result = accepted_301_result(doc)
    if not result:
        findings.append(finding("prior301Fixture.results", "Pinned #301 fixture must include bounded-external-activation-hold-pass."))
        return findings
    if result.get("status") != "pass" or result.get("verdict") != "hold":
        findings.append(finding("prior301Fixture.results.verdict", "Accepted #301 result must pass with hold verdict."))
    evidence = result.get("runEvidence", {})
    if not isinstance(evidence, dict):
        findings.append(finding("prior301Fixture.results.runEvidence", "Accepted #301 run evidence must be an object."))
        return findings
    prior299 = evidence.get("prior299Evidence", {})
    fixture299 = prior299.get("fixture", {})
    if (
        fixture299.get("path") != bounded_gate.PINNED_299_FIXTURE_PATH
        or fixture299.get("sha256") != bounded_gate.PINNED_299_FIXTURE_SHA256
        or fixture299.get("hashMatches") is not True
    ):
        findings.append(finding("prior301Fixture.results.prior299Evidence.fixture", "Accepted #301 evidence must consume pinned #299 evidence by path and sha256."))
    if prior299.get("prior297Fixture", {}).get("sha256") != bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256:
        findings.append(finding("prior301Fixture.results.prior299Evidence.prior297Fixture", "Accepted #301 evidence must preserve pinned #297 evidence."))
    if prior299.get("prior295Fixture", {}).get("sha256") != bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256:
        findings.append(finding("prior301Fixture.results.prior299Evidence.prior295Fixture", "Accepted #301 evidence must preserve pinned #295 evidence."))
    if prior299.get("prior293Fixture", {}).get("sha256") != bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256:
        findings.append(finding("prior301Fixture.results.prior299Evidence.prior293Fixture", "Accepted #301 evidence must preserve pinned #293 evidence."))
    if prior299.get("approvalPacketFixture", {}).get("sha256") != bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256:
        findings.append(finding("prior301Fixture.results.prior299Evidence.approvalPacketFixture", "Accepted #301 evidence must preserve pinned #291 approval-packet evidence."))
    if evidence.get("riskVerdict") != "hold-fail-closed-before-real-external-service-activation":
        findings.append(finding("prior301Fixture.results.riskVerdict", "Accepted #301 risk verdict must hold before real external-service activation."))
    decision = evidence.get("activationDecision", {})
    if decision.get("decision") != "hold" or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("prior301Fixture.results.activationDecision", "Accepted #301 must hold before external mutation."))
    findings.extend(bounded_gate.operator_run.smoke.sensitive_payload_findings(evidence, "prior301Fixture.results.runEvidence"))
    findings.extend(bounded_gate.operator_run.smoke.unsafe_claim_findings(evidence, "prior301Fixture.results.runEvidence"))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("runEvidenceId") != REQUIRED_RUN_ID:
        findings.append(finding("runEvidenceId", f"Run evidence id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_301_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_301_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_301_FIXTURE_PATH or hashes.get(PINNED_301_FIXTURE_PATH) != PINNED_301_FIXTURE_SHA256:
        findings.append(finding("prior301Fixture.expectedSha256", "Prior #301 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_301_REPORT_PATH or hashes.get(PINNED_301_REPORT_PATH) != PINNED_301_REPORT_SHA256:
        findings.append(finding("prior301Report.expectedSha256", "Prior #301 report path and sha256 must be pinned from the merge commit."))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this approval micro-gate."))
    approvals = scenario.get("nissanApproval", {})
    if (
        not isinstance(approvals, dict)
        or approvals.get("required") is not True
        or approvals.get("status") != "pending"
        or approvals.get("approved") is not False
        or approvals.get("approvedBy") is not None
        or approvals.get("approvedAt") is not None
        or approvals.get("approvalPrompt") != REQUIRED_APPROVAL_PROMPT
    ):
        findings.append(finding("nissanApproval", "Nissan approval fields must be present, pending, not approved, and pinned to the exact bounded no-escalation ask."))
    scope = scenario.get("proposedRunScope", {})
    if (
        scope.get("adlPath") != gate.REQUIRED_ADL_PATH
        or scope.get("reviewedCommand") != gate.LOCAL_COMMAND_PREFIX
        or scope.get("serviceWrapper") != "local-ephemeral-json-state"
        or scope.get("runType") != "bounded-local-free-approval-gate"
        or scope.get("liveMutation") is not False
        or scope.get("networkExposure") != "none"
        or scope.get("estimatedCostUsd") != "0.00"
    ):
        findings.append(finding("proposedRunScope", "Proposed run scope must be exact, local/free, simple-agent only, and non-mutating."))
    preconditions = scenario.get("preconditions", {})
    required_preconditions = {
        "pinned301EvidencePresent": True,
        "pinned301HashMatches": True,
        "lineagePreserved": True,
        "mainnetBlocked": True,
        "credentialsNotRequired": True,
        "noExternalServiceRunning": True,
    }
    for key, expected in required_preconditions.items():
        if not isinstance(preconditions, dict) or preconditions.get(key) is not expected:
            findings.append(finding(f"preconditions.{key}", f"{key} must be {str(expected).lower()}."))
    transcript = scenario.get("commandTranscriptTemplate", {})
    if transcript.get("mode") != "external-service-activation-micro-gate" or transcript.get("command") != REQUIRED_TRANSCRIPT_COMMAND or transcript.get("expectedExitCode") != 0:
        findings.append(finding("commandTranscriptTemplate", "Command transcript template must record the pinned local micro-gate generator command."))
    findings.extend(gate.command_findings([transcript.get("command")], "commandTranscriptTemplate.command"))
    trace = scenario.get("traceEvalRequirements", {})
    if (
        trace.get("requiredGateStatus") != "pass"
        or trace.get("toolExecution") is not None
        or trace.get("mustVerifyLineage") is not True
        or trace.get("mustRejectCredentialPayloads") is not True
        or trace.get("mustRejectMainnet") is not True
        or trace.get("requiredTraceEvents") != REQUIRED_AUDIT_TRAIL
    ):
        findings.append(finding("traceEvalRequirements", "Trace/eval requirements must pass locally, preserve required events, and reject credentials/mainnet/tool execution."))
    wrapper = scenario.get("serviceWrapperExpectations", {})
    if (
        wrapper.get("before", {}).get("enabled") is not False
        or wrapper.get("before", {}).get("externalProcessPid") is not None
        or wrapper.get("after", {}).get("enabled") is not False
        or wrapper.get("after", {}).get("externalProcessPid") is not None
        or wrapper.get("after", {}).get("persistentMutation") is not False
    ):
        findings.append(finding("serviceWrapperExpectations", "Service-wrapper expectations must remain disabled before/after with no process or persistence."))
    rollback = scenario.get("rollbackDisablePlan", {})
    if (
        rollback.get("disableCommand") != "external-service:disable --target simple-agent --state ephemeral --dry-run"
        or rollback.get("rollbackCommand") != "external-service:rollback --target simple-agent --state ephemeral --dry-run"
        or rollback.get("requiresRealServiceStop") is not False
        or rollback.get("verifiedNoPersistence") is not True
    ):
        findings.append(finding("rollbackDisablePlan", "Rollback/disable plan must be dry-run only, local, and persistence-free."))
    decision = scenario.get("askHoldDecision", {})
    if decision.get("decision") != REQUIRED_DECISION or decision.get("liveActionAuthorized") is not False or decision.get("requiresFreshNissanApproval") is not True:
        findings.append(finding("askHoldDecision", "Decision must ask Nissan and hold with no live action authorization."))
    if scenario.get("riskVerdict") != REQUIRED_RISK_VERDICT:
        findings.append(finding("riskVerdict", f"Risk verdict must be `{REQUIRED_RISK_VERDICT}`."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must ask Nissan and hold before real mutation or mainnet."))
    if scenario.get("auditTrail") != REQUIRED_AUDIT_TRAIL:
        findings.append(finding("auditTrail", "Audit trail must record the pinned #301 load, lineage checks, approval fields, and hold."))
    for payload_field in ("credentialPayload", "secretPayload", "privatePayload"):
        if payload_field in scenario:
            findings.append(finding(f"scenario.{payload_field}", "Credential-like payload fields are not allowed in this approval micro-gate."))
            findings.extend(
                bounded_gate.operator_run.smoke.sensitive_payload_findings(
                    scenario[payload_field],
                    f"scenario.{payload_field}",
                )
            )
    findings.extend(bounded_gate.operator_run.smoke.unsafe_claim_findings(scenario, "scenario"))
    findings.extend(gate.command_findings(scenario.get("localCommands", []), "localCommands"))
    return findings


def build_run_evidence(
    scenario: dict[str, Any],
    prior_doc: dict[str, Any],
    fixture_binding: dict[str, Any],
    report_binding: dict[str, Any],
    commit: str,
) -> dict[str, Any]:
    prior = accepted_301_result(prior_doc) or {}
    prior_evidence = prior.get("runEvidence", {}) if isinstance(prior.get("runEvidence", {}), dict) else {}
    prior_299 = prior_evidence.get("prior299Evidence", {})
    return {
        "runEvidenceId": scenario.get("runEvidenceId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior301Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": prior.get("id"),
            "acceptedVerdict": prior.get("verdict"),
            "prior299Fixture": prior_299.get("fixture", {}),
            "prior297Fixture": prior_299.get("prior297Fixture", {}),
            "prior295Fixture": prior_299.get("prior295Fixture", {}),
            "prior293Fixture": prior_299.get("prior293Fixture", {}),
            "approvalPacketFixture": prior_299.get("approvalPacketFixture", {}),
            "priorRiskVerdict": prior_evidence.get("riskVerdict"),
        },
        "proposedRunScope": scenario.get("proposedRunScope", {}),
        "preconditions": scenario.get("preconditions", {}),
        "nissanApproval": scenario.get("nissanApproval", {}),
        "commandTranscriptTemplate": scenario.get("commandTranscriptTemplate", {}),
        "traceEvalRequirements": scenario.get("traceEvalRequirements", {}),
        "serviceWrapperExpectations": scenario.get("serviceWrapperExpectations", {}),
        "rollbackDisablePlan": scenario.get("rollbackDisablePlan", {}),
        "askHoldDecision": scenario.get("askHoldDecision", {}),
        "auditTrail": scenario.get("auditTrail", []),
        "riskVerdict": scenario.get("riskVerdict"),
        "nextStepCue": scenario.get("nextStepCue"),
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_301_FIXTURE_PATH, hashes.get(PINNED_301_FIXTURE_PATH, ""), "prior301Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_301_REPORT_PATH, hashes.get(PINNED_301_REPORT_PATH, ""), "prior301Report", findings)
    prior_doc: dict[str, Any] = {}
    prior_path = ROOT / PINNED_301_FIXTURE_PATH
    if prior_path.exists():
        try:
            prior_doc = load_json(prior_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(finding("prior301Fixture.json", f"Prior #301 evidence must be JSON: {exc}"))
    findings.extend(prior_301_findings(prior_doc))
    status = "pass" if not findings else "fail"
    verdict = scenario.get("requestedVerdict", REQUIRED_DECISION) if status == "pass" else scenario.get("expectedVerdict", REQUIRED_DECISION)
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
        "mode": "beta-external-service-activation-micro-gate",
        "issue": 303,
        "parentEpic": 220,
        "follows": [301, 299, 297, 295, 293, 291, 289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "askHoldVerdicts": sum(1 for result in results if result["verdict"] == REQUIRED_DECISION),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": boundary_values(),
        "mainnetStatement": "This approval micro-gate does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Approval micro-gate scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated approval micro-gate JSON.")
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
