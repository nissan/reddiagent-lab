#!/usr/bin/env python3
"""Check ADL v0.2 conformance level field-set contracts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
CONFORMANCE_PATH = ROOT / "specs" / "CONFORMANCE-v0.1.md"
LEVEL3_READY = ROOT / "tests" / "fixtures" / "adl-v0.2-level3-ready.yaml"
LEVEL3_MISSING_RECEIPT = ROOT / "tests" / "fixtures" / "adl-v0.2-level3-missing-receipt.yaml"
LEVEL3_UNSUPPORTED_LIVE_RAIL = ROOT / "tests" / "fixtures" / "adl-v0.2-level3-unsupported-live-rail.yaml"
LEVEL4_MISSING_OBSERVABILITY = ROOT / "tests" / "fixtures" / "adl-v0.2-level4-missing-observability.yaml"
LEVEL4_WITHOUT_LEVEL3 = ROOT / "tests" / "fixtures" / "adl-v0.2-level4-complete-without-level3.yaml"
INVALID_REQUESTED_LEVEL = ROOT / "tests" / "fixtures" / "adl-v0.2-invalid-requested-level.yaml"
INVALID_MISSING_OBSERVABILITY_EVENTS = (
    ROOT / "examples" / "invalid" / "adl-v0.2-missing-observability-events.yaml"
)


def run_cli(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/adl_v02_conformance.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def schema_errors(path: Path) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    doc = yaml.safe_load(path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(doc), key=lambda item: list(item.path))]


def report_for(path: Path, *args: str, check: bool = True) -> dict:
    proc = run_cli([str(path.relative_to(ROOT)), *args], check=check)
    return json.loads(proc.stdout)[0]


def report_for_document(document: dict, check: bool = True) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mutated.yaml"
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        proc = run_cli([str(path)], check=check)
    return json.loads(proc.stdout)[0]


def test_schema_accepts_requested_conformance_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    conformance_schema = schema["properties"]["conformance"]

    assert conformance_schema["required"] == ["requestedLevel"]
    assert conformance_schema["properties"]["requestedLevel"] == {
        "type": "integer",
        "minimum": 0,
        "maximum": 4,
    }
    assert schema_errors(LEVEL3_READY) == []
    assert schema_errors(LEVEL3_MISSING_RECEIPT) == []
    assert schema_errors(LEVEL3_UNSUPPORTED_LIVE_RAIL) == []
    assert schema_errors(LEVEL4_MISSING_OBSERVABILITY) == []
    assert schema_errors(LEVEL4_WITHOUT_LEVEL3) == []
    assert schema_errors(INVALID_MISSING_OBSERVABILITY_EVENTS) == []
    assert "5 is greater than the maximum of 4" in schema_errors(INVALID_REQUESTED_LEVEL)


def test_spec_and_conformance_docs_capture_profile_matrix() -> None:
    spec = SPEC_PATH.read_text()
    conformance = CONFORMANCE_PATH.read_text()

    for text in (spec, conformance):
        assert "requestedLevel" in text
        assert "achievedLevel" in text
        assert "missingFieldsByLevel" in text
        assert "forbiddenCapabilitiesByLevel" in text
        assert "Level 3" in text
        assert "Level 4" in text

    assert "extensions.x402.intents[*].policyRefs" in spec
    assert "harness.observability.events" in spec
    assert "adapter.loss.reported" in spec
    assert "local-only" in spec
    assert "mainnet remains separately approval-gated" in spec.lower()


def test_level3_ready_fixture_passes_requested_conformance() -> None:
    report = report_for(LEVEL3_READY)

    assert report["requestedLevel"] == 3
    assert report["achievedLevel"] >= 3
    assert report["status"] == "pass"
    assert report["missingFieldsByLevel"]["3"] == []
    assert report["forbiddenCapabilitiesByLevel"]["3"] == []
    assert report["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert "receipt-evidence" in report["profile"]["evidenceOutputs"]


def test_schema_valid_level3_fixture_fails_missing_receipt_reputation_fields() -> None:
    proc = run_cli([str(LEVEL3_MISSING_RECEIPT.relative_to(ROOT))], check=False)
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["schemaDiagnostics"] == []
    assert report["requestedLevel"] == 3
    assert report["status"] == "fail"
    assert report["achievedLevel"] < 3
    assert report["missingFieldsByLevel"]["3"] == [
        "extensions.receipts.required=true",
        "extensions.reputation.emitSignals",
        "extensions.receipts.refs[intentRef=review-fee]",
    ]


def test_level3_payment_authority_must_match_intent_envelope() -> None:
    document = yaml.safe_load(LEVEL3_READY.read_text())
    intent = document["extensions"]["x402"]["intents"][0]
    intent["authority"]["maxAmount"] = "999.00"
    intent["authority"]["currency"] = "EUR"
    intent["authority"]["rails"] = ["x402-dry-run", "stripe"]
    intent["authority"]["scope"]["value"] = "different-review-fee"

    report = report_for_document(document, check=False)

    assert report["status"] == "fail"
    assert report["achievedLevel"] < 3
    assert report["missingFieldsByLevel"]["3"] == [
        "extensions.x402.intents[review-fee].authority",
    ]


def test_level3_payment_policy_must_match_budget_and_enforcement() -> None:
    excessive_intent = yaml.safe_load(LEVEL3_READY.read_text())
    excessive_intent["extensions"]["x402"]["intents"][0]["maxAmount"] = "50.00"
    report = report_for_document(excessive_intent, check=False)
    assert report["status"] == "fail"
    assert report["missingFieldsByLevel"]["3"] == [
        "extensions.x402.intents[review-fee].authority",
        "harness.policies[payment:x402:intent:review-fee]",
    ]

    wrong_target = yaml.safe_load(LEVEL3_READY.read_text())
    wrong_target["harness"]["policies"][0]["enforcement"]["target"] = "static-validator"
    report = report_for_document(wrong_target, check=False)
    assert report["status"] == "fail"
    assert report["missingFieldsByLevel"]["3"] == [
        "harness.policies[payment:x402:intent:review-fee]",
    ]

    wrong_phase = yaml.safe_load(LEVEL3_READY.read_text())
    wrong_phase["harness"]["policies"][0]["enforcement"]["phase"] = "compatibility"
    report = report_for_document(wrong_phase, check=False)
    assert report["status"] == "fail"
    assert report["missingFieldsByLevel"]["3"] == [
        "harness.policies[payment:x402:intent:review-fee]",
    ]

    loose_budget = yaml.safe_load(LEVEL3_READY.read_text())
    loose_budget["harness"]["policies"][0]["limits"]["maxUsd"] = "99.00"
    report = report_for_document(loose_budget, check=False)
    assert report["status"] == "fail"
    assert report["missingFieldsByLevel"]["3"] == [
        "harness.policies[payment:x402:intent:review-fee]",
    ]


def test_schema_valid_level4_fixture_fails_missing_production_evidence_fields() -> None:
    proc = run_cli([str(LEVEL4_MISSING_OBSERVABILITY.relative_to(ROOT))], check=False)
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["schemaDiagnostics"] == []
    assert report["requestedLevel"] == 4
    assert report["status"] == "fail"
    assert report["missingFieldsByLevel"]["4"] == [
        "harness.deployment.rollback",
        "harness.observability.events",
        "harness.recovery.disable",
        "harness.observability.events.deployment.health.checked",
        "harness.observability.events.adapter.loss.reported",
    ]
    assert report["forbiddenCapabilitiesByLevel"]["4"] == []


def test_level4_complete_shape_still_fails_without_cumulative_level3_fields() -> None:
    proc = run_cli([str(LEVEL4_WITHOUT_LEVEL3.relative_to(ROOT))], check=False)
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["schemaDiagnostics"] == []
    assert report["requestedLevel"] == 4
    assert report["status"] == "fail"
    assert report["achievedLevel"] < 4
    assert report["missingFieldsByLevel"]["4"] == []
    assert report["missingFieldsByLevel"]["3"] == [
        "extensions.x402.enabled=true",
        "extensions.x402.intents",
        "extensions.receipts.required=true",
        "extensions.reputation.emitSignals",
    ]


def test_schema_valid_level4_fixture_fails_missing_required_observability_events() -> None:
    proc = run_cli([str(INVALID_MISSING_OBSERVABILITY_EVENTS.relative_to(ROOT))], check=False)
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["schemaDiagnostics"] == []
    assert report["requestedLevel"] == 4
    assert report["status"] == "fail"
    assert "harness.observability.events.trace.completed" in report["missingFieldsByLevel"]["1"]
    assert "harness.observability.events.model.called" in report["missingFieldsByLevel"]["2"]
    assert "harness.observability.events.receipt.emitted" in report["missingFieldsByLevel"]["3"]
    assert "harness.observability.events.adapter.loss.reported" in report["missingFieldsByLevel"]["4"]


def test_cli_requested_level_override_reports_lower_level_live_gate() -> None:
    proc = run_cli(
        [
            str(LEVEL3_READY.relative_to(ROOT)),
            "--requested-level",
            "2",
        ],
        check=False,
    )
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["requestedLevel"] == 2
    assert report["status"] == "fail"
    assert report["forbiddenCapabilitiesByLevel"]["2"] == [
        "payment/reputation extension requires Level 3 or higher"
    ]


def test_invalid_requested_level_reports_schema_diagnostics_without_crashing() -> None:
    proc = run_cli([str(INVALID_REQUESTED_LEVEL.relative_to(ROOT))], check=False)
    assert proc.returncode == 1
    report = json.loads(proc.stdout)[0]

    assert report["requestedLevel"] == 5
    assert report["achievedLevel"] == -1
    assert report["status"] == "fail"
    assert report["profile"] is None
    assert report["schemaDiagnostics"]


def main() -> int:
    test_schema_accepts_requested_conformance_level()
    test_spec_and_conformance_docs_capture_profile_matrix()
    test_level3_ready_fixture_passes_requested_conformance()
    test_schema_valid_level3_fixture_fails_missing_receipt_reputation_fields()
    test_level3_payment_authority_must_match_intent_envelope()
    test_level3_payment_policy_must_match_budget_and_enforcement()
    test_schema_valid_level4_fixture_fails_missing_production_evidence_fields()
    test_level4_complete_shape_still_fails_without_cumulative_level3_fields()
    test_schema_valid_level4_fixture_fails_missing_required_observability_events()
    test_cli_requested_level_override_reports_lower_level_live_gate()
    test_invalid_requested_level_reports_schema_diagnostics_without_crashing()
    print("PASS ADL v0.2 conformance profiles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
