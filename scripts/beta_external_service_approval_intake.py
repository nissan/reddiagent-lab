#!/usr/bin/env python3
"""Build deterministic Nissan approval-intake evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-approval-intake-scenarios.json"
PINNED_303_MERGE_COMMIT = "d0e7b7968ef9c9e7086cbb1a9dfef5a104be6a24"
PINNED_303_FIXTURE_PATH = "tests/fixtures/beta-external-service-activation-micro-gate.json"
PINNED_303_FIXTURE_SHA256 = "df7da6f3012c7c2f1f66287f3f2e8030862e7f6526dce248e7154d07e4199832"
PINNED_303_REPORT_PATH = "tests/BETA-EXTERNAL-SERVICE-ACTIVATION-MICRO-GATE-REPORT.md"
PINNED_303_REPORT_SHA256 = "ff96d3c6c0a8177625e4e44b2e027ca2135bbe57ab4155a0ccb22d545d7082aa"
REQUIRED_RUN_ID = "reddiagent-beta-0-external-service-approval-intake"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_APPROVAL_PROMPT = (
    "Approve exactly this local/free bounded external-service activation scope for examples/simple-agent.yaml, "
    "with no provider/devnet/mainnet escalation?"
)
REQUIRED_INTAKE_COMMAND = (
    "python scripts/beta_external_service_approval_intake.py "
    "--output tests/fixtures/beta-external-service-approval-intake.json"
)
REQUIRED_HOLD_DECISION = "hold-fail-closed"
REQUIRED_HOLD_RISK = "hold-fail-closed-without-fresh-nissan-approval"
REQUIRED_AUDIT_TRAIL = [
    "load-pinned-303-evidence",
    "verify-303-consumed-301",
    "verify-299-297-295-293-291-lineage",
    "record-exact-approval-prompt",
    "record-nissan-response-fields",
    "derive-approve-or-hold-decision",
    "stop-before-real-mutation",
]
ESCALATION_MARKERS = (
    "provider",
    "production",
    "devnet",
    "mainnet",
    "cost",
    "privacy",
    "legal",
    "docker",
    "coolify",
    "mcp",
    "payment",
    "wallet",
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
    "persistentMutation",
    "unboundedMutation",
    "productionEscalation",
)

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_service_activation_micro_gate as micro_gate  # noqa: E402
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
    boundaries = micro_gate.boundary_values()
    boundaries.update(
        {
            "approvalIntakeOnly": True,
            "approvalPromptPinned": True,
            "nissanApprovalFreshnessRequired": True,
            "realMutationAuthorized": False,
            "mainnetBlocked": True,
        }
    )
    return boundaries


def false_boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in boundary_values().items():
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def accepted_303_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "external-service-activation-micro-gate-ask-hold-pass":
            return result
    return None


def prior_303_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-external-service-activation-micro-gate":
        findings.append(finding("prior303Fixture.mode", "Pinned #303 fixture must be the activation micro-gate."))
    if doc.get("issue") != 303 or doc.get("parentEpic") != 220:
        findings.append(finding("prior303Fixture.issue", "Pinned #303 fixture must belong to issue #303 and parent #220."))
    if doc.get("follows") != [301, 299, 297, 295, 293, 291, 289, 287, 285]:
        findings.append(finding("prior303Fixture.follows", "Pinned #303 fixture must preserve #301/#299/#297/#295/#293/#291 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior303Fixture.status", "Pinned #303 fixture must pass."))
    findings.extend(micro_gate.false_boundary_findings(doc.get("boundaries", {}), "prior303Fixture.boundaries"))
    result = accepted_303_result(doc)
    if not result:
        findings.append(finding("prior303Fixture.results", "Pinned #303 fixture must include the accepted ask/hold result."))
        return findings
    evidence = result.get("runEvidence", {})
    if result.get("status") != "pass" or result.get("verdict") != "ask-nissan-and-hold":
        findings.append(finding("prior303Fixture.results.verdict", "Accepted #303 result must pass with ask/hold verdict."))
    if evidence.get("nissanApproval", {}).get("approvalPrompt") != REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("prior303Fixture.results.nissanApproval.approvalPrompt", "Accepted #303 prompt must remain exact."))
    prior301 = evidence.get("prior301Evidence", {})
    if (
        prior301.get("fixture", {}).get("path") != micro_gate.PINNED_301_FIXTURE_PATH
        or prior301.get("fixture", {}).get("sha256") != micro_gate.PINNED_301_FIXTURE_SHA256
        or prior301.get("fixture", {}).get("hashMatches") is not True
    ):
        findings.append(finding("prior303Fixture.results.prior301Evidence.fixture", "Accepted #303 evidence must consume pinned #301 evidence."))
    lineage = {
        "prior299Fixture": micro_gate.bounded_gate.PINNED_299_FIXTURE_SHA256,
        "prior297Fixture": micro_gate.bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256,
        "prior295Fixture": micro_gate.bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256,
        "prior293Fixture": micro_gate.bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256,
        "approvalPacketFixture": micro_gate.bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256,
    }
    for key, expected_sha in lineage.items():
        if prior301.get(key, {}).get("sha256") != expected_sha:
            findings.append(finding(f"prior303Fixture.results.prior301Evidence.{key}", f"Accepted #303 evidence must preserve pinned {key} lineage."))
    if evidence.get("askHoldDecision", {}).get("liveActionAuthorized") is not False:
        findings.append(finding("prior303Fixture.results.askHoldDecision", "Accepted #303 evidence must not authorize live action."))
    return findings


def approval_decision(response: dict[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    if not isinstance(response, dict):
        return REQUIRED_HOLD_DECISION, REQUIRED_HOLD_RISK, [finding("nissanResponse", "Nissan response fields must be an object.")]
    status = response.get("status")
    text = str(response.get("responseText") or "").strip()
    source = response.get("source")
    timestamp = response.get("timestamp")
    if response.get("prompt") != REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("nissanResponse.prompt", "Response must echo the exact approval prompt."))
    if status in ("absent", "pending"):
        return REQUIRED_HOLD_DECISION, REQUIRED_HOLD_RISK, findings
    if not source or not timestamp:
        findings.append(finding("nissanResponse.source", "Response source and timestamp fields are required."))
    if status != "approved":
        findings.append(finding("nissanResponse.status", "Only absent, pending, or exact approved status is accepted."))
        return REQUIRED_HOLD_DECISION, REQUIRED_HOLD_RISK, findings
    findings.append(
        finding(
            "nissanResponse.status",
            "This deterministic #305 package cannot self-certify approval; approved responses require a future fresh external approval capture.",
        )
    )
    if response.get("fresh") is not True:
        findings.append(finding("nissanResponse.fresh", "Approval must be fresh for #305."))
    if response.get("scope") != "exact-303-local-free-bounded-scope":
        findings.append(finding("nissanResponse.scope", "Approval scope must match the exact #303 local/free bounded scope."))
    if response.get("approver") != "Nissan":
        findings.append(finding("nissanResponse.approver", "Approver must be Nissan."))
    lowered = text.lower()
    if "approve" not in lowered:
        findings.append(finding("nissanResponse.responseText", "Approval response text must explicitly approve."))
    for marker in ESCALATION_MARKERS:
        if response.get(f"{marker}Escalation") is True or marker in lowered:
            findings.append(finding("nissanResponse.escalation", f"Response must not include {marker} escalation."))
    for field in ("providerEscalation", "productionEscalation", "devnetEscalation", "mainnetEscalation", "costEscalation", "privacyEscalation", "legalEscalation"):
        if response.get(field) is not False:
            findings.append(finding(f"nissanResponse.{field}", f"{field} must be false."))
    return REQUIRED_HOLD_DECISION, REQUIRED_HOLD_RISK, findings


def scenario_findings(scenario: dict[str, Any]) -> tuple[list[dict[str, str]], str, str]:
    findings: list[dict[str, str]] = []
    if scenario.get("approvalIntakeId") != REQUIRED_RUN_ID:
        findings.append(finding("approvalIntakeId", f"Approval intake id must be `{REQUIRED_RUN_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_303_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_303_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_303_FIXTURE_PATH or hashes.get(PINNED_303_FIXTURE_PATH) != PINNED_303_FIXTURE_SHA256:
        findings.append(finding("prior303Fixture.expectedSha256", "Prior #303 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_303_REPORT_PATH or hashes.get(PINNED_303_REPORT_PATH) != PINNED_303_REPORT_SHA256:
        findings.append(finding("prior303Report.expectedSha256", "Prior #303 report path and sha256 must be pinned from the merge commit."))
    if scenario.get("approvalPrompt") != REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("approvalPrompt", "Approval prompt must be exact."))
    if scenario.get("intakeCommand") != REQUIRED_INTAKE_COMMAND:
        findings.append(finding("intakeCommand", "Intake command must be the pinned local generator."))
    findings.extend(gate.command_findings([scenario.get("intakeCommand", "")], "intakeCommand"))
    for field in UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this approval-intake package."))
    scope = scenario.get("boundedScopeEcho", {})
    if (
        scope.get("sourceIssue") != 303
        or scope.get("adlPath") != gate.REQUIRED_ADL_PATH
        or scope.get("scope") != "local/free/bounded approval only"
        or scope.get("providerEscalation") is not False
        or scope.get("devnetEscalation") is not False
        or scope.get("mainnetEscalation") is not False
        or scope.get("estimatedCostUsd") != "0.00"
    ):
        findings.append(finding("boundedScopeEcho", "Bounded scope echo must match #303 exactly and reject escalation."))
    preconditions = scenario.get("preconditionEcho", {})
    for key in ("pinned303EvidencePresent", "pinned303HashMatches", "pinned301Consumed", "lineagePreserved", "mainnetBlocked", "noRealMutation"):
        if not isinstance(preconditions, dict) or preconditions.get(key) is not True:
            findings.append(finding(f"preconditionEcho.{key}", f"{key} must be true."))
    decision, risk, response_findings = approval_decision(scenario.get("nissanResponse", {}))
    findings.extend(response_findings)
    expected_decision = scenario.get("expectedDecision")
    expected_risk = scenario.get("expectedRiskVerdict")
    if expected_decision != REQUIRED_HOLD_DECISION:
        findings.append(finding("expectedDecision", "Expected decision must hold fail-closed in this package."))
    if expected_risk != REQUIRED_HOLD_RISK:
        findings.append(finding("expectedRiskVerdict", "Expected risk verdict must hold without fresh Nissan approval."))
    if scenario.get("auditTrail") != REQUIRED_AUDIT_TRAIL:
        findings.append(finding("auditTrail", "Audit trail must record evidence load, lineage, response, decision, and stop."))
    if scenario.get("stopBeforeMutation") is not True:
        findings.append(finding("stopBeforeMutation", "Approval intake must stop before mutation."))
    findings.extend(micro_gate.bounded_gate.operator_run.smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(micro_gate.bounded_gate.operator_run.smoke.unsafe_claim_findings(scenario, "scenario"))
    return findings, decision, risk


def build_run_evidence(
    scenario: dict[str, Any],
    prior_doc: dict[str, Any],
    fixture_binding: dict[str, Any],
    report_binding: dict[str, Any],
    decision: str,
    risk: str,
    commit: str,
) -> dict[str, Any]:
    accepted = accepted_303_result(prior_doc) or {}
    prior_evidence = accepted.get("runEvidence", {}) if isinstance(accepted.get("runEvidence", {}), dict) else {}
    return {
        "approvalIntakeId": scenario.get("approvalIntakeId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior303Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": accepted.get("id"),
            "acceptedVerdict": accepted.get("verdict"),
            "prior301Fixture": prior_evidence.get("prior301Evidence", {}).get("fixture", {}),
            "prior299Fixture": prior_evidence.get("prior301Evidence", {}).get("prior299Fixture", {}),
            "prior297Fixture": prior_evidence.get("prior301Evidence", {}).get("prior297Fixture", {}),
            "prior295Fixture": prior_evidence.get("prior301Evidence", {}).get("prior295Fixture", {}),
            "prior293Fixture": prior_evidence.get("prior301Evidence", {}).get("prior293Fixture", {}),
            "approvalPacketFixture": prior_evidence.get("prior301Evidence", {}).get("approvalPacketFixture", {}),
            "approvalPrompt": prior_evidence.get("nissanApproval", {}).get("approvalPrompt"),
        },
        "approvalPrompt": scenario.get("approvalPrompt"),
        "nissanResponse": scenario.get("nissanResponse", {}),
        "timestampSourceFields": {
            "responseTimestamp": scenario.get("nissanResponse", {}).get("timestamp"),
            "responseSource": scenario.get("nissanResponse", {}).get("source"),
            "fresh": scenario.get("nissanResponse", {}).get("fresh"),
        },
        "boundedScopeEcho": scenario.get("boundedScopeEcho", {}),
        "preconditionEcho": scenario.get("preconditionEcho", {}),
        "approveOrHoldDecision": {
            "decision": decision,
            "liveActionAuthorized": False,
            "stopBeforeMutation": True,
        },
        "auditTrail": scenario.get("auditTrail", []),
        "riskVerdict": risk,
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings, decision, risk = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_303_FIXTURE_PATH, hashes.get(PINNED_303_FIXTURE_PATH, ""), "prior303Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_303_REPORT_PATH, hashes.get(PINNED_303_REPORT_PATH, ""), "prior303Report", findings)
    prior_doc = gate.load_artifact(PINNED_303_FIXTURE_PATH, "prior303Fixture", findings)
    findings.extend(prior_303_findings(prior_doc))
    status = "pass" if not findings else "fail"
    verdict = decision if status == "pass" else scenario.get("expectedDecision", REQUIRED_HOLD_DECISION)
    risk_verdict = risk if status == "pass" else scenario.get("expectedRiskVerdict", REQUIRED_HOLD_RISK)
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": verdict,
        "expectedVerdict": scenario["expectedDecision"],
        "findings": findings,
        "sourceCommit": commit,
        "runEvidence": build_run_evidence(scenario, prior_doc, fixture_binding, report_binding, verdict, risk_verdict, commit),
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
        "mode": "beta-external-service-approval-intake",
        "issue": 305,
        "parentEpic": 220,
        "follows": [303, 301, 299, 297, 295, 293, 291, 289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "holdDecisions": sum(1 for result in results if result["verdict"] == REQUIRED_HOLD_DECISION),
            "approveDecisions": 0,
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": boundary_values(),
        "mainnetStatement": "This approval-intake package does not approve or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Approval-intake scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated approval-intake JSON.")
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
