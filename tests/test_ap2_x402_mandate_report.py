#!/usr/bin/env python3
"""Check static AP2/x402 mandate mapping reports."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/ap2_x402_mandate_report.py", fixture],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def assert_static_boundaries(report: dict) -> None:
    assert report["runtimeExecutionAllowed"] is False
    assert report["networkAccess"] is False
    assert report["paymentAccess"] is False
    assert report["mcpInvocation"] is False


def main() -> int:
    ready = run_case("tests/fixtures/ap2-x402-mandate-ready.json")
    assert ready.returncode == 0, ready.stderr
    ready_doc = parse_json(ready)
    assert ready_doc["mode"] == "static-ap2-x402-mandate-report"
    assert ready_doc["status"] == "pass"
    assert ready_doc["ap2Ready"] is True
    assert ready_doc["rapFacilitatorProfile"] == "metadata-only"
    assert ready_doc["unsafe"] == []
    assert ready_doc["unsupported"] == []
    assert_static_boundaries(ready_doc)
    mapping_statuses = {entry["status"] for entry in ready_doc["mandateMapping"]}
    assert {"ap2-ready", "metadata-only", "rap-ready"} <= mapping_statuses
    preserved = ready_doc["preservedVocabulary"]
    assert preserved["ap2"] == ["IntentMandate", "CartMandate", "PaymentMandate"]
    assert preserved["x402"] == ["PaymentRequired", "PaymentSignature", "PaymentResponse"]
    metadata_sections = {entry["section"] for entry in ready_doc["metadataOnly"]}
    assert "ap2.mandates.IntentMandate" in metadata_sections
    assert "ap2.mandates.CartMandate" in metadata_sections
    assert "ap2.mandates.PaymentMandate" in metadata_sections
    assert "rap.facilitatorProfile" in metadata_sections

    lossy = run_case("tests/fixtures/ap2-x402-mandate-lossy.json")
    assert lossy.returncode == 2
    lossy_doc = parse_json(lossy)
    assert lossy_doc["status"] == "fail"
    assert lossy_doc["ap2Ready"] is False
    assert lossy_doc["rapFacilitatorProfile"] == "blocked"
    assert lossy_doc["mandateMapping"] == []
    assert_static_boundaries(lossy_doc)
    reasons = [finding["reason"] for finding in lossy_doc["findings"]]
    assert "AP2/x402 mapping input must not claim runtime, network, payment, or MCP access." in reasons
    assert "AP2 mandate scope must be constrained." in reasons
    assert "Payment budget must define a bounded max amount." in reasons
    assert "PaymentMandate settlement rail must match an accepted x402 rail." in reasons
    assert "PaymentMandate asset must match the Reddi payment budget asset." in reasons
    assert "Payment success alone cannot satisfy Reddi/RAP receipt semantics." in reasons
    assert "Required eval gates must pass before reputation or RAP handoff is ready." in reasons
    unsafe_paths = {finding["path"] for finding in lossy_doc["unsafe"]}
    assert "x402.PaymentRequired.resource" in unsafe_paths
    assert "x402.PaymentSignature.walletPrivateKey" in unsafe_paths
    assert "ap2.mandates.PaymentMandate.endpoint" in unsafe_paths
    assert "rap.facilitatorProfile.endpoint" in unsafe_paths

    print("PASS AP2/x402 mandate report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
