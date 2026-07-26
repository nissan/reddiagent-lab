#!/usr/bin/env python3
"""Build deterministic RAP receipt-integrity benchmark evidence."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from rap_receipt_validator import validate_receipt  # noqa: E402

ROOT = SCRIPTS_DIR.parent
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

# Structurally real passing receipt: every threat case below mutates this
# data so the defect is exhibited by the receipt itself, and
# scripts/rap_receipt_validator.py computes the decision from it.
PASS_RECEIPT = {
    "receiptId": "rcpt-375-0001",
    "finalizedAt": "2026-07-26T03:00:00Z",
    "request": {
        "requestId": "req-375-0001",
        "requestHash": "sha256:req-375-0001",
        "purpose": "market-data-lookup",
        "toolName": "market_data.quote",
        "resourceScope": "mcp:market-data:quote:read",
    },
    "delegatedAuthority": {
        "mandateId": "mandate-ap2-0001",
        "principal": "user:principal-0001",
        "spender": "agent:spender-0001",
        "payee": "agent:svc-market-data",
        "purpose": "market-data-lookup",
        "rail": "x402-solana-devnet",
        "maxAmount": 250000,
        "expiresAt": "2026-07-27T00:00:00Z",
        "revoked": False,
        "auditRef": "audit:mandate-ap2-0001",
    },
    "resourceAuthorization": {
        "serverRef": "mcp:server:market-data",
        "toolName": "market_data.quote",
        "authorizationRef": "authz:mcp-0001",
        "scope": "mcp:market-data:quote:read",
    },
    "paymentEvidence": {
        "requiredHash": "sha256:x402-required-0001",
        "payloadHash": "sha256:x402-payload-0001",
        "responseHash": "sha256:x402-response-0001",
        "rail": "x402-solana-devnet",
        "facilitatorRef": "facilitator:devnet-01",
        "payee": "agent:svc-market-data",
        "amount": 120000,
        "boundRequestId": "req-375-0001",
    },
    "settlementProgramProof": {
        "cluster": "devnet",
        "signature": "sig:settlement-0001",
        "mint": "mint:usdc-devnet",
        "programId": "prog:token-2022",
        "confirmationStatus": "confirmed",
        "payer": "wallet:spender-0001",
        "payee": "agent:svc-market-data",
        "amount": 120000,
    },
    "serviceOutcome": {
        "requestHash": "sha256:req-375-0001",
        "responseHash": "sha256:svc-response-0001",
        "status": "success",
        "completedAt": "2026-07-26T02:59:30Z",
        "agentId": "agent:svc-market-data",
    },
    "evalEvidence": {
        "gateId": "gate:service-quality-v1",
        "status": "pass",
        "evaluatorRef": "evaluator:rap-quality-01",
        "reportHash": "sha256:eval-report-0001",
    },
    "replayIdempotency": {
        "receiptId": "rcpt-375-0001",
        "idempotencyKey": "idem-375-0001",
        "requestHash": "sha256:req-375-0001",
        "nonce": "nonce-375-0001",
        "priorPaymentResponseHashes": [],
    },
    "privacyAccounting": {
        "entryRef": "acct:entry-0001",
        "privacyClass": "pii-minimized",
        "joinRefs": [
            "req-375-0001",
            "sha256:x402-response-0001",
            "sig:settlement-0001",
            "sha256:svc-response-0001",
            "sha256:eval-report-0001",
        ],
        "retentionPolicy": "90d-minimized",
    },
    "disputeState": {
        "status": "none",
        "openedAt": None,
        "resolutionRef": None,
    },
    "rollbackHold": {
        "holdState": "none",
        "rollbackRequired": False,
        "killSwitchRef": None,
    },
}


def base_receipt() -> dict[str, Any]:
    return copy.deepcopy(PASS_RECEIPT)


def receipt_without_layer(layer: str) -> dict[str, Any]:
    receipt = base_receipt()
    del receipt[layer]
    return receipt


def receipt_with_fields(layer: str, **fields: Any) -> dict[str, Any]:
    receipt = base_receipt()
    receipt[layer].update(fields)
    return receipt


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
            "receipt": base_receipt(),
            "expectedDecision": "accept",
            "diagnostics": [],
            "proves": "RAP can accept only when payment, authority, resource access, settlement, service, eval, replay, accounting, dispute, and rollback evidence all pass.",
        },
        {
            "id": "payment_service_decoupling",
            "threat": "x402 settlement is present but service result is missing",
            "receipt": receipt_without_layer("serviceOutcome"),
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
            "receipt": receipt_with_fields("delegatedAuthority", purpose="portfolio-rebalance"),
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
            "receipt": receipt_with_fields("delegatedAuthority", payee="", maxAmount=None),
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
            "receipt": receipt_with_fields("privacyAccounting", joinRefs=["req-375-0001"]),
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
            "receipt": receipt_with_fields(
                "replayIdempotency", priorPaymentResponseHashes=["sha256:x402-response-0001"]
            ),
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
            "receipt": receipt_with_fields("delegatedAuthority", expiresAt="2026-07-25T00:00:00Z"),
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
            "receipt": receipt_with_fields(
                "resourceAuthorization", toolName="market_data.trade", scope="mcp:market-data:trade:write"
            ),
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
            "receipt": receipt_with_fields("settlementProgramProof", payee="agent:svc-imposter"),
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
            "receipt": receipt_with_fields("serviceOutcome", status="failed"),
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
            "receipt": receipt_without_layer("paymentEvidence"),
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
            "receipt": receipt_with_fields("evalEvidence", status="failed"),
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
            "receipt": receipt_with_fields("disputeState", status="open", openedAt="2026-07-26T02:30:00Z"),
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
            "receipt": receipt_with_fields(
                "rollbackHold", rollbackRequired=True, holdState="hold", killSwitchRef="ops:kill-switch-0001"
            ),
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
        "validatorScript": "scripts/rap_receipt_validator.py",
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
        # Cross-check the spec against the implementation: the documented
        # expectedDecision must equal what rap_receipt_validator computes
        # from the case's structural receipt, and every documented diagnostic
        # code must be produced by the validator.
        verdict = validate_receipt(case.get("receipt", {}))
        if verdict["decision"] != decision:
            findings.append(
                {
                    "path": f"threatCases.{index}.expectedDecision",
                    "reason": f"Validator computed {verdict['decision']!r} for this receipt.",
                }
            )
        expected_codes = {diag.get("code") for diag in diagnostics}
        computed_codes = {diag["code"] for diag in verdict["diagnostics"]}
        missing_codes = sorted(code for code in expected_codes if code not in computed_codes)
        if missing_codes:
            findings.append(
                {
                    "path": f"threatCases.{index}.diagnostics",
                    "reason": f"Validator did not produce documented codes: {', '.join(missing_codes)}.",
                }
            )
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
