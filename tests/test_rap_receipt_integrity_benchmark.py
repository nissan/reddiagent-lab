#!/usr/bin/env python3
"""Check RAP receipt-integrity benchmark evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "rap-receipt-integrity-benchmark.json"

sys.path.insert(0, str(ROOT / "scripts"))
import rap_receipt_integrity_benchmark as benchmark  # noqa: E402


def run_benchmark() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/rap_receipt_integrity_benchmark.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_benchmark()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "rap-receipt-integrity-benchmark"
    assert doc["issue"] == 375
    assert doc["parentEpic"] == 220
    assert doc["dateChecked"] == "2026-07-26"
    assert doc["status"] == "pass"
    assert doc["findings"] == []
    assert doc["decision"] == "receipt-integrity-benchmark-ready-for-static-compatibility-reports"
    assert doc["consumes"]["issues"] == [374, 361, 365, 366]
    assert doc["threatCaseCount"] >= 14
    assert doc["negativeThreatCaseCount"] >= 13
    assert doc["diagnosticCount"] >= 13

    assert doc["requiredLayers"] == list(benchmark.REQUIRED_LAYERS)
    layer_requirements = {row["layer"]: row for row in doc["layerRequirements"]}
    assert set(layer_requirements) == set(benchmark.REQUIRED_LAYERS)
    assert "paymentEvidence" in layer_requirements["delegatedAuthority"]["cannotSubstitute"]
    assert "serviceOutcome" in layer_requirements["paymentEvidence"]["cannotSubstitute"]
    assert "paymentEvidence" in layer_requirements["serviceOutcome"]["cannotSubstitute"]
    assert "paymentEvidence" in layer_requirements["evalEvidence"]["cannotSubstitute"]

    cases = {case["id"]: case for case in doc["threatCases"]}
    assert cases["valid_full_receipt"]["expectedDecision"] == "accept"
    assert cases["valid_full_receipt"]["diagnostics"] == []
    for case_id in {
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
    }:
        assert case_id in cases
        assert cases[case_id]["expectedDecision"] in {"reject", "hold"}
        assert cases[case_id]["diagnostics"]
        for diagnostic in cases[case_id]["diagnostics"]:
            assert set(doc["stableDiagnosticContract"]) <= set(diagnostic)
            assert diagnostic["severity"] == "error"
            assert diagnostic["code"].startswith("rap_receipt.")
            assert diagnostic["path"].startswith("receipt.")
            assert diagnostic["remediation"]

    rule = doc["receiptIntegrityRule"]
    assert "x402/payment settlement alone cannot become service success" in rule
    assert "delegated authority" in rule
    assert "reputation eligibility" in rule
    assert "dispute closure" in rule
    assert "accounting acceptance" in rule
    assert doc["nextIssue"]["issue"] == 376
    assert "keep-docs-only" in doc["docsRefresh"]["status"]

    for key, expected in benchmark.boundaries().items():
        assert doc["boundaries"][key] is expected

    mutated = json.loads(json.dumps(doc))
    mutated["requiredLayers"] = mutated["requiredLayers"][1:]
    assert "requiredLayers" in {finding["path"] for finding in benchmark.collect_findings(mutated)}

    mutated = json.loads(json.dumps(doc))
    mutated["threatCases"][1]["diagnostics"] = []
    assert "threatCases.1.diagnostics" in {finding["path"] for finding in benchmark.collect_findings(mutated)}

    mutated = json.loads(json.dumps(doc))
    mutated["boundaries"]["devnetRun"] = True
    assert "boundaries.devnetRun" in {finding["path"] for finding in benchmark.collect_findings(mutated)}
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
