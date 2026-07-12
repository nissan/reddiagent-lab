#!/usr/bin/env python3
"""Static MCP adapter error-semantics checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_adapter_error_semantics_check.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-adapter-error-approved.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-adapter-error-semantics-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []

    leaky = run_case("tests/fixtures/mcp-adapter-error-leaky.json")
    assert leaky.returncode == 2
    leaky_doc = parse_json(leaky)
    assert leaky_doc["status"] == "fail"
    assert leaky_doc["networkAccess"] is False
    assert leaky_doc["mcpInvocation"] is False
    assert leaky_doc["paymentAccess"] is False

    reasons = [finding["reason"] for finding in leaky_doc["findings"]]
    assert "MCP adapter error fixture status must be error or denied." in reasons
    assert "MCP adapter error fixture must not include output payload data." in reasons
    assert "MCP adapter errors must force required-gate failure." in reasons
    assert "MCP adapter error code is not in the reviewed static allowlist." in reasons
    assert "MCP adapter error retryability must be explicit." in reasons
    assert "MCP adapter error fixture must not claim network, invocation, or payment access." in reasons
    assert "MCP adapter error fixture must not expose raw runtime, server, auth, or environment details." in reasons

    print("PASS MCP adapter error semantics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
