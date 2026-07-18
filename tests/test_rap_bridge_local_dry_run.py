#!/usr/bin/env python3
"""Check RAP bridge local executable dry-run prototype."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "rap-bridge-local-dry-run-scenarios.json"


def run_case(fixture: str = "tests/fixtures/rap-bridge-local-dry-run-scenarios.json") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/rap_bridge_local_dry_run.py", fixture],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def assert_boundaries(row: dict) -> None:
    assert row["localOnly"] is True
    assert row["liveRapBridgeCall"] is False
    assert row["runtimeExecutionAllowed"] is False
    assert row["networkAccess"] is False
    assert row["mcpInvocation"] is False
    assert row["providerApiAccess"] is False
    assert row["credentialAccess"] is False
    assert row["walletAccess"] is False
    assert row["facilitatorAccess"] is False
    assert row["paymentRailAccess"] is False
    assert row["settlementAccess"] is False
    assert row["devnetAccess"] is False
    assert row["mainnetAccess"] is False
    assert row["externalSpend"] is False


def mutated_positive_report(mutator) -> dict:
    doc = json.loads(FIXTURE.read_text())
    doc["scenarios"] = [doc["scenarios"][0]]
    mutator(doc["scenarios"][0])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=True) as fixture:
        json.dump(doc, fixture)
        fixture.flush()
        proc = run_case(fixture.name)
    assert proc.returncode == 3
    return parse_json(proc)


def main() -> int:
    proc = run_case()
    assert proc.returncode == 0
    report = parse_json(proc)
    assert report["mode"] == "rap-bridge-local-executable-dry-run-prototype"
    assert report["issue"] == 245
    assert report["parentEpic"] == 220
    assert report["status"] == "pass"
    assert report["summary"]["positiveScenarios"] == 1
    assert report["summary"]["negativeScenarios"] >= 7
    assert report["summary"]["failClosedScenarios"] >= 7
    assert len(report["summary"]["artifactHashes"]) == 1
    assert_boundaries(report)

    positive = report["results"][0]
    assert positive["id"] == "local-rap-bridge-dry-run-pass"
    assert positive["status"] == "pass"
    assert positive["failClosed"] is False
    artifact = positive["artifact"]
    assert artifact["runId"] == "rap-local-run-245-pass"
    assert artifact["intent"]["dryRun"] is True
    assert artifact["paymentHandoff"]["mode"] == "metadata-only"
    assert artifact["paymentHandoff"]["livePaymentPrepared"] is False
    assert artifact["receipt"]["paymentHandoffId"] == artifact["runId"]
    assert artifact["sourceEvidence"]["status"] == "pass"
    assert artifact["budgetEvidence"]["estimatedUsd"] == 0
    assert artifact["rollbackEvidence"]["status"] == "pass"
    assert artifact["reputationEvidence"]["source"] == "receipt-and-eval"
    assert artifact["reputationEvidence"]["emittedLive"] is False
    trace_events = {row["event"] for row in artifact["traceEvents"]}
    assert {
        "rap_bridge.intent.accepted",
        "rap_bridge.quote.prepared",
        "rap_bridge.payment_handoff.prepared",
        "rap_bridge.receipt.emitted",
        "rap_bridge.reputation.prepared",
        "rap_bridge.rollback.proven",
    } <= trace_events
    for event in artifact["traceEvents"]:
        assert event["runId"] == artifact["runId"]
        assert event["traceId"] == artifact["runId"]
        assert_boundaries(event)

    negative_reasons = {
        finding["reason"]
        for result in report["results"][1:]
        for finding in result["findings"]
    }
    assert "Receipt must bind to run id." in negative_reasons
    assert "Receipt must bind to trace id." in negative_reasons
    assert "Receipt must bind to payment handoff id." in negative_reasons
    assert "Runtime trace evidence is required." in negative_reasons
    assert "Payment rail must be an approved dry-run rail." in negative_reasons
    assert "wallet-access-denied" in negative_reasons
    assert "facilitator-access-denied" in negative_reasons
    assert "settlement-denied" in negative_reasons
    assert "live-mcp-denied" in negative_reasons
    assert "devnet-denied" in negative_reasons
    assert "mainnet-denied" in negative_reasons

    missing_binding = mutated_positive_report(
        lambda scenario: scenario["boundReferences"].__setitem__("receipt", "other-run")
    )
    assert missing_binding["results"][0]["status"] == "fail"
    assert any(
        item["path"] == "boundReferences.receipt"
        for item in missing_binding["results"][0]["findings"]
    )

    missing_source = mutated_positive_report(
        lambda scenario: scenario["source"].__setitem__("status", "fail")
    )
    assert missing_source["results"][0]["status"] == "fail"
    assert any(item["path"] == "source.status" for item in missing_source["results"][0]["findings"])

    wallet_request = mutated_positive_report(lambda scenario: scenario.__setitem__("walletRequest", True))
    assert wallet_request["results"][0]["status"] == "fail"
    assert any(
        item["reason"] == "wallet-access-denied"
        for item in wallet_request["results"][0]["findings"]
    )

    truthy_mainnet_request = mutated_positive_report(
        lambda scenario: scenario.__setitem__("mainnetRequest", 1)
    )
    assert truthy_mainnet_request["results"][0]["status"] == "fail"
    assert any(
        item["reason"] == "mainnet-denied"
        for item in truthy_mainnet_request["results"][0]["findings"]
    )

    string_wallet_request = mutated_positive_report(
        lambda scenario: scenario.__setitem__("walletRequest", "true")
    )
    assert string_wallet_request["results"][0]["status"] == "fail"
    assert any(
        item["reason"] == "wallet-access-denied"
        for item in string_wallet_request["results"][0]["findings"]
    )

    print("PASS RAP bridge local dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
