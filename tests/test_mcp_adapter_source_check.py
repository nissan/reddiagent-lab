#!/usr/bin/env python3
"""MCP adapter output source-check fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_adapter_source_check.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-approved-output.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "deterministic-adapter-output-source-check"
    assert approved_doc["adapter"] == "mcp"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["status"] == "pass"
    assert approved_doc["sourceChecks"][0] == {
        "gateId": "approved-source-output",
        "toolId": "docs_search",
        "status": "pass",
        "title": "Tool Registry Contract v0.1",
        "url": "specs/TOOL-REGISTRY-v0.1.md",
        "message": "Tool output cites an approved in-repo source.",
    }

    unapproved = run_case("tests/fixtures/mcp-unapproved-output.json")
    assert unapproved.returncode == 2
    unapproved_doc = parse_json(unapproved)
    assert unapproved_doc["status"] == "fail"
    assert unapproved_doc["networkAccess"] is False
    assert unapproved_doc["mcpInvocation"] is False
    assert unapproved_doc["paymentAccess"] is False
    assert unapproved_doc["sourceCheckSummary"] == {
        "total": 1,
        "passCount": 0,
        "failCount": 1,
        "requiredFailureCount": 1,
        "status": "fail",
    }
    failed_check = unapproved_doc["sourceChecks"][0]
    assert failed_check["toolId"] == "docs_search"
    assert failed_check["status"] == "fail"
    assert failed_check["title"] == "Unreviewed MCP Source"
    assert failed_check["url"] == "https://example.invalid/mcp-source"
    assert failed_check["guidance"]["reference"] == "specs/DATA-SOURCE-CONTRACT-v0.1.md"
    assert "Source trust" in failed_check["guidance"]["why_it_matters"]

    print("PASS MCP adapter source checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
