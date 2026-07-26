#!/usr/bin/env python3
"""RAP receipt-integrity validator.

Computes an accept/reject/hold decision for a structured RAP receipt across
the ten evidence layers defined by ``scripts/rap_receipt_integrity_benchmark.py``,
using the same stable ``rap_receipt.*`` diagnostic codes. The validator is
pure and deterministic: no network, no wall-clock reads — expiry is judged
against the receipt's own ``finalizedAt`` field.

Enforced properties:

- All ten evidence layers must be present and structurally valid.
- Fail closed on types: every decision-relevant field has an expected type
  (``FIELD_TYPES``); a wrong-typed value (string amount, string ledger,
  bool-as-int, non-string timestamp, ...) emits
  ``rap_receipt.<category>.invalid`` and rejects. Semantic checks never run
  on — and can never be skipped by — a wrong-typed field.
- Non-substitutability: settlement/payment evidence alone can never produce
  accept for service success, reputation eligibility, dispute closure, or
  accounting acceptance (missing layers reject).
- Replay protection and context binding: payment proof is bound to a single
  request id, service outcome and replay idempotency hashes must match the
  request hash, and a payment response hash already recorded in the replay
  ledger rejects.
- Delegated-authority scope: purpose must match the request intent, the
  mandate must not be revoked, and ``expiresAt`` must not predate
  ``finalizedAt``.
- Payee, rail, and amount binding: payment, settlement, and service-agent
  payees must match the mandate payee; the payment rail must match the
  mandate rail; the paid amount must not exceed the mandate cap; and the
  settlement amount must equal the payment amount and stay within the cap.
- Settlement proof must carry a confirmed status
  (``CONFIRMED_SETTLEMENT_STATUSES``); anything else rejects.
- Eval-failed receipts cannot yield a reputation-eligible accept.
- Open disputes and active rollback/hold/kill-switch state produce hold.
  Unknown enum values for decision-relevant statuses are *not* semantic
  states: they emit ``rap_receipt.<category>.invalid`` and reject.

Unknown extra layers policy (deliberate): top-level keys outside the request
envelope and the ten required layers are ignored. This is fail-closed, not
fail-open — every acceptance criterion is anchored to the required layers,
which are always fully validated, so an unknown layer carries zero evidential
weight and can never substitute for any required evidence (see
``NON_SUBSTITUTABLE``). Ignoring extras keeps receipts forward-compatible
with future evidence layers without weakening the current decision.

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

# Expected-type kinds for decision-relevant fields. AMOUNT excludes bool
# explicitly because bool is an int subclass in Python.
STR = "string"
AMOUNT = "amount"
STR_LIST = "string-list"
BOOL = "boolean"

FIELD_TYPES: dict[str, dict[str, str]] = {
    layer: {field: STR for field in fields} for layer, fields in REQUIRED_LAYER_FIELDS.items()
}
FIELD_TYPES["delegatedAuthority"]["maxAmount"] = AMOUNT
FIELD_TYPES["paymentEvidence"]["amount"] = AMOUNT
FIELD_TYPES["settlementProgramProof"]["amount"] = AMOUNT
FIELD_TYPES["replayIdempotency"]["priorPaymentResponseHashes"] = STR_LIST
FIELD_TYPES["privacyAccounting"]["joinRefs"] = STR_LIST
FIELD_TYPES["rollbackHold"]["rollbackRequired"] = BOOL

REQUEST_FIELD_TYPES: dict[str, str] = {field: STR for field in REQUIRED_REQUEST_FIELDS}


def _wrong_type(value: Any, kind: str) -> bool:
    if kind == AMOUNT:
        return isinstance(value, bool) or not isinstance(value, (int, float))
    if kind == STR_LIST:
        return not isinstance(value, list) or any(not isinstance(item, str) for item in value)
    if kind == BOOL:
        return not isinstance(value, bool)
    return not isinstance(value, str)

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

# Closed enum sets for decision-relevant statuses. Known-bad values map to
# their true semantic reject/hold codes; anything outside the set is a
# structural rap_receipt.<category>.invalid reject, never a semantic hold.
KNOWN_SERVICE_STATUSES = frozenset({"success", "failed"})
KNOWN_EVAL_STATUSES = frozenset({"pass", "failed"})
KNOWN_DISPUTE_STATUSES = CLEAR_DISPUTE_STATUSES | {"open"}
KNOWN_HOLD_STATES = frozenset({"none", "hold"})
CONFIRMED_SETTLEMENT_STATUSES = frozenset({"confirmed", "finalized"})


def _diagnostic(code: str, message: str, layer: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "layer": layer, "path": path}


def _missing_fields(layer_value: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [
        field
        for field in fields
        if field not in layer_value or layer_value[field] is None or layer_value[field] == ""
    ]


def _wrong_typed_fields(layer_value: dict[str, Any], field_types: dict[str, str]) -> list[str]:
    """Fields that are present (not missing) but carry a wrong-typed value."""
    missing = set(_missing_fields(layer_value, tuple(field_types)))
    return [
        field
        for field, kind in field_types.items()
        if field not in missing and _wrong_type(layer_value[field], kind)
    ]


def _valid_request(receipt: dict[str, Any]) -> dict[str, Any] | None:
    """Return the request envelope when complete and well-typed, else None.

    Semantic cross-checks must never consume a malformed request: the
    structural layer already rejects it via rap_receipt.envelope.required.
    """
    request = receipt.get("request")
    if not isinstance(request, dict):
        return None
    if _missing_fields(request, REQUIRED_REQUEST_FIELDS) or _wrong_typed_fields(request, REQUEST_FIELD_TYPES):
        return None
    return request


def _valid_layer(receipt: dict[str, Any], layer: str) -> dict[str, Any] | None:
    """Return the layer dict when present, complete, and well-typed, else None."""
    value = receipt.get(layer)
    if not isinstance(value, dict):
        return None
    if _missing_fields(value, REQUIRED_LAYER_FIELDS[layer]):
        return None
    if _wrong_typed_fields(value, FIELD_TYPES[layer]):
        return None
    return value


def _structural_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if _valid_request(receipt) is None:
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
        wrong_typed = _wrong_typed_fields(value, FIELD_TYPES[layer])
        if wrong_typed:
            diagnostics.append(
                _diagnostic(
                    f"rap_receipt.{category}.invalid",
                    f"Evidence layer {layer} has wrong-typed fields: {', '.join(sorted(wrong_typed))}.",
                    category,
                    f"receipt.{layer}",
                )
            )
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
    request = _valid_request(receipt)
    finalized_at = receipt.get("finalizedAt")
    if authority is None or request is None:
        return diagnostics
    if authority["purpose"] != request["purpose"]:
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
    request = _valid_request(receipt)
    if resource is None or request is None:
        return []
    if resource["toolName"] != request["toolName"] or resource["scope"] != request["resourceScope"]:
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
    if payment is not None:
        # _valid_layer guarantees numeric amounts and string rails here; a
        # wrong-typed field already rejected via rap_receipt.*.invalid.
        if payment["amount"] > authority["maxAmount"]:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.authority.scope_mismatch",
                    f"Paid amount {payment['amount']} exceeds mandate cap {authority['maxAmount']}.",
                    "authority",
                    "receipt.paymentEvidence.amount",
                )
            )
        if payment["rail"] != authority["rail"]:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.authority.scope_mismatch",
                    f"Payment rail {payment['rail']!r} does not match mandate rail {authority['rail']!r}.",
                    "authority",
                    "receipt.paymentEvidence.rail",
                )
            )
    return diagnostics


def _settlement_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    settlement = _valid_layer(receipt, "settlementProgramProof")
    if settlement is None:
        return diagnostics
    if settlement["confirmationStatus"] not in CONFIRMED_SETTLEMENT_STATUSES:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.settlement.unconfirmed",
                f"Settlement confirmationStatus {settlement['confirmationStatus']!r} is not a confirmed state; "
                f"expected one of: {', '.join(sorted(CONFIRMED_SETTLEMENT_STATUSES))}.",
                "settlement",
                "receipt.settlementProgramProof.confirmationStatus",
            )
        )
    payment = _valid_layer(receipt, "paymentEvidence")
    if payment is not None and settlement["amount"] != payment["amount"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.settlement.amount_mismatch",
                f"Settled amount {settlement['amount']} does not match payment amount {payment['amount']}.",
                "settlement",
                "receipt.settlementProgramProof.amount",
            )
        )
    authority = _valid_layer(receipt, "delegatedAuthority")
    if authority is not None and settlement["amount"] > authority["maxAmount"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.authority.scope_mismatch",
                f"Settled amount {settlement['amount']} exceeds mandate cap {authority['maxAmount']}.",
                "authority",
                "receipt.settlementProgramProof.amount",
            )
        )
    return diagnostics


def _replay_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    payment = _valid_layer(receipt, "paymentEvidence")
    replay = _valid_layer(receipt, "replayIdempotency")
    request = _valid_request(receipt)
    # _valid_layer guarantees priorPaymentResponseHashes is a list of strings;
    # a wrong-typed ledger already rejected via rap_receipt.replay.invalid.
    if payment is not None and replay is not None and payment["responseHash"] in replay["priorPaymentResponseHashes"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.replay.duplicate_payment",
                "Payment response hash already appears in the replay ledger; a settled payment cannot be counted twice.",
                "replay",
                "receipt.replayIdempotency.priorPaymentResponseHashes",
            )
        )
    if payment is not None and request is not None and payment["boundRequestId"] != request["requestId"]:
        diagnostics.append(
            _diagnostic(
                "rap_receipt.replay.duplicate_payment",
                f"Payment proof is bound to request {payment['boundRequestId']!r}, not this receipt's request {request['requestId']!r}.",
                "replay",
                "receipt.paymentEvidence.boundRequestId",
            )
        )
    # Context binding: service outcome and replay idempotency evidence must be
    # bound to this receipt's request hash, not lifted from another request.
    if request is not None:
        request_hash = request["requestHash"]
        for layer, path in (
            ("serviceOutcome", "receipt.serviceOutcome.requestHash"),
            ("replayIdempotency", "receipt.replayIdempotency.requestHash"),
        ):
            value = _valid_layer(receipt, layer)
            if value is not None and value["requestHash"] != request_hash:
                diagnostics.append(
                    _diagnostic(
                        "rap_receipt.replay.duplicate_payment",
                        f"{layer} evidence is bound to request hash {value['requestHash']!r}, "
                        f"not this receipt's request hash {request_hash!r}.",
                        "replay",
                        path,
                    )
                )
    return diagnostics


def _accounting_diagnostics(receipt: dict[str, Any]) -> list[dict[str, str]]:
    accounting = _valid_layer(receipt, "privacyAccounting")
    if accounting is None:
        return []
    # _valid_layer guarantees joinRefs is a list of strings; a wrong-typed
    # value already rejected via rap_receipt.accounting.invalid.
    join_refs = accounting["joinRefs"]
    request = _valid_request(receipt)
    required_refs: list[str] = []
    if request is not None:
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
    if service is not None:
        if service["status"] not in KNOWN_SERVICE_STATUSES:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.service.invalid",
                    f"Service status {service['status']!r} is not a known status; unknown enum values reject.",
                    "service",
                    "receipt.serviceOutcome.status",
                )
            )
        elif service["status"] != "success":
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.service.failed_after_payment",
                    f"Service status is {service['status']!r} after settled payment; hold for refund, retry, or dispute handling.",
                    "service",
                    "receipt.serviceOutcome.status",
                )
            )
    evaluation = _valid_layer(receipt, "evalEvidence")
    if evaluation is not None:
        if evaluation["status"] not in KNOWN_EVAL_STATUSES:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.eval.invalid",
                    f"Eval status {evaluation['status']!r} is not a known status; unknown enum values reject.",
                    "eval",
                    "receipt.evalEvidence.status",
                )
            )
        elif evaluation["status"] != "pass":
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.eval.failed",
                    "Required evaluation gate did not pass; the receipt cannot become reputation-eligible.",
                    "eval",
                    "receipt.evalEvidence.status",
                )
            )
    dispute = _valid_layer(receipt, "disputeState")
    if dispute is not None:
        if dispute["status"] not in KNOWN_DISPUTE_STATUSES:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.dispute.invalid",
                    f"Dispute status {dispute['status']!r} is not a known status; unknown enum values reject.",
                    "dispute",
                    "receipt.disputeState.status",
                )
            )
        elif dispute["status"] not in CLEAR_DISPUTE_STATUSES:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.dispute.open",
                    f"Dispute state is {dispute['status']!r}; hold accounting and reputation until resolution closes.",
                    "dispute",
                    "receipt.disputeState.status",
                )
            )
    ops = _valid_layer(receipt, "rollbackHold")
    if ops is not None:
        if ops["holdState"] not in KNOWN_HOLD_STATES:
            diagnostics.append(
                _diagnostic(
                    "rap_receipt.rollback.invalid",
                    f"Hold state {ops['holdState']!r} is not a known state; unknown enum values reject.",
                    "rollback",
                    "receipt.rollbackHold.holdState",
                )
            )
        elif ops["rollbackRequired"] or ops["holdState"] != "none" or ops.get("killSwitchRef"):
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
    diagnostics.extend(_settlement_diagnostics(receipt))
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
    output = {
        # Documented non-substitutability matrix (mirrors the benchmark doc):
        # which layers each evidence layer can never substitute for.
        "nonSubstitutableMatrix": {layer: list(rules) for layer, rules in NON_SUBSTITUTABLE.items()},
        "verdicts": verdicts,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    decisions = {verdict["decision"] for verdict in verdicts}
    if "reject" in decisions:
        return 1
    if "hold" in decisions:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
