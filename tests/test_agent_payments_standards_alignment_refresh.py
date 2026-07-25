#!/usr/bin/env python3
"""Check agent-payments standards alignment refresh evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "agent-payments-standards-alignment-refresh.json"

sys.path.insert(0, str(ROOT / "scripts"))
import agent_payments_standards_alignment_refresh as packet  # noqa: E402


def run_packet() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/agent_payments_standards_alignment_refresh.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_packet()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "agent-payments-standards-alignment-refresh"
    assert doc["issue"] == 374
    assert doc["parentEpic"] == 220
    assert doc["dateChecked"] == "2026-07-25"
    assert doc["status"] == "pass"
    assert doc["findings"] == []
    assert doc["decision"] == "standards-refresh-ready-for-receipt-integrity-benchmark"
    assert doc["protocolCount"] == 10
    assert doc["sourceCount"] >= 20

    matrix = {row["protocol"]: row for row in doc["sourceMatrix"]}
    assert set(matrix) == {
        "x402",
        "Pay.sh",
        "AP2/FIDO/Verifiable Intent",
        "MCP authorization",
        "AIP",
        "Solana Agent Registry/SATI/ERC-8004",
        "Token-2022",
        "MPP",
        "ACP",
        "RAP",
    }
    assert matrix["x402"]["layer"] == "paymentEvidence"
    assert matrix["AP2/FIDO/Verifiable Intent"]["layer"] == "delegatedAuthority"
    assert matrix["MCP authorization"]["layer"] == "protectedResourceAccess"
    assert matrix["Token-2022"]["layer"] == "settlementAssetControls"
    assert matrix["RAP"]["layer"] == "receiptAccountingDisputeEvalReputation"

    rules = "\n".join(rule["rule"] for rule in doc["layerRules"])
    assert "x402 is payment evidence" in rules
    assert "AP2/FIDO/Verifiable Intent is delegated authority" in rules
    assert "MCP auth is protected resource access" in rules
    assert "Solana is settlement/program evidence" in rules
    assert "RAP binds receipt/accounting/dispute/eval/reputation evidence" in rules

    assert [row["issue"] for row in doc["issueLadder"]] == [374, 375, 376, 377, 378, 379, 380]
    assert doc["issueLadder"][1]["issue"] == 375
    assert doc["issueLadder"][1]["swimlane"] == "RAP Receipt Integrity"
    assert doc["issueLadder"][-1]["status"] == "lower-priority"
    assert doc["laterGateNotCreated"]["name"] == "bounded Solana devnet external tester cohort-0 execution"
    assert "fresh bounded Nissan approval" in doc["laterGateNotCreated"]["reason"]

    refreshed = {entry["sourceIssue"]: entry["refresh"] for entry in doc["refreshAssumptions"]}
    assert "#361" in refreshed
    assert "#365" in refreshed
    assert "#366" in refreshed
    assert "#206" in refreshed
    assert "Keep docs-only" in refreshed["#206"]

    for key, expected in packet.boundaries().items():
        assert doc["boundaries"][key] is expected

    mutated = json.loads(json.dumps(doc))
    mutated["issueLadder"][1]["issue"] = 380
    assert "issueLadder" in {finding["path"] for finding in packet.collect_findings(mutated)}

    mutated = json.loads(json.dumps(doc))
    mutated["boundaries"]["devnetRun"] = True
    assert "boundaries.devnetRun" in {finding["path"] for finding in packet.collect_findings(mutated)}

    mutated = json.loads(json.dumps(doc))
    mutated["layerRules"] = mutated["layerRules"][1:]
    assert "layerRules" in {finding["path"] for finding in packet.collect_findings(mutated)}
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
