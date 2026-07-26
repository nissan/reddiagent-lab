#!/usr/bin/env python3
"""Build deterministic RAP receipt-integrity benchmark evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = 375
PARENT_EPIC = 220
DATE_CHECKED = "2026-07-26"
FIXTURE = ROOT / "tests" / "fixtures" / "rap-receipt-integrity-benchmark.json"

REQUIRED_LAYERS = (
    "delegatedAuthority",
    "resourceAuthorization",
    "paymentEvidence",
    "settlementProgramProof",
    "serviceOutcome",
    "evalEvidence",
    "replayIdempotency",
    "privacyAccounting",
    "disputeState",
    "rollbackHold",
)

PASS_RECEIPT = {
    "delegatedAuthority": "bound-current-purpose-payee-cap",
    "resourceAuthorization": "resource-scope-match",
    "paymentEvidence": "x402-payment-response-present",
    "settlementProgramProof": "allowed-devnet-signature-confirmed",
    "serviceOutcome": "service-result-pass",
    "evalEvidence": "required-eval-pass",
    "replayIdempotency": "unique-receipt-id-and-idempotency-key",
    "privacyAccounting": "pii-minimized-accounting-ready",
    "disputeState": "not-disputed",
    "rollbackHold": "no-hold-or-rollback-required",
}


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def diagnostic(code: str, category: str, path: str, hint: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "category": category,
        "path": path,
        "remediation": hint,
    }


def threat_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": "valid_full_receipt",
            "threat": "positive full receipt integrity path",
            "receipt": dict(PASS_RECEIPT),
            "expectedDecision": "accept",
            "diagnostics": [],
            "proves": "RAP can accept only when payment, authority, resource access, settlement, service, eval, replay, accounting, dispute, and rollback evidence all pass.",
        },
        {
            "id": "payment_service_decoupling",
            "threat": "x402 settlement is present but service result is missing",
            "receipt": {**PASS_RECEIPT, "serviceOutcome": "missing"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.service_outcome.required",
                    "service",
                    "receipt.serviceOutcome",
                    "Bind settled payment to a concrete service result before accounting or reputation.",
                )
            ],
            "proves": "Payment evidence alone cannot become service success.",
        },
        {
            "id": "valid_authorization_misuse",
            "threat": "valid mandate is reused for the wrong purpose",
            "receipt": {**PASS_RECEIPT, "delegatedAuthority": "purpose-mismatch"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.authority.scope_mismatch",
                    "authority",
                    "receipt.delegatedAuthority",
                    "Require mandate purpose, spender, payee, cap, and expiry to match the receipt.",
                )
            ],
            "proves": "A real authorization cannot be reused outside its bounded intent.",
        },
        {
            "id": "weak_intent_binding",
            "threat": "mandate exists but does not bind payee and cap",
            "receipt": {**PASS_RECEIPT, "delegatedAuthority": "missing-payee-cap-binding"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.authority.weak_binding",
                    "authority",
                    "receipt.delegatedAuthority",
                    "Bind principal, spender, payee, purpose, rail, cap, expiry, and audit reference.",
                )
            ],
            "proves": "Delegated authority must be stronger than a generic payment permission.",
        },
        {
            "id": "limited_accountability",
            "threat": "accounting cannot link request, response, payment, and evaluator",
            "receipt": {**PASS_RECEIPT, "privacyAccounting": "missing-accounting-join"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.accounting.join_required",
                    "accounting",
                    "receipt.privacyAccounting",
                    "Persist privacy-safe request, response, payment, settlement, service, and eval references.",
                )
            ],
            "proves": "Receipt integrity needs accountable joins, not standalone payment records.",
        },
        {
            "id": "replay_duplicate_receipt",
            "threat": "same payment response is replayed under a duplicate receipt",
            "receipt": {**PASS_RECEIPT, "replayIdempotency": "duplicate-payment-response"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.replay.duplicate_payment",
                    "replay",
                    "receipt.replayIdempotency",
                    "Reject duplicate payment response hashes and require stable idempotency keys.",
                )
            ],
            "proves": "A settled payment cannot be counted twice.",
        },
        {
            "id": "stale_scope",
            "threat": "authorization scope expired before receipt finalization",
            "receipt": {**PASS_RECEIPT, "delegatedAuthority": "expired"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.authority.expired",
                    "authority",
                    "receipt.delegatedAuthority",
                    "Reject receipts whose mandate expiry or revocation state is stale.",
                )
            ],
            "proves": "Payment success after expiry cannot revive stale delegated authority.",
        },
        {
            "id": "wrong_resource",
            "threat": "MCP/resource authorization covers a different resource",
            "receipt": {**PASS_RECEIPT, "resourceAuthorization": "resource-mismatch"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.resource.scope_mismatch",
                    "resource",
                    "receipt.resourceAuthorization",
                    "Match protected resource metadata and tool scope to the paid service receipt.",
                )
            ],
            "proves": "Protected resource access stays separate from payment permission.",
        },
        {
            "id": "wrong_merchant_payee",
            "threat": "settlement payee differs from mandate and service merchant",
            "receipt": {**PASS_RECEIPT, "settlementProgramProof": "payee-mismatch"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.settlement.payee_mismatch",
                    "settlement",
                    "receipt.settlementProgramProof",
                    "Require authority payee, x402 accepts entry, and settlement destination to match.",
                )
            ],
            "proves": "Settlement proof must bind to the intended payee or merchant.",
        },
        {
            "id": "failed_service_after_settled_payment",
            "threat": "payment settled but service failed",
            "receipt": {**PASS_RECEIPT, "serviceOutcome": "failed-after-payment"},
            "expectedDecision": "hold",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.service.failed_after_payment",
                    "service",
                    "receipt.serviceOutcome",
                    "Hold accounting and reputation; route the receipt to refund, retry, or dispute handling.",
                )
            ],
            "proves": "Settled payment with failed service is not a successful RAP receipt.",
        },
        {
            "id": "service_returned_without_payment",
            "threat": "service succeeded but payment evidence is absent",
            "receipt": {**PASS_RECEIPT, "paymentEvidence": "missing"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.payment.required",
                    "payment",
                    "receipt.paymentEvidence",
                    "Attach x402/payment evidence before paid-service accounting can pass.",
                )
            ],
            "proves": "Service success alone cannot create payment accounting evidence.",
        },
        {
            "id": "eval_failed_reputation_emission",
            "threat": "service result is present but required evaluator failed",
            "receipt": {**PASS_RECEIPT, "evalEvidence": "failed"},
            "expectedDecision": "reject",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.eval.failed",
                    "eval",
                    "receipt.evalEvidence",
                    "Block reputation and acceptance until required evaluation gates pass.",
                )
            ],
            "proves": "Reputation eligibility requires evaluation evidence, not just payment and service completion.",
        },
        {
            "id": "disputed_receipt",
            "threat": "receipt has an open dispute",
            "receipt": {**PASS_RECEIPT, "disputeState": "open"},
            "expectedDecision": "hold",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.dispute.open",
                    "dispute",
                    "receipt.disputeState",
                    "Hold final accounting and reputation until dispute resolution closes.",
                )
            ],
            "proves": "Disputed receipts cannot close accounting or reputation.",
        },
        {
            "id": "rollback_required",
            "threat": "rollback or kill-switch criteria are active",
            "receipt": {**PASS_RECEIPT, "rollbackHold": "rollback-required"},
            "expectedDecision": "hold",
            "diagnostics": [
                diagnostic(
                    "rap_receipt.rollback.required",
                    "rollback",
                    "receipt.rollbackHold",
                    "Preserve hold evidence and block acceptance while rollback criteria are active.",
                )
            ],
            "proves": "Operational rollback or kill-switch state overrides payment settlement.",
        },
    ]


def layer_requirements() -> list[dict[str, Any]]:
    return [
        {
            "layer": "delegatedAuthority",
            "positiveEvidence": "Bound AP2/FIDO/Verifiable Intent mandate with principal, spender, payee, purpose, rail, cap, expiry, revocation, and audit reference.",
            "cannotSubstitute": ["paymentEvidence", "resourceAuthorization", "settlementProgramProof"],
            "stableFields": ["authority.mandateId", "authority.principal", "authority.payee", "authority.scope", "authority.maxAmount", "authority.expiresAt"],
        },
        {
            "layer": "resourceAuthorization",
            "positiveEvidence": "Protected-resource authorization for the exact service/tool/resource scope.",
            "cannotSubstitute": ["delegatedAuthority", "paymentEvidence"],
            "stableFields": ["resource.serverRef", "resource.toolName", "resource.authorizationRef", "resource.scope"],
        },
        {
            "layer": "paymentEvidence",
            "positiveEvidence": "x402/payment challenge, payload, selected rail, response, and facilitator verification references.",
            "cannotSubstitute": ["delegatedAuthority", "serviceOutcome", "evalEvidence", "reputationEligibility"],
            "stableFields": ["payment.requiredHash", "payment.payloadHash", "payment.responseHash", "payment.rail", "payment.facilitatorRef"],
        },
        {
            "layer": "settlementProgramProof",
            "positiveEvidence": "Environment, mint, program, payer, payee, amount, signature, and confirmation proof against allowlists.",
            "cannotSubstitute": ["serviceOutcome", "delegatedAuthority", "disputeState"],
            "stableFields": ["settlement.cluster", "settlement.signature", "settlement.mint", "settlement.programId", "settlement.confirmationStatus"],
        },
        {
            "layer": "serviceOutcome",
            "positiveEvidence": "Service result hash, status, completed-at timestamp, and resource response reference.",
            "cannotSubstitute": ["paymentEvidence", "settlementProgramProof"],
            "stableFields": ["service.requestHash", "service.responseHash", "service.status", "service.completedAt"],
        },
        {
            "layer": "evalEvidence",
            "positiveEvidence": "Required evaluator gate result for service quality and policy acceptance.",
            "cannotSubstitute": ["paymentEvidence", "serviceOutcome"],
            "stableFields": ["eval.gateId", "eval.status", "eval.evaluatorRef", "eval.reportHash"],
        },
        {
            "layer": "replayIdempotency",
            "positiveEvidence": "Unique receipt id, request hash, idempotency key, nonce, and duplicate-payment rejection.",
            "cannotSubstitute": ["settlementProgramProof"],
            "stableFields": ["receipt.id", "receipt.idempotencyKey", "receipt.requestHash", "receipt.nonce"],
        },
        {
            "layer": "privacyAccounting",
            "positiveEvidence": "Privacy-minimized accounting refs that can join receipt, payment, settlement, service, and eval evidence.",
            "cannotSubstitute": ["paymentEvidence"],
            "stableFields": ["accounting.entryRef", "accounting.privacyClass", "accounting.joinRefs", "accounting.retentionPolicy"],
        },
        {
            "layer": "disputeState",
            "positiveEvidence": "Closed/clear dispute state before final acceptance or reputation emission.",
            "cannotSubstitute": ["paymentEvidence", "evalEvidence"],
            "stableFields": ["dispute.status", "dispute.openedAt", "dispute.resolutionRef"],
        },
        {
            "layer": "rollbackHold",
            "positiveEvidence": "No rollback, hold, kill-switch, or refund/retry criteria active.",
            "cannotSubstitute": ["paymentEvidence", "serviceOutcome"],
            "stableFields": ["ops.holdState", "ops.rollbackRequired", "ops.killSwitchRef"],
        },
    ]


def boundaries() -> dict[str, bool]:
    return {
        "staticDeterministicBenchmark": True,
        "fixtureReportOnly": True,
        "liveNetwork": False,
        "walletAccess": False,
        "paymentFacilitatorSettlementAction": False,
        "mcpProviderInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "externalTesterExecution": False,
        "deployment": False,
        "credentialAccess": False,
        "spend": False,
        "mainnetBlockedUntilOfficialAuditAndExplicitGoLive": True,
    }


def build_doc() -> dict[str, Any]:
    cases = threat_cases()
    diagnostics = [diag for case in cases for diag in case["diagnostics"]]
    return {
        "mode": "rap-receipt-integrity-benchmark",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "dateChecked": DATE_CHECKED,
        "status": "pass",
        "decision": "receipt-integrity-benchmark-ready-for-static-compatibility-reports",
        "consumes": {
            "issues": [374, 361, 365, 366],
            "fixtures": [
                "tests/fixtures/agent-payments-standards-alignment-refresh.json",
                "tests/fixtures/rap-x402-ap2-audit-prep-alignment-packet.json",
                "tests/fixtures/beta-external-tester-mvp-packet.json",
                "tests/fixtures/smart-contract-audit-readiness-freeze-packet.json",
            ],
        },
        "threatCaseCount": len(cases),
        "negativeThreatCaseCount": sum(1 for case in cases if case["expectedDecision"] != "accept"),
        "diagnosticCount": len(diagnostics),
        "requiredLayers": list(REQUIRED_LAYERS),
        "layerRequirements": layer_requirements(),
        "threatCases": cases,
        "stableDiagnosticContract": ["code", "severity", "category", "path", "remediation"],
        "receiptIntegrityRule": "RAP acceptance requires all layers to pass; x402/payment settlement alone cannot become service success, delegated authority, reputation eligibility, dispute closure, or accounting acceptance.",
        "nextIssue": {
            "issue": 376,
            "title": "Add static Pay.sh/x402 discovery compatibility report",
            "status": "queued-after-375",
        },
        "docsRefresh": {
            "issue": 206,
            "status": "keep-docs-only-until-taxonomy-or-first-implementation-wave-justifies-refresh",
        },
        "boundaries": boundaries(),
    }


def collect_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if doc.get("issue") != CURRENT_ISSUE:
        findings.append({"path": "issue", "reason": f"Expected issue {CURRENT_ISSUE}."})
    if doc.get("parentEpic") != PARENT_EPIC:
        findings.append({"path": "parentEpic", "reason": f"Expected parent epic {PARENT_EPIC}."})
    if doc.get("requiredLayers") != list(REQUIRED_LAYERS):
        findings.append({"path": "requiredLayers", "reason": "Required receipt-integrity layer order changed."})
    layers = {row.get("layer") for row in doc.get("layerRequirements", [])}
    for layer in REQUIRED_LAYERS:
        if layer not in layers:
            findings.append({"path": f"layerRequirements.{layer}", "reason": "Missing layer requirement."})
    cases = doc.get("threatCases", [])
    if len(cases) < 14:
        findings.append({"path": "threatCases", "reason": "Expected at least 14 threat cases."})
    required_case_ids = {
        "payment_service_decoupling",
        "valid_authorization_misuse",
        "weak_intent_binding",
        "limited_accountability",
        "replay_duplicate_receipt",
        "stale_scope",
        "wrong_resource",
        "wrong_merchant_payee",
        "failed_service_after_settled_payment",
        "service_returned_without_payment",
        "eval_failed_reputation_emission",
        "disputed_receipt",
        "rollback_required",
    }
    case_ids = {case.get("id") for case in cases}
    for case_id in required_case_ids:
        if case_id not in case_ids:
            findings.append({"path": f"threatCases.{case_id}", "reason": "Missing required threat case."})
    for index, case in enumerate(cases):
        decision = case.get("expectedDecision")
        diagnostics = case.get("diagnostics", [])
        if decision not in {"accept", "reject", "hold"}:
            findings.append({"path": f"threatCases.{index}.expectedDecision", "reason": "Unexpected decision."})
        if decision != "accept" and not diagnostics:
            findings.append({"path": f"threatCases.{index}.diagnostics", "reason": "Negative/hold cases require diagnostics."})
        for diag in diagnostics:
            for key in doc.get("stableDiagnosticContract", []):
                if not diag.get(key):
                    findings.append({"path": f"threatCases.{index}.diagnostics.{key}", "reason": "Stable diagnostic field missing."})
    rule = doc.get("receiptIntegrityRule", "")
    for phrase in (
        "x402/payment settlement alone cannot become service success",
        "delegated authority",
        "reputation eligibility",
        "dispute closure",
        "accounting acceptance",
    ):
        if phrase not in rule:
            findings.append({"path": "receiptIntegrityRule", "reason": f"Missing rule phrase: {phrase}"})
    if doc.get("nextIssue", {}).get("issue") != 376:
        findings.append({"path": "nextIssue.issue", "reason": "Expected #376 as next issue."})
    if "keep-docs-only" not in doc.get("docsRefresh", {}).get("status", ""):
        findings.append({"path": "docsRefresh.status", "reason": "#206 docs refresh should remain deferred."})
    for key, expected in boundaries().items():
        if doc.get("boundaries", {}).get(key) is not expected:
            findings.append({"path": f"boundaries.{key}", "reason": f"Expected {expected!r}."})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write the fixture instead of printing JSON.")
    args = parser.parse_args()

    doc = build_doc()
    findings = collect_findings(doc)
    doc["findings"] = findings
    doc["status"] = "pass" if not findings else "fail"
    output = dump_json(doc)
    if args.write:
        FIXTURE.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
