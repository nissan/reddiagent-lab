#!/usr/bin/env python3
"""Build deterministic evidence for Nissan's bounded external-service approval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-approval-authorization-scenarios.json"
PINNED_305_MERGE_COMMIT = "1be33d28535ccddadcf568d604bd63769df284d5"
PINNED_305_FIXTURE_PATH = "tests/fixtures/beta-external-service-approval-intake.json"
PINNED_305_FIXTURE_SHA256 = "7f55d6626612893804eac83cc6944f7ef22f663ff7f8cc430f7e3ced2afb1f9e"
PINNED_305_REPORT_PATH = "tests/BETA-EXTERNAL-SERVICE-APPROVAL-INTAKE-REPORT.md"
PINNED_305_REPORT_SHA256 = "25e3369bf54b53e03c42cd7573280f0ef3e940a24b6a51d50caa3fc912574845"
REQUIRED_AUTHORIZATION_ID = "reddiagent-beta-0-external-service-approval-authorization"
REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_RELEASE_CANDIDATE_ID = "reddiagent-beta-0-rc-local-1"
REQUIRED_APPROVAL_SOURCE = "telegram:-5218935737:16856"
REQUIRED_APPROVAL_TIMESTAMP = "2026-07-20T07:44:18+10:00"
REQUIRED_APPROVAL_TEXT = "1. You have approval to do this, and then move on to 2"
REQUIRED_APPROVAL_SCOPE = "exact-303-local-free-bounded-scope"
REQUIRED_AUTHORIZATION_COMMAND = (
    "python scripts/beta_external_service_approval_authorization.py "
    "--output tests/fixtures/beta-external-service-approval-authorization.json"
)
REQUIRED_VERDICT = "approve-exact-bounded-scope"
REQUIRED_RISK_VERDICT = "approved-for-exact-local-free-bounded-scope-mainnet-blocked"
REQUIRED_NEXT_STEP_CUE = (
    "Proceed to the next bounded local/free external-service activation evidence lane, then move on to "
    "the next #220 backlog priority; mainnet remains blocked."
)
REQUIRED_AUDIT_TRAIL = [
    "load-pinned-305-evidence",
    "verify-305-consumed-303",
    "verify-301-299-297-295-293-291-lineage",
    "bind-telegram-approval-source",
    "verify-exact-scope-no-escalation",
    "authorize-next-bounded-local-free-lane",
    "keep-mainnet-blocked",
]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_service_approval_intake as intake  # noqa: E402
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
    boundaries = intake.boundary_values()
    boundaries.update(
        {
            "approvalAuthorizationOnly": True,
            "telegramApprovalBound": True,
            "exactBoundedScopeAuthorized": True,
            "realMutationAuthorized": False,
            "mainnetBlocked": True,
        }
    )
    return boundaries


def boundary_findings(boundaries: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field, expected in boundary_values().items():
        if boundaries.get(field) is not expected:
            findings.append(finding(f"{prefix}.{field}", f"{field} must be {str(expected).lower()}."))
    return findings


def accepted_305_result(doc: dict[str, Any]) -> dict[str, Any] | None:
    for result in doc.get("results", []):
        if result.get("id") == "approval-intake-absent-response-hold-pass":
            return result
    return None


def prior_305_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("mode") != "beta-external-service-approval-intake":
        findings.append(finding("prior305Fixture.mode", "Pinned #305 fixture must be the approval-intake package."))
    if doc.get("issue") != 305 or doc.get("parentEpic") != 220:
        findings.append(finding("prior305Fixture.issue", "Pinned #305 fixture must belong to issue #305 and parent #220."))
    if doc.get("follows") != [303, 301, 299, 297, 295, 293, 291, 289, 287, 285]:
        findings.append(finding("prior305Fixture.follows", "Pinned #305 fixture must preserve #303/#301/#299/#297/#295/#293/#291 lineage."))
    if doc.get("status") != "pass":
        findings.append(finding("prior305Fixture.status", "Pinned #305 fixture must pass."))
    findings.extend(intake.false_boundary_findings(doc.get("boundaries", {}), "prior305Fixture.boundaries"))
    result = accepted_305_result(doc)
    if not result:
        findings.append(finding("prior305Fixture.results", "Pinned #305 fixture must include the accepted absent-response hold result."))
        return findings
    evidence = result.get("runEvidence", {})
    if result.get("status") != "pass" or result.get("verdict") != "hold-fail-closed":
        findings.append(finding("prior305Fixture.results.verdict", "Accepted #305 result must pass with hold-fail-closed verdict."))
    if evidence.get("approvalPrompt") != intake.REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("prior305Fixture.results.approvalPrompt", "Accepted #305 prompt must remain exact."))
    prior303 = evidence.get("prior303Evidence", {})
    if (
        prior303.get("fixture", {}).get("path") != intake.PINNED_303_FIXTURE_PATH
        or prior303.get("fixture", {}).get("sha256") != intake.PINNED_303_FIXTURE_SHA256
        or prior303.get("fixture", {}).get("hashMatches") is not True
    ):
        findings.append(finding("prior305Fixture.results.prior303Evidence.fixture", "Accepted #305 evidence must consume pinned #303 evidence."))
    lineage = {
        "prior301Fixture": intake.micro_gate.PINNED_301_FIXTURE_SHA256,
        "prior299Fixture": intake.micro_gate.bounded_gate.PINNED_299_FIXTURE_SHA256,
        "prior297Fixture": intake.micro_gate.bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256,
        "prior295Fixture": intake.micro_gate.bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256,
        "prior293Fixture": intake.micro_gate.bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256,
        "approvalPacketFixture": intake.micro_gate.bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256,
    }
    for key, expected_sha in lineage.items():
        if prior303.get(key, {}).get("sha256") != expected_sha:
            findings.append(finding(f"prior305Fixture.results.prior303Evidence.{key}", f"Accepted #305 evidence must preserve pinned {key} lineage."))
    decision = evidence.get("approveOrHoldDecision", {})
    if decision.get("decision") != "hold-fail-closed" or decision.get("liveActionAuthorized") is not False:
        findings.append(finding("prior305Fixture.results.approveOrHoldDecision", "Accepted #305 evidence must hold before fresh external approval."))
    return findings


def approval_findings(approval: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if approval.get("status") != "approved":
        findings.append(finding("telegramApproval.status", "Fresh Nissan approval must be approved."))
    if approval.get("approver") != "Nissan":
        findings.append(finding("telegramApproval.approver", "Approver must be Nissan."))
    if approval.get("source") != REQUIRED_APPROVAL_SOURCE:
        findings.append(finding("telegramApproval.source", f"Approval source must be `{REQUIRED_APPROVAL_SOURCE}`."))
    if approval.get("timestamp") != REQUIRED_APPROVAL_TIMESTAMP:
        findings.append(finding("telegramApproval.timestamp", f"Approval timestamp must be `{REQUIRED_APPROVAL_TIMESTAMP}`."))
    if approval.get("responseText") != REQUIRED_APPROVAL_TEXT:
        findings.append(finding("telegramApproval.responseText", "Approval text must match the captured Telegram message exactly."))
    if approval.get("fresh") is not True:
        findings.append(finding("telegramApproval.fresh", "Approval must be fresh for this post-#305 authorization."))
    if approval.get("prompt") != intake.REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("telegramApproval.prompt", "Approval must bind to the exact #303/#305 prompt."))
    if approval.get("scope") != REQUIRED_APPROVAL_SCOPE:
        findings.append(finding("telegramApproval.scope", f"Approval scope must be `{REQUIRED_APPROVAL_SCOPE}`."))
    for field in ("providerEscalation", "productionEscalation", "devnetEscalation", "mainnetEscalation", "costEscalation", "privacyEscalation", "legalEscalation"):
        if approval.get(field) is not False:
            findings.append(finding(f"telegramApproval.{field}", f"{field} must be false."))
    lowered = str(approval.get("responseText") or "").lower()
    if "approval" not in lowered and "approve" not in lowered:
        findings.append(finding("telegramApproval.responseText", "Approval text must explicitly approve."))
    return findings


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if scenario.get("authorizationId") != REQUIRED_AUTHORIZATION_ID:
        findings.append(finding("authorizationId", f"Authorization id must be `{REQUIRED_AUTHORIZATION_ID}`."))
    if scenario.get("releaseId") != REQUIRED_RELEASE_ID:
        findings.append(finding("releaseId", f"Release id must be `{REQUIRED_RELEASE_ID}`."))
    if scenario.get("releaseCandidateId") != REQUIRED_RELEASE_CANDIDATE_ID:
        findings.append(finding("releaseCandidateId", f"Release candidate id must be `{REQUIRED_RELEASE_CANDIDATE_ID}`."))
    if scenario.get("sourceMergeCommit") != PINNED_305_MERGE_COMMIT:
        findings.append(finding("sourceMergeCommit", f"Source merge commit must be `{PINNED_305_MERGE_COMMIT}`."))
    hashes = expected_hash_map(scenario)
    if scenario.get("priorEvidenceFixturePath") != PINNED_305_FIXTURE_PATH or hashes.get(PINNED_305_FIXTURE_PATH) != PINNED_305_FIXTURE_SHA256:
        findings.append(finding("prior305Fixture.expectedSha256", "Prior #305 fixture path and sha256 must be pinned from the merge commit."))
    if scenario.get("priorEvidenceReportPath") != PINNED_305_REPORT_PATH or hashes.get(PINNED_305_REPORT_PATH) != PINNED_305_REPORT_SHA256:
        findings.append(finding("prior305Report.expectedSha256", "Prior #305 report path and sha256 must be pinned from the merge commit."))
    if scenario.get("approvalPrompt") != intake.REQUIRED_APPROVAL_PROMPT:
        findings.append(finding("approvalPrompt", "Approval prompt must be exact."))
    if scenario.get("authorizationCommand") != REQUIRED_AUTHORIZATION_COMMAND:
        findings.append(finding("authorizationCommand", "Authorization command must be the pinned local generator."))
    findings.extend(gate.command_findings([scenario.get("authorizationCommand", "")], "authorizationCommand"))
    findings.extend(approval_findings(scenario.get("telegramApproval", {})))
    scope = scenario.get("boundedScope", {})
    if (
        scope.get("sourceIssue") != 303
        or scope.get("adlPath") != gate.REQUIRED_ADL_PATH
        or scope.get("scope") != "local/free/bounded approval only"
        or scope.get("providerEscalation") is not False
        or scope.get("devnetEscalation") is not False
        or scope.get("mainnetEscalation") is not False
        or scope.get("estimatedCostUsd") != "0.00"
    ):
        findings.append(finding("boundedScope", "Bounded scope must match #303 exactly and reject escalation."))
    for field in intake.UNSAFE_FLAG_FIELDS:
        if scenario.get(field) not in (None, False):
            findings.append(finding(field, f"{field} must be false or absent in this authorization package."))
    if scenario.get("kind") == "positive" and scenario.get("expectedVerdict") != REQUIRED_VERDICT:
        findings.append(finding("expectedVerdict", "Expected verdict must approve only the exact bounded scope."))
    if scenario.get("expectedRiskVerdict") != REQUIRED_RISK_VERDICT:
        findings.append(finding("expectedRiskVerdict", "Expected risk verdict must keep approval bounded and mainnet blocked."))
    if scenario.get("auditTrail") != REQUIRED_AUDIT_TRAIL:
        findings.append(finding("auditTrail", "Audit trail must bind #305 evidence, Telegram approval, exact scope, and mainnet block."))
    if scenario.get("nextStepCue") != REQUIRED_NEXT_STEP_CUE:
        findings.append(finding("nextStepCue", "Next-step cue must stay bounded and preserve mainnet block."))
    findings.extend(intake.micro_gate.bounded_gate.operator_run.smoke.sensitive_payload_findings(scenario, "scenario"))
    findings.extend(intake.micro_gate.bounded_gate.operator_run.smoke.unsafe_claim_findings(scenario, "scenario"))
    return findings


def build_run_evidence(
    scenario: dict[str, Any],
    prior_doc: dict[str, Any],
    fixture_binding: dict[str, Any],
    report_binding: dict[str, Any],
    commit: str,
) -> dict[str, Any]:
    accepted = accepted_305_result(prior_doc) or {}
    prior_evidence = accepted.get("runEvidence", {}) if isinstance(accepted.get("runEvidence", {}), dict) else {}
    return {
        "authorizationId": scenario.get("authorizationId"),
        "sourceCommit": commit,
        "sourceMergeCommit": scenario.get("sourceMergeCommit"),
        "prior305Evidence": {
            "fixture": fixture_binding,
            "report": report_binding,
            "acceptedResultId": accepted.get("id"),
            "acceptedVerdict": accepted.get("verdict"),
            "prior303Fixture": prior_evidence.get("prior303Evidence", {}).get("fixture", {}),
            "prior301Fixture": prior_evidence.get("prior303Evidence", {}).get("prior301Fixture", {}),
            "prior299Fixture": prior_evidence.get("prior303Evidence", {}).get("prior299Fixture", {}),
            "prior297Fixture": prior_evidence.get("prior303Evidence", {}).get("prior297Fixture", {}),
            "prior295Fixture": prior_evidence.get("prior303Evidence", {}).get("prior295Fixture", {}),
            "prior293Fixture": prior_evidence.get("prior303Evidence", {}).get("prior293Fixture", {}),
            "approvalPacketFixture": prior_evidence.get("prior303Evidence", {}).get("approvalPacketFixture", {}),
            "approvalPrompt": prior_evidence.get("approvalPrompt"),
        },
        "approvalPrompt": scenario.get("approvalPrompt"),
        "telegramApproval": scenario.get("telegramApproval", {}),
        "boundedScope": scenario.get("boundedScope", {}),
        "authorizationDecision": {
            "decision": REQUIRED_VERDICT,
            "scope": REQUIRED_APPROVAL_SCOPE,
            "nextBoundedLaneAuthorized": True,
            "realMutationAuthorizedByThisArtifact": False,
            "mainnetAuthorized": False,
        },
        "auditTrail": scenario.get("auditTrail", []),
        "nextStepCue": scenario.get("nextStepCue"),
        "riskVerdict": REQUIRED_RISK_VERDICT,
        "boundaries": boundary_values(),
    }


def build_result(scenario: dict[str, Any], commit: str) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    hashes = expected_hash_map(scenario)
    fixture_binding = gate.artifact_binding(PINNED_305_FIXTURE_PATH, hashes.get(PINNED_305_FIXTURE_PATH, ""), "prior305Fixture", findings)
    report_binding = gate.artifact_binding(PINNED_305_REPORT_PATH, hashes.get(PINNED_305_REPORT_PATH, ""), "prior305Report", findings)
    prior_doc = gate.load_artifact(PINNED_305_FIXTURE_PATH, "prior305Fixture", findings)
    findings.extend(prior_305_findings(prior_doc))
    status = "pass" if not findings else "fail"
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "verdict": REQUIRED_VERDICT if status == "pass" else "hold-fail-closed",
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
        "mode": "beta-external-service-approval-authorization",
        "issue": 307,
        "parentEpic": 220,
        "follows": [305, 303, 301, 299, 297, 295, 293, 291, 289, 287, 285],
        "status": "pass" if not mismatches else "fail",
        "sourceCommit": actual_commit,
        "releaseId": doc.get("releaseId"),
        "findings": mismatches,
        "summary": {
            "approveDecisions": sum(1 for result in results if result["verdict"] == REQUIRED_VERDICT),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "boundaries": boundary_values(),
        "mainnetStatement": "This authorization does not approve or run mainnet; mainnet remains blocked until separate fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS), help="Approval authorization scenario JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the generated authorization JSON.")
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
