#!/usr/bin/env python3
"""Check payment dry-run receipt reports."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/dry_run_receipt.py", path],
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
    ready = run_case("examples/payment-agent.yaml")
    assert ready.returncode == 0, ready.stderr
    ready_doc = parse_json(ready)
    assert ready_doc["mode"] == "static-payment-dry-run-receipt-report"
    assert ready_doc["status"] == "pass"
    assert ready_doc["receiptReady"] is True
    assert ready_doc["unsafe"] == []
    assert ready_doc["unsupported"] == []
    assert_static_boundaries(ready_doc)
    receipt = ready_doc["receipt"]
    assert receipt["receiptVersion"] == "reddiagent.receipt/v0.2"
    assert receipt["paymentRef"] == "dry-run:none"
    assert receipt["settlementReference"] is None
    assert receipt["serviceResultStatus"] == "pass"
    assert receipt["requiredEvalGateStatus"] == "pass"
    assert receipt["emissionPolicy"] == "emit-after-payment-and-service-pass"
    assert "receiptVerified" in receipt["reputationSignalsAllowed"]
    metadata_sections = {entry["section"] for entry in ready_doc["metadataOnly"]}
    assert "extensions.x402" in metadata_sections
    assert "extensions.receipts" in metadata_sections
    assert "harness.runtime" in metadata_sections

    unsafe = run_case("tests/fixtures/payment-dry-run-receipt-unsafe.yaml")
    assert unsafe.returncode == 2
    unsafe_doc = parse_json(unsafe)
    assert unsafe_doc["status"] == "fail"
    assert unsafe_doc["receiptReady"] is False
    assert unsafe_doc["receipt"] is None
    assert_static_boundaries(unsafe_doc)
    reasons = [finding["reason"] for finding in unsafe_doc["findings"]]
    assert "Dry-run receipt input must not claim runtime, network, payment, or MCP access." in reasons
    assert "Dry-run receipt input contains a live endpoint, credential, wallet, or signature field." in reasons
    assert "Payment receipt requires a bounded max amount." in reasons
    assert "Dry-run payment receipts must be required before completion." in reasons
    unsafe_paths = {finding["path"] for finding in unsafe_doc["unsafe"]}
    assert "extensions.x402.paymentAccess" in unsafe_paths
    assert "extensions.x402.intents[0].facilitatorUrl" in unsafe_paths
    assert "extensions.x402.intents[0].walletPrivateKey" in unsafe_paths

    print("PASS payment dry-run receipt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
