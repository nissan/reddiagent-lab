#!/usr/bin/env python3
"""Static MCP adapter aggregation checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_adapter_aggregation_check.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-adapter-aggregation-approved.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-adapter-aggregation-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []

    leaky = run_case("tests/fixtures/mcp-adapter-aggregation-leaky.json")
    assert leaky.returncode == 2
    leaky_doc = parse_json(leaky)
    assert leaky_doc["status"] == "fail"
    assert leaky_doc["networkAccess"] is False
    assert leaky_doc["mcpInvocation"] is False
    assert leaky_doc["paymentAccess"] is False

    reasons = [finding["reason"] for finding in leaky_doc["findings"]]
    assert "MCP adapter aggregation package must have a non-empty packageId." in reasons
    assert "MCP adapter aggregation must use aggregationMode=static-reviewed." in reasons
    assert "MCP adapter aggregation package must not claim network, invocation, or payment access." in reasons
    assert "MCP adapter aggregation must not expose raw runtime, server, auth, or environment details." in reasons
    assert "Passing MCP adapter outputs must include non-empty title, url, and snippet strings." in reasons
    assert "Passing MCP adapter results must not include error objects." in reasons
    assert "Aggregated MCP resultIds must be unique." in reasons
    assert "Aggregated MCP result status must be pass, error, or denied." in reasons
    assert "Aggregated MCP results must not claim network, invocation, or payment access." in reasons
    assert "MCP adapter aggregate completion must match result statuses and counts." in reasons
    assert "MCP adapter aggregate completion must not claim network, invocation, or payment access." in reasons

    print("PASS MCP adapter aggregation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
