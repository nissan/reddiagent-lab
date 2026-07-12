#!/usr/bin/env python3
"""Static MCP adapter fixture contract checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_adapter_contract_check.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-adapter-contract-approved.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-adapter-contract-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []

    malformed = run_case("tests/fixtures/mcp-adapter-contract-malformed.json")
    assert malformed.returncode == 2
    malformed_doc = parse_json(malformed)
    assert malformed_doc["status"] == "fail"
    assert malformed_doc["networkAccess"] is False
    assert malformed_doc["mcpInvocation"] is False
    assert malformed_doc["paymentAccess"] is False

    reasons = [finding["reason"] for finding in malformed_doc["findings"]]
    assert "MCP adapter fixture identity fields must be non-empty strings." in reasons
    assert "MCP adapter fixture must not embed live server, process, auth, or credential fields." in reasons
    assert "MCP adapter fixture must not claim network, invocation, or payment access." in reasons
    assert "MCP adapter fixture output must include non-empty title, url, and snippet strings." in reasons

    print("PASS MCP adapter contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
