#!/usr/bin/env python3
"""Static MCP capability policy checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ADL = "examples/mcp-readonly-agent.yaml"


def run_case(policy: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_capability_policy_check.py", ADL, "--policy", policy],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-capability-policy-approved.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-capability-policy-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []

    missing = run_case("tests/fixtures/mcp-capability-policy-empty.json")
    assert missing.returncode == 2
    missing_doc = parse_json(missing)
    assert missing_doc["findings"] == [
        {
            "toolId": "docs_search",
            "serverRef": "approved-docs-search",
            "status": "fail",
            "reason": "MCP tool has no matching static capability policy.",
        }
    ]

    overbroad = run_case("tests/fixtures/mcp-capability-policy-overbroad.json")
    assert overbroad.returncode == 2
    overbroad_doc = parse_json(overbroad)
    reasons = [finding["reason"] for finding in overbroad_doc["findings"]]
    assert "MCP capability policy grants capabilities outside readonly adapter inspection." in reasons
    assert "MCP capability policy must require approved-source-output." in reasons
    assert "MCP capability policy must not grant network, invocation, or payment access." in reasons
    extra = [
        finding
        for finding in overbroad_doc["findings"]
        if finding["reason"] == "MCP capability policy grants capabilities outside readonly adapter inspection."
    ][0]["extraCapabilities"]
    assert extra == ["network.fetch", "payment.spend"]

    print("PASS MCP capability policy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
