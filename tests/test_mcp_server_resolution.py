#!/usr/bin/env python3
"""Static MCP server resolution checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ADL = "examples/mcp-readonly-agent.yaml"


def run_case(registry: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_server_resolution_check.py", ADL, "--registry", registry],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    approved = run_case("tests/fixtures/mcp-server-registry-approved.json")
    assert approved.returncode == 0
    approved_doc = parse_json(approved)
    assert approved_doc["mode"] == "static-mcp-server-resolution-check"
    assert approved_doc["status"] == "pass"
    assert approved_doc["networkAccess"] is False
    assert approved_doc["mcpInvocation"] is False
    assert approved_doc["paymentAccess"] is False
    assert approved_doc["findings"] == []

    missing = run_case("tests/fixtures/mcp-server-registry-empty.json")
    assert missing.returncode == 2
    missing_doc = parse_json(missing)
    assert missing_doc["status"] == "fail"
    assert missing_doc["findings"][0] == {
        "toolId": "docs_search",
        "serverRef": "approved-docs-search",
        "status": "fail",
        "reason": "MCP serverRef is not present in the static reviewed registry.",
    }

    live = run_case("tests/fixtures/mcp-server-registry-live.json")
    assert live.returncode == 2
    live_doc = parse_json(live)
    reasons = [finding["reason"] for finding in live_doc["findings"]]
    assert "MCP serverRef is not marked static-reviewed." in reasons
    assert "MCP server registry embeds live resolution fields." in reasons
    assert "Static server resolution checks must not grant network access or MCP invocation." in reasons
    assert "MCP serverRef must declare approved-source-output as its source gate." in reasons
    live_fields = [finding for finding in live_doc["findings"] if finding["reason"] == "MCP server registry embeds live resolution fields."][0]["fields"]
    assert live_fields == ["command", "env", "url"]

    print("PASS MCP server resolution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
