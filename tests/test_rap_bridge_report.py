#!/usr/bin/env python3
"""Check static x402/MCP-to-RAP bridge reports."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_case(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/rap_bridge_report.py", fixture],
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
    ready = run_case("tests/fixtures/rap-bridge-x402-paid-mcp-ready.json")
    assert ready.returncode == 0
    ready_doc = parse_json(ready)
    assert ready_doc["mode"] == "static-x402-mcp-rap-bridge-report"
    assert ready_doc["status"] == "pass"
    assert ready_doc["bridgeReady"] is True
    conformance = ready_doc["dryRunBridgeConformance"]
    assert conformance["level"] == "rap-dry-run-bridge"
    assert conformance["status"] == "pass"
    assert conformance["reportOnly"] is True
    assert conformance["liveBridgeAllowed"] is False
    assert conformance["passedChecks"] == conformance["requiredChecks"]
    assert "x402Vocabulary:PaymentRequired,PaymentSignature,PaymentResponse" in ready_doc["rapReady"]
    assert "authority:bounded-mandate" in ready_doc["rapReady"]
    assert "receipts:payment-plus-service-result" in ready_doc["rapReady"]
    assert ready_doc["unsafe"] == []
    assert ready_doc["unsupported"] == []
    metadata_sections = {entry["section"] for entry in ready_doc["metadataOnly"]}
    assert "x402.PaymentRequired" in metadata_sections
    assert "x402.PaymentSignature" in metadata_sections
    assert "x402.PaymentResponse" in metadata_sections
    assert "authority" in metadata_sections
    assert "receipts" in metadata_sections
    assert "reputation" in metadata_sections
    assert "conformance" in metadata_sections
    assert ready_doc["preservedVocabulary"]["x402"] == [
        "PaymentRequired",
        "PaymentSignature",
        "PaymentResponse",
    ]
    assert "receipt_verified" in ready_doc["preservedVocabulary"]["reputation"]
    assert_static_boundaries(ready_doc)

    unsafe = run_case("tests/fixtures/rap-bridge-x402-paid-mcp-unsafe.json")
    assert unsafe.returncode == 2
    unsafe_doc = parse_json(unsafe)
    assert unsafe_doc["status"] == "fail"
    assert unsafe_doc["bridgeReady"] is False
    unsafe_conformance = unsafe_doc["dryRunBridgeConformance"]
    assert unsafe_conformance["status"] == "fail"
    assert unsafe_conformance["reportOnly"] is False
    assert unsafe_conformance["liveBridgeAllowed"] is True
    assert "unsafe-live-field-scan" not in unsafe_conformance["declaredChecks"]
    assert "conformance.checks" in unsafe_conformance["failedChecks"]
    assert "conformance.reportOnly" in unsafe_conformance["failedChecks"]
    assert "conformance.liveBridgeAllowed" in unsafe_conformance["failedChecks"]
    assert unsafe_doc["rapReady"] == []
    assert_static_boundaries(unsafe_doc)
    reasons = [finding["reason"] for finding in unsafe_doc["findings"]]
    assert "Bridge input must not claim runtime, network, payment, or MCP access." in reasons
    assert "Bridge input contains a live endpoint, executable, credential, or wallet field." in reasons
    assert "Authority scope must be constrained." in reasons
    assert "Authority must define a bounded max amount." in reasons
    assert "Payment success alone cannot prove task success for RAP receipt handoff." in reasons
    assert "Required eval gate must pass before reputation signals are RAP-ready." in reasons
    assert "RAP bridge conformance must remain report-only." in reasons
    assert "RAP bridge conformance must not allow a live bridge." in reasons
    unsafe_paths = {finding["path"] for finding in unsafe_doc["unsafe"]}
    assert "service.mcp.serverUrl" in unsafe_paths
    assert "x402.PaymentRequired.resource" in unsafe_paths
    assert "x402.facilitator.endpoint" in unsafe_paths
    assert "x402.facilitator.settlementEndpoint" in unsafe_paths
    assert "x402.PaymentSignature.walletAddress" in unsafe_paths
    assert "x402.PaymentSignature.walletPrivateKey" in unsafe_paths

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=True) as live_resource:
        live_resource_doc = json.loads(
            (ROOT / "tests/fixtures/rap-bridge-x402-paid-mcp-ready.json").read_text()
        )
        live_resource_doc["x402"]["PaymentRequired"]["resource"] = (
            "https://live-mcp.example.invalid/forecast_report"
        )
        json.dump(live_resource_doc, live_resource)
        live_resource.flush()

        live_resource_proc = run_case(live_resource.name)
        assert live_resource_proc.returncode == 2
        live_resource_report = parse_json(live_resource_proc)
        live_resource_paths = {
            finding["path"] for finding in live_resource_report["unsafe"]
        }
        assert live_resource_report["bridgeReady"] is False
        assert "x402.PaymentRequired.resource" in live_resource_paths

    print("PASS RAP bridge report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
