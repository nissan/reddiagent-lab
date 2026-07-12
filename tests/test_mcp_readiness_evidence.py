#!/usr/bin/env python3
"""Static MCP readiness trace/evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(evidence: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_readiness_evidence_check.py", evidence],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-readiness-evidence-pass.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-readiness-evidence-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []
    assert approved_doc["observedEvents"] == approved_doc["requiredEvents"]

    failed = run_case("tests/fixtures/mcp-readiness-evidence-fail.json")
    assert failed.returncode == 2
    failed_doc = parse_json(failed)
    assert failed_doc["status"] == "fail"
    reasons = [finding["reason"] for finding in failed_doc["findings"]]
    assert "Missing required MCP readiness gate evidence event." in reasons
    assert "MCP readiness evidence must not claim network, invocation, or payment access." in reasons
    assert "MCP readiness completion status must match required gate status." in reasons

    print("PASS MCP readiness evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
