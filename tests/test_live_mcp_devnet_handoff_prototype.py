#!/usr/bin/env python3
"""Live MCP/devnet payment handoff prototype evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "live-mcp-devnet-handoff-prototype.json"


def run_prototype() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/live_mcp_devnet_handoff_prototype.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_prototype()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["status"] == "pass"
    assert doc["mode"] == "live-mcp-devnet-payment-handoff-prototype"
    assert doc["boundaries"] == {
        "prototypeExecutionAllowed": True,
        "liveMcpResolutionAllowedByPolicy": True,
        "liveMcpInvocationAllowedByPolicy": True,
        "devnetPaymentHandoffAllowedByPolicy": True,
        "networkAccessUsed": False,
        "credentialAccessUsed": False,
        "walletAccessUsed": False,
        "paymentRailAccessUsed": False,
        "mcpInvocationUsed": False,
        "devnetAccessUsed": False,
        "mainnetAccessUsed": False,
        "externalSpendUsd": 0,
        "secretMaterialLogged": False,
    }
    assert doc["costEvidence"] == {
        "externalSpendUsd": 0,
        "devnetLamportsSpent": 0,
        "hostedProviderCalls": 0,
        "networkCalls": 0,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    passing = scenarios["approved-mcp-devnet-handoff"]
    mainnet_denied = scenarios["mainnet-payment-denied"]
    mcp_denied = scenarios["unreviewed-mcp-server-denied"]

    assert passing["completion"]["status"] == "pass"
    assert passing["mcp"]["mcpInvocationAllowed"] is True
    assert passing["mcp"]["mcpInvocationUsed"] is False
    assert passing["payment"]["paymentHandoffAllowed"] is True
    assert passing["payment"]["paymentRailAccessUsed"] is False
    assert passing["payment"]["devnetAccess"] is True
    assert passing["payment"]["mainnetAccess"] is False
    assert passing["receipt"]["network"] == "devnet"
    assert passing["receipt"]["productionSettlement"] is False
    assert passing["receipt"]["mainnetSettlement"] is False
    assert passing["rollbackPlan"]["cleanupVerified"] is True
    assert [event["event"] for event in passing["trace"]] == [
        "handoff.started",
        "mcp.allowlist_checked",
        "payment.devnet_policy_checked",
        "rollback.plan_registered",
        "handoff.completed",
    ]

    assert mainnet_denied["completion"]["status"] == "fail"
    assert mainnet_denied["payment"]["reason"] == "mainnet payment handoff is blocked pending separate approval"
    assert mainnet_denied["payment"]["paymentHandoffAllowed"] is False
    assert mainnet_denied["payment"]["paymentRailAccessUsed"] is False
    assert mainnet_denied["payment"]["mainnetAccess"] is False
    assert mainnet_denied["receipt"] is None

    assert mcp_denied["completion"]["status"] == "fail"
    assert mcp_denied["mcp"]["reason"] == "MCP serverRef is not in the reviewed allowlist"
    assert mcp_denied["mcp"]["mcpInvocationAllowed"] is False
    assert mcp_denied["mcp"]["mcpInvocationUsed"] is False
    assert mcp_denied["payment"]["devnetAccess"] is True
    assert mcp_denied["receipt"] is None

    print("PASS live MCP/devnet handoff prototype")
    return 0


if __name__ == "__main__":
    sys.exit(main())
