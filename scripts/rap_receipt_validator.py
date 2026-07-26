#!/usr/bin/env python3
"""RAP receipt-integrity validator.

Computes an accept/reject/hold decision for a structured RAP receipt across
the ten evidence layers defined by ``scripts/rap_receipt_integrity_benchmark.py``,
using the same stable ``rap_receipt.*`` diagnostic codes. The validator is
pure and deterministic: no network, no wall-clock reads — expiry is judged
against the receipt's own ``finalizedAt`` field.

Enforced properties:

- All ten evidence layers must be present and structurally valid.
- Non-substitutability: settlement/payment evidence alone can never produce
  accept for service success, reputation eligibility, dispute closure, or
  accounting acceptance (missing layers reject).
- Replay protection: payment proof is bound to a single request id, and a
  payment response hash already recorded in the replay ledger rejects.
- Delegated-authority scope: purpose must match the request intent, the
  mandate must not be revoked, and ``expiresAt`` must not predate
  ``finalizedAt``.
- Payee binding: payment, settlement, and service-agent payees must match the
  mandate payee, and the paid amount must not exceed the mandate cap.
- Eval-failed receipts cannot yield a reputation-eligible accept.
- Open disputes and active rollback/hold/kill-switch state produce hold.

Academic anchors: arXiv 2607.19545 (USENIX Sec 2026), arXiv 2605.11781
(paid-but-denied), arXiv 2602.06345 (consume-once + context binding).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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

LAYER_CATEGORY = {
    "delegatedAuthority": "authority",
    "resourceAuthorization": "resource",
    "paymentEvidence": "payment",
    "settlementProgramProof": "settlement",
    "serviceOutcome": "service",
    "evalEvidence": "eval",
    "replayIdempotency": "replay",
    "privacyAccounting": "accounting",
    "disputeState": "dispute",
    "rollbackHold": "rollback",
}

MISSING_LAYER_CODES = {
    "serviceOutcome": "rap_receipt.service_outcome.required",
    "paymentEvidence": "rap_receipt.payment.required",
    # Distinct from rap_receipt.rollback.required (an active hold state):
    # a receipt with no rollback/hold evidence layer at all is a reject.
    "rollbackHold": "rap_receipt.rollback.evidence_required",
}

REQUIRED_LAYER_FIELDS: dict[str, tuple[str, ...]] = {
    "delegatedAuthority": (
        "mandateId",
        "principal",
        "spender",
        "payee",
        "purpose",
        "rail",
        "maxAmount",
        "expiresAt",
        "auditRef",
    ),
    "resourceAuthorization": ("serverRef", "toolName", "authorizationRef", "scope"),
    "paymentEvidence": (
        "requiredHash",
        "payloadHash",
        "responseHash",
        "rail",
        "facilitatorRef",
        "payee",
        "amount",
        "boundRequestId",
    ),
    "settlementProgramProof": (
        "cluster",
        "signature",
        "mint",
        "programId",
        "confirmationStatus",
        "payer",
        "payee",
        "amount",
    ),
    "serviceOutcome": ("requestHash", "responseHash", "status", "completedAt", "agentId"),
    "evalEvidence": ("gateId", "status", "evaluatorRef", "reportHash"),
    "replayIdempotency": (
        "receiptId",
        "idempotencyKey",
        "requestHash",
        "nonce",
        "priorPaymentResponseHashes",
    ),
    "privacyAccounting": ("entryRef", "privacyClass", "joinRefs", "retentionPolicy"),
    "disputeState": ("status",),
    "rollbackHold": ("holdState", "rollbackRequired"),
}

REQUIRED_REQUEST_FIELDS = ("requestId", "requestHash", "purpose", "toolName", "resourceScope")

# Layers whose evidence can never substitute for the listed layers/outcomes.
# Mirrors layer_requirements() in scripts/rap_receipt_integrity_benchmark.py.
NON_SUBSTITUTABLE: dict[str, tuple[str, ...]] = {
    "delegatedAuthority": ("paymentEvidence", "resourceAuthorization", "settlementProgramProof"),
    "resourceAuthorization": ("delegatedAuthority", "paymentEvidence"),
    "paymentEvidence": ("delegatedAuthority", "serviceOutcome", "evalEvidence", "reputationEligibility"),
    "settlementProgramProof": ("serviceOutcome", "delegatedAuthority", "disputeState"),
    "serviceOutcome": ("paymentEvidence", "settlementProgramProof"),
    "evalEvidence": ("paymentEvidence", "serviceOutcome"),
    "replayIdempotency": ("settlementProgramProof",),
    "privacyAccounting": ("paymentEvidence",),
    "disputeState": ("paymentEvidence", "evalEvidence"),
    "rollbackHold": ("paymentEvidence", "serviceOutcome"),
}

# Diagnostics whose worst outcome is hold rather than reject.
HOLD_CODES = frozenset(
    {
        "rap_receipt.service.failed_after_payment",
        "rap_receipt.dispute.open",
        "rap_receipt.rollback.required",
    }
)

CLEAR_DISPUTE_STATUSES = frozenset({"none", "closed"})


def _diagnostic(code: str, message: str, layer: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "layer": layer, "path": path}


def _missing_fields(layer_value: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [
        field
        for field in fields
        if field not in layer_value or layer_value[field] is None or layer_value[field] == ""
    ]


def _valid_layer(receipt: dict[str, Any], layer: str) -> dict[str, Any] | None:
    """Return the layer dict when present and structurally complete, else None."""
    value = receipt.get(layer)
    if not isinstance(value, dict):
        return None
    if _missing_fields(value, REQUIRED_LAYER_FIELDS[layer]):
        return None
    return value


def _structural_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    request = receipt.get("request")
    if not isinstance(request, dict) or _missing_fields(request, REQUIRED_REQUEST_FIELDS):
        diagnostics.append(
            _diagnostic(
                "rap_receipt.envelope.required",
                "Receipt must carry a request envelope with id, hash, purpose, tool, and resource scope.",
                "envelope",
                "receipt.request",
            )
        )
    if not isinstance(receipt.get("finalizedAt"), str) or not receipt.get("finalizedAt"):
        diagnostics.append(
            _diagnostic(
                "rap_receipt.envelope.required",
                "Receipt must carry a finalizedAt timestamp for deterministic expiry checks.",
                "envelope",
                "receipt.finalizedAt",
            )
        )
    for layer in REQUIRED_LAYERS:
        category = LAYER_CATEGORY[layer]
        value = receipt.get(layer)
        if not isinstance(value, dict):
            code = MISSING_LAYER_CODES.get(layer, f"rap_receipt.{category}.required")
            diagnostics.append(
                _diagnostic(
                    code,
                    f"Evidence layer {layer} must be present as a structured object.",
                    category,
                    f"receipt.{layer}",
                )
            )
            continue
        missing = _missing_fields(value, REQUIRED_LAYER_FIELDS[layer])
        if not missing:
            continue
        if layer == "delegatedAuthority" and any(field in ("payee", "maxAmount") for field in missing):
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.authority.weak_binding",
                    "Delegated authority must bind payee and spend cap, not just a generic payment permission.",
                    "authority",
                    "receipt.delegatedAuthority",
                )
            )
            missing = [field for field in missing if field not in ("payee", "maxAmount")]
        if layer == "privacyAccounting" and "joinRefs" in missing:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.accounting.join_required",
                    "Accounting must persist join references across request, payment, settlement, service, and eval evidence.",
                    "accounting",
                    "receipt.privacyAccounting.joinRefs",
                )
            )
            missing = [field for field in missing if field != "joinRefs"]
        if missing:
            diagnostics.append(
                _diagnostic(
                    f"rap_receipt.{category}.invalid",
                    f"Evidence layer {layer} is missing required fields: {', '.join(sorted(missing))}.",
                    category,
                    f"receipt.{layer}",
                )
            )
    return diagnostics


def _authority_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    authority = _valid_layer(receipt, "delegatedAuthority")
    request = receipt.get("request")
    finalized_at = receipt.get("finalizedAt")
    if authority is None or not isinstance(request, dict):
        return diagnostics
    if request.get("purpose") and authority["purpose"] != request["purpose"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.authority.scope_mismatch",
                f"Mandate purpose {authority['purpose']!r} does not match request purpose {request['purpose']!r}.",
                "authority",
                "receipt.delegatedAuthority.purpose",
            )
        )
    if authority.get("revoked"):
        diagnostics.append(
            _diagnostic(
                "rap_receipt.authority.expired",
                "Mandate is revoked; settled payment cannot revive stale delegated authority.",
                "authority",
                "receipt.delegatedAuthority.revoked",
            )
        )
    elif isinstance(finalized_at, str) and finalized_at and authority["expiresAt"] < finalized_at:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.authority.expired",
                f"Mandate expired at {authority['expiresAt']} before receipt finalization at {finalized_at}.",
                "authority",
                "receipt.delegatedAuthority.expiresAt",
            )
        )
    return diagnostics


def _resource_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    resource = _valid_layer(receipt, "resourceAuthorization")
    request = receipt.get("request")
    if resource is None or not isinstance(request, dict):
        return []
    if resource["toolName"] != request.get("toolName") or resource["scope"] != request.get("resourceScope"):
        return [
            _diagnostic(
                "rap_receipt.resource.scope_mismatch",
                "Resource authorization covers a different tool or scope than the paid request.",
                "resource",
                "receipt.resourceAuthorization",
            )
        ]
    return []


def _payee_binding_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    authority = _valid_layer(receipt, "delegatedAuthority")
    if authority is None:
        return diagnostics
    expected_payee = authority["payee"]
    for layer, field, path in (
        ("paymentEvidence", "payee", "receipt.paymentEvidence.payee"),
        ("settlementProgramProof", "payee", "receipt.settlementProgramProof.payee"),
        ("serviceOutcome", "agentId", "receipt.serviceOutcome.agentId"),
    ):
        value = _valid_layer(receipt, layer)
        if value is not None and value[field] != expected_payee:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.settlement.payee_mismatch",
                    f"{layer}.{field} {value[field]!r} does not match mandate payee {expected_payee!r}.",
                    "settlement",
                    path,
                )
            )
    payment = _valid_layer(receipt, "paymentEvidence")
    if payment is not None and isinstance(payment["amount"], (int, float)) and isinstance(
        authority["maxAmount"], (int, float)
    ):
        if payment["amount"] > authority["maxAmount"]:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.authority.scope_mismatch",
                    f"Paid amount {payment['amount']} exceeds mandate cap {authority['maxAmount']}.",
                    "authority",
                    "receipt.paymentEvidence.amount",
                )
            )
    return diagnostics


def _replay_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    payment = _valid_layer(receipt, "paymentEvidence")
    replay = _valid_layer(receipt, "replayIdempotency")
    request = receipt.get("request")
    if payment is None:
        return diagnostics
    if replay is not None:
        prior = replay["priorPaymentResponseHashes"]
        if isinstance(prior, list) and payment["responseHash"] in prior:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.replay.duplicate_payment",
                    "Payment response hash already appears in the replay ledger; a settled payment cannot be counted twice.",
                    "replay",
                    "receipt.replayIdempotency.priorPaymentResponseHashes",
                )
            )
    if isinstance(request, dict) and request.get("requestId") and payment["boundRequestId"] != request["requestId"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.replay.duplicate_payment",
                f"Payment proof is bound to request {payment['boundRequestId']!r}, not this receipt's request {request['requestId']!r}.",
                "replay",
                "receipt.paymentEvidence.boundRequestId",
            )
        )
    return diagnostics


def _accounting_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    accounting = _valid_layer(receipt, "privacyAccounting")
    if accounting is None or not isinstance(accounting["joinRefs"], list):
        return []
    join_refs = accounting["joinRefs"]
    request = receipt.get("request")
    required_refs: list[str] = []
    if isinstance(request, dict) and request.get("requestId"):
        required_refs.append(request["requestId"])
    for layer, field in (
        ("paymentEvidence", "responseHash"),
        ("settlementProgramProof", "signature"),
        ("serviceOutcome", "responseHash"),
        ("evalEvidence", "reportHash"),
    ):
        value = _valid_layer(receipt, layer)
        if value is not None:
            required_refs.append(value[field])
    missing = sorted(ref for ref in required_refs if ref not in join_refs)
    if missing:
        return [
            _diagnostic(
                "rap_receipt.accounting.join_required",
                f"Accounting joinRefs cannot link all evidence; missing references: {', '.join(missing)}.",
                "accounting",
                "receipt.privacyAccounting.joinRefs",
            )
        ]
    return []


def _outcome_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    service = _valid_layer(receipt, "serviceOutcome")
    if service is not None and service["status"] != "success":
        diagnostics.append(
            _diagnostic(
                "rap_receipt.service.failed_after_payment",
                f"Service status is {service['status']!r} after settled payment; hold for refund, retry, or dispute handling.",
                "service",
                "receipt.serviceOutcome.status",
            )
        )
    evaluation = _valid_layer(receipt, "evalEvidence")
    if evaluation is not None and evaluation["status"] != "pass":
        diagnostics.append(
            _diagnostic(
                "rap_receipt.eval.failed",
                "Required evaluation gate did not pass; the receipt cannot become reputation-eligible.",
                "eval",
                "receipt.evalEvidence.status",
            )
        )
    dispute = _valid_layer(receipt, "disputeState")
    if dispute is not None and dispute["status"] not in CLEAR_DISPUTE_STATUSES:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.dispute.open",
                f"Dispute state is {dispute['status']!r}; hold accounting and reputation until resolution closes.",
                "dispute",
                "receipt.disputeState.status",
            )
        )
    ops = _valid_layer(receipt, "rollbackHold")
    if ops is not None and (ops["rollbackRequired"] or ops["holdState"] != "none" or ops.get("killSwitchRef")):
        diagnostics.append(
            _diagnostic(
                "rap_receipt.rollback.required",
                "Rollback, hold, or kill-switch criteria are active; acceptance is blocked while hold evidence is preserved.",
                "rollback",
                "receipt.rollbackHold",
            )
        )
    return diagnostics


def validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Validate one structured RAP receipt.

    Returns ``{"decision": "accept" | "reject" | "hold", "diagnostics": [...]}``
    where each diagnostic is ``{"code", "message", "layer", "path"}``. Reject
    outranks hold; accept requires zero diagnostics.
    """
    if not isinstance(receipt, dict):
        return {
            "decision": "reject",
            "diagnostics": [
                _diagnostic(
                    "rap_receipt.envelope.required",
                    "Receipt must be a JSON object.",
                    "envelope",
                    "receipt",
                )
            ],
        }
    diagnostics: list[dict[str, str]] = []
    diagnostics.extend(_structural_diagnostics(receipt))
    diagnostics.extend(_authority_diagnostics(receipt))
    diagnostics.extend(_resource_diagnostics(receipt))
    diagnostics.extend(_payee_binding_diagnostics(receipt))
    diagnostics.extend(_replay_diagnostics(receipt))
    diagnostics.extend(_accounting_diagnostics(receipt))
    diagnostics.extend(_outcome_diagnostics(receipt))
    if any(diag["code"] not in HOLD_CODES for diag in diagnostics):
        decision = "reject"
    elif diagnostics:
        decision = "hold"
    else:
        decision = "accept"
    return {"decision": decision, "diagnostics": diagnostics}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate RAP receipt JSON files.")
    parser.add_argument("paths", nargs="+", help="Path(s) to receipt JSON files (one receipt object per file).")
    args = parser.parse_args()

    verdicts = []
    for raw_path in args.paths:
        receipt = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        verdict = validate_receipt(receipt)
        verdicts.append({"path": raw_path, **verdict})
    print(json.dumps({"verdicts": verdicts}, indent=2, sort_keys=True))
    decisions = {verdict["decision"] for verdict in verdicts}
    if "reject" in decisions:
        return 1
    if "hold" in decisions:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
