#!/usr/bin/env python3
"""Validate the RAP receipt-integrity validator against the benchmark threat model."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

sys.path.insert(0, str(ROOT / "scripts"))
import rap_receipt_integrity_benchmark as benchmark  # noqa: E402
import rap_receipt_validator as validator  # noqa: E402


def codes(verdict: dict) -> set[str]:
    return {diag["code"] for diag in verdict["diagnostics"]}


def test_pass_receipt_accepts_with_no_diagnostics() -> None:
    verdict = validator.validate_receipt(benchmark.base_receipt())
    assert verdict == {"decision": "accept", "diagnostics": []}


def test_all_benchmark_threat_cases_match_expected_decisions() -> None:
    cases = benchmark.threat_cases()
    assert len(cases) == 14
    for case in cases:
        verdict = validator.validate_receipt(case["receipt"])
        assert verdict["decision"] == case["expectedDecision"], case["id"]
        expected_codes = {diag["code"] for diag in case["diagnostics"]}
        assert expected_codes <= codes(verdict), case["id"]
        for diag in verdict["diagnostics"]:
            assert set(diag) == {"code", "message", "layer", "path"}, case["id"]
            assert diag["code"].startswith("rap_receipt."), case["id"]
            assert diag["path"].startswith("receipt"), case["id"]
            assert diag["message"], case["id"]


def test_fixture_threat_cases_match_computed_decisions() -> None:
    doc = json.loads((ROOT / "tests" / "fixtures" / "rap-receipt-integrity-benchmark.json").read_text())
    for case in doc["threatCases"]:
        verdict = validator.validate_receipt(case["receipt"])
        assert verdict["decision"] == case["expectedDecision"], case["id"]
        assert {diag["code"] for diag in case["diagnostics"]} <= codes(verdict), case["id"]


def test_every_layer_removal_rejects_with_required_code() -> None:
    for layer in validator.REQUIRED_LAYERS:
        verdict = validator.validate_receipt(benchmark.receipt_without_layer(layer))
        assert verdict["decision"] == "reject", layer
        category = validator.LAYER_CATEGORY[layer]
        expected = validator.MISSING_LAYER_CODES.get(layer, f"rap_receipt.{category}.required")
        assert expected in codes(verdict), layer


def test_every_layer_type_corruption_rejects() -> None:
    for layer in validator.REQUIRED_LAYERS:
        receipt = benchmark.base_receipt()
        receipt[layer] = "string-sentinel"
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", layer


def test_purpose_mismatch_rejects() -> None:
    receipt = benchmark.receipt_with_fields("delegatedAuthority", purpose="portfolio-rebalance")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.scope_mismatch" in codes(verdict)


def test_expired_authority_rejects_relative_to_finalized_at() -> None:
    receipt = benchmark.receipt_with_fields("delegatedAuthority", expiresAt="2026-07-25T00:00:00Z")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.expired" in codes(verdict)
    # Moving finalization before expiry (data-only, no wall clock) restores accept.
    receipt["finalizedAt"] = "2026-07-24T00:00:00Z"
    assert validator.validate_receipt(receipt)["decision"] == "accept"


def test_revoked_authority_rejects() -> None:
    receipt = benchmark.receipt_with_fields("delegatedAuthority", revoked=True)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.expired" in codes(verdict)


def test_weak_intent_binding_rejects() -> None:
    receipt = benchmark.receipt_with_fields("delegatedAuthority", payee="", maxAmount=None)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.weak_binding" in codes(verdict)


def test_amount_over_mandate_cap_rejects() -> None:
    receipt = benchmark.receipt_with_fields("paymentEvidence", amount=999999999)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.scope_mismatch" in codes(verdict)


def test_resource_scope_mismatch_rejects() -> None:
    receipt = benchmark.receipt_with_fields("resourceAuthorization", scope="mcp:market-data:trade:write")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.resource.scope_mismatch" in codes(verdict)


def test_payee_binding_enforced_on_every_leg() -> None:
    for layer, field in (
        ("paymentEvidence", "payee"),
        ("settlementProgramProof", "payee"),
        ("serviceOutcome", "agentId"),
    ):
        receipt = benchmark.receipt_with_fields(layer, **{field: "agent:svc-imposter"})
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", layer
        assert "rap_receipt.settlement.payee_mismatch" in codes(verdict), layer
        paths = {diag["path"] for diag in verdict["diagnostics"]}
        assert f"receipt.{layer}.{field}" in paths, layer


def test_replay_double_spend_rejects() -> None:
    receipt = benchmark.receipt_with_fields(
        "replayIdempotency", priorPaymentResponseHashes=["sha256:x402-response-0001"]
    )
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.replay.duplicate_payment" in codes(verdict)


def test_payment_bound_to_foreign_request_rejects() -> None:
    receipt = benchmark.receipt_with_fields("paymentEvidence", boundRequestId="req-other-9999")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.replay.duplicate_payment" in codes(verdict)


def test_accounting_missing_joins_rejects() -> None:
    receipt = benchmark.receipt_with_fields("privacyAccounting", joinRefs=["req-375-0001"])
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.accounting.join_required" in codes(verdict)


def test_eval_failed_receipt_cannot_accept() -> None:
    receipt = benchmark.receipt_with_fields("evalEvidence", status="failed")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.eval.failed" in codes(verdict)


def test_hold_states_produce_hold_with_expected_codes() -> None:
    for receipt, code in (
        (benchmark.receipt_with_fields("serviceOutcome", status="failed"), "rap_receipt.service.failed_after_payment"),
        (
            benchmark.receipt_with_fields("disputeState", status="open", openedAt="2026-07-26T02:30:00Z"),
            "rap_receipt.dispute.open",
        ),
        (
            benchmark.receipt_with_fields("rollbackHold", rollbackRequired=True, holdState="hold"),
            "rap_receipt.rollback.required",
        ),
    ):
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "hold", code
        assert code in codes(verdict), code


def test_reject_outranks_hold() -> None:
    receipt = benchmark.receipt_with_fields("disputeState", status="open", openedAt="2026-07-26T02:30:00Z")
    receipt["evalEvidence"]["status"] = "failed"
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert {"rap_receipt.dispute.open", "rap_receipt.eval.failed"} <= codes(verdict)


def test_payment_and_settlement_alone_can_never_accept() -> None:
    """Non-substitutability: perfect payment + settlement evidence cannot buy
    service success, reputation eligibility, dispute closure, or accounting
    acceptance."""
    full = benchmark.base_receipt()
    payment_only = {
        "receiptId": full["receiptId"],
        "finalizedAt": full["finalizedAt"],
        "request": copy.deepcopy(full["request"]),
        "paymentEvidence": copy.deepcopy(full["paymentEvidence"]),
        "settlementProgramProof": copy.deepcopy(full["settlementProgramProof"]),
    }
    verdict = validator.validate_receipt(payment_only)
    assert verdict["decision"] == "reject"
    missing_codes = codes(verdict)
    assert "rap_receipt.service_outcome.required" in missing_codes
    assert "rap_receipt.authority.required" in missing_codes
    assert "rap_receipt.eval.required" in missing_codes
    assert "rap_receipt.accounting.required" in missing_codes
    assert "rap_receipt.dispute.required" in missing_codes


def test_non_substitutability_matrix_matches_benchmark_doc() -> None:
    rows = {row["layer"]: tuple(row["cannotSubstitute"]) for row in benchmark.layer_requirements()}
    assert rows == validator.NON_SUBSTITUTABLE
    assert set(validator.NON_SUBSTITUTABLE) == set(validator.REQUIRED_LAYERS)


WRONG_TYPE_SENTINELS = {
    validator.STR: 12345,
    validator.AMOUNT: "120000",
    validator.STR_LIST: "not-a-list",
    validator.BOOL: "false",
}


def test_every_decision_relevant_field_rejects_on_wrong_type() -> None:
    """C1/C2/C3/M4 sweep: any wrong-typed decision-relevant field must emit
    rap_receipt.<category>.invalid and reject — never skip, never crash."""
    for layer, field_types in validator.FIELD_TYPES.items():
        for field, kind in field_types.items():
            receipt = benchmark.receipt_with_fields(layer, **{field: WRONG_TYPE_SENTINELS[kind]})
            verdict = validator.validate_receipt(receipt)
            assert verdict["decision"] == "reject", (layer, field)
            category = validator.LAYER_CATEGORY[layer]
            assert f"rap_receipt.{category}.invalid" in codes(verdict), (layer, field)
    for field in validator.REQUIRED_REQUEST_FIELDS:
        receipt = benchmark.base_receipt()
        receipt["request"][field] = 12345
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", field
        assert "rap_receipt.envelope.required" in codes(verdict), field


def test_wrong_typed_amount_rejects_instead_of_skipping_cap() -> None:
    # C1 / probe A10: stringified over-cap amount must not bypass the spend cap.
    receipt = benchmark.receipt_with_fields("paymentEvidence", amount="999999999")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.payment.invalid" in codes(verdict)
    # Probe A22: bool is an int subclass; amounts must still reject it.
    receipt = benchmark.receipt_with_fields("paymentEvidence", amount=True)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.payment.invalid" in codes(verdict)


def test_wrong_typed_max_amount_rejects_instead_of_skipping_cap() -> None:
    # C1 / probe A11: stringified cap plus over-cap payment must reject.
    receipt = benchmark.receipt_with_fields("delegatedAuthority", maxAmount="tiny")
    receipt["paymentEvidence"]["amount"] = 999999999
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.invalid" in codes(verdict)


def test_wrong_typed_replay_ledger_rejects_instead_of_skipping_check() -> None:
    # C2 / probe A12: ledger check must never be skippable by type.
    for bad_ledger in ("sha256:x402-response-0001", ["sha256:x402-response-0001", 42]):
        receipt = benchmark.receipt_with_fields("replayIdempotency", priorPaymentResponseHashes=bad_ledger)
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", bad_ledger
        assert "rap_receipt.replay.invalid" in codes(verdict), bad_ledger


def test_wrong_typed_join_refs_rejects_instead_of_skipping_check() -> None:
    # C3 / probe A13: joinRefs as a string must reject, not skip the join check.
    receipt = benchmark.receipt_with_fields("privacyAccounting", joinRefs="req-375-0001")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.accounting.invalid" in codes(verdict)


def test_wrong_typed_expires_at_rejects_without_crashing() -> None:
    # M4 / probe A14: int expiresAt used to raise TypeError on str comparison.
    receipt = benchmark.receipt_with_fields("delegatedAuthority", expiresAt=12345)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.invalid" in codes(verdict)


def test_unconfirmed_settlement_status_rejects() -> None:
    # M5 / probe A16: settlement proof must carry a confirmed status.
    for status in ("failed", "processed", "pending"):
        receipt = benchmark.receipt_with_fields("settlementProgramProof", confirmationStatus=status)
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", status
        assert "rap_receipt.settlement.unconfirmed" in codes(verdict), status
    # Both confirmed states accept.
    for status in ("confirmed", "finalized"):
        receipt = benchmark.receipt_with_fields("settlementProgramProof", confirmationStatus=status)
        assert validator.validate_receipt(receipt)["decision"] == "accept", status


def test_request_hash_context_binding_enforced() -> None:
    # M6 / probes A17 + A20: outcome and idempotency evidence lifted from a
    # different request must reject, mirroring the boundRequestId binding.
    for layer, path in (
        ("serviceOutcome", "receipt.serviceOutcome.requestHash"),
        ("replayIdempotency", "receipt.replayIdempotency.requestHash"),
    ):
        receipt = benchmark.receipt_with_fields(layer, requestHash="sha256:req-OTHER")
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", layer
        assert "rap_receipt.replay.duplicate_payment" in codes(verdict), layer
        assert path in {diag["path"] for diag in verdict["diagnostics"]}, layer


def test_settlement_amount_cross_checked_against_payment_and_cap() -> None:
    # M7 / probe A19: settling 1 while claiming the full payment must reject.
    receipt = benchmark.receipt_with_fields("settlementProgramProof", amount=1)
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.settlement.amount_mismatch" in codes(verdict)
    # Settlement amount over the mandate cap rejects even when it matches payment.
    receipt = benchmark.receipt_with_fields("settlementProgramProof", amount=300000)
    receipt["paymentEvidence"]["amount"] = 300000
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.scope_mismatch" in codes(verdict)
    assert "receipt.settlementProgramProof.amount" in {diag["path"] for diag in verdict["diagnostics"]}


def test_payment_rail_must_match_mandate_rail() -> None:
    # M8 / probe A18: the mandate binds the rail; a different rail rejects.
    receipt = benchmark.receipt_with_fields("paymentEvidence", rail="stripe-card")
    verdict = validator.validate_receipt(receipt)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.authority.scope_mismatch" in codes(verdict)
    assert "receipt.paymentEvidence.rail" in {diag["path"] for diag in verdict["diagnostics"]}


def test_unknown_enum_values_reject_as_invalid_not_hold() -> None:
    # M9 / probes A7-A9, A23: unknown enum values are structural rejects, not
    # semantically-labeled holds.
    for layer, field, value, code in (
        ("serviceOutcome", "status", "Success", "rap_receipt.service.invalid"),
        ("evalEvidence", "status", "PASS", "rap_receipt.eval.invalid"),
        ("disputeState", "status", "None", "rap_receipt.dispute.invalid"),
        ("rollbackHold", "holdState", "paused", "rap_receipt.rollback.invalid"),
        ("rollbackHold", "rollbackRequired", "false", "rap_receipt.rollback.invalid"),
    ):
        receipt = benchmark.receipt_with_fields(layer, **{field: value})
        verdict = validator.validate_receipt(receipt)
        assert verdict["decision"] == "reject", (layer, field, value)
        assert code in codes(verdict), (layer, field, value)


def test_unknown_extra_layers_are_ignored_and_cannot_substitute() -> None:
    # M11: documented policy — extras are ignored; required layers are still
    # fully validated and extras carry zero evidential weight.
    receipt = benchmark.base_receipt()
    receipt["superAdminOverride"] = {"grant": "all"}
    receipt["extraLayer"] = {"x": 1}
    assert validator.validate_receipt(receipt) == {"decision": "accept", "diagnostics": []}
    # Extras cannot substitute for missing required evidence.
    stripped = benchmark.receipt_without_layer("serviceOutcome")
    stripped["serviceOutcomeOverride"] = {"status": "success"}
    verdict = validator.validate_receipt(stripped)
    assert verdict["decision"] == "reject"
    assert "rap_receipt.service_outcome.required" in codes(verdict)


def test_benchmark_collect_findings_flags_spec_implementation_drift() -> None:
    doc = benchmark.build_doc()
    assert benchmark.collect_findings(doc) == []
    drifted = json.loads(json.dumps(doc))
    drifted["threatCases"][0]["expectedDecision"] = "reject"
    paths = {finding["path"] for finding in benchmark.collect_findings(drifted)}
    assert "threatCases.0.expectedDecision" in paths
    drifted = json.loads(json.dumps(doc))
    drifted["threatCases"][2]["receipt"]["delegatedAuthority"]["purpose"] = doc["threatCases"][2]["receipt"]["request"][
        "purpose"
    ]
    paths = {finding["path"] for finding in benchmark.collect_findings(drifted)}
    assert {"threatCases.2.expectedDecision", "threatCases.2.diagnostics"} <= paths


def test_cli_exit_codes_and_json_verdicts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        accept_path = tmp_path / "accept.json"
        reject_path = tmp_path / "reject.json"
        hold_path = tmp_path / "hold.json"
        accept_path.write_text(json.dumps(benchmark.base_receipt()))
        reject_path.write_text(json.dumps(benchmark.receipt_without_layer("paymentEvidence")))
        hold_path.write_text(
            json.dumps(benchmark.receipt_with_fields("disputeState", status="open", openedAt="2026-07-26T02:30:00Z"))
        )

        def run_cli(*paths: Path) -> subprocess.CompletedProcess:
            return subprocess.run(
                [PYTHON, "scripts/rap_receipt_validator.py", *[str(path) for path in paths]],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

        proc = run_cli(accept_path)
        assert proc.returncode == 0, proc.stderr
        output = json.loads(proc.stdout)
        assert output["verdicts"][0]["decision"] == "accept"
        # M10: the CLI documents the non-substitutability matrix in its output.
        assert output["nonSubstitutableMatrix"] == {
            layer: list(rules) for layer, rules in validator.NON_SUBSTITUTABLE.items()
        }

        proc = run_cli(accept_path, hold_path)
        assert proc.returncode == 2, proc.stderr
        assert json.loads(proc.stdout)["verdicts"][1]["decision"] == "hold"

        proc = run_cli(accept_path, hold_path, reject_path)
        assert proc.returncode == 1, proc.stderr
        decisions = [verdict["decision"] for verdict in json.loads(proc.stdout)["verdicts"]]
        assert decisions == ["accept", "hold", "reject"]


def main() -> int:
    test_pass_receipt_accepts_with_no_diagnostics()
    test_all_benchmark_threat_cases_match_expected_decisions()
    test_fixture_threat_cases_match_computed_decisions()
    test_every_layer_removal_rejects_with_required_code()
    test_every_layer_type_corruption_rejects()
    test_purpose_mismatch_rejects()
    test_expired_authority_rejects_relative_to_finalized_at()
    test_revoked_authority_rejects()
    test_weak_intent_binding_rejects()
    test_amount_over_mandate_cap_rejects()
    test_resource_scope_mismatch_rejects()
    test_payee_binding_enforced_on_every_leg()
    test_replay_double_spend_rejects()
    test_payment_bound_to_foreign_request_rejects()
    test_accounting_missing_joins_rejects()
    test_eval_failed_receipt_cannot_accept()
    test_hold_states_produce_hold_with_expected_codes()
    test_reject_outranks_hold()
    test_payment_and_settlement_alone_can_never_accept()
    test_non_substitutability_matrix_matches_benchmark_doc()
    test_every_decision_relevant_field_rejects_on_wrong_type()
    test_wrong_typed_amount_rejects_instead_of_skipping_cap()
    test_wrong_typed_max_amount_rejects_instead_of_skipping_cap()
    test_wrong_typed_replay_ledger_rejects_instead_of_skipping_check()
    test_wrong_typed_join_refs_rejects_instead_of_skipping_check()
    test_wrong_typed_expires_at_rejects_without_crashing()
    test_unconfirmed_settlement_status_rejects()
    test_request_hash_context_binding_enforced()
    test_settlement_amount_cross_checked_against_payment_and_cap()
    test_payment_rail_must_match_mandate_rail()
    test_unknown_enum_values_reject_as_invalid_not_hold()
    test_unknown_extra_layers_are_ignored_and_cannot_substitute()
    test_benchmark_collect_findings_flags_spec_implementation_drift()
    test_cli_exit_codes_and_json_verdicts()
    print("PASS RAP receipt validator")
    return 0


if __name__ == "__main__":
    sys.exit(main())
