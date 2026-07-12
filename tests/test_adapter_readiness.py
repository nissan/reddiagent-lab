#!/usr/bin/env python3
"""Adapter readiness checks for read-only MCP shapes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/adapter_readiness.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    positive = run_case("examples/mcp-readonly-agent.yaml")
    assert positive.returncode == 0
    positive_doc = parse_json(positive)
    assert positive_doc["status"] == "pass"
    assert positive_doc["mode"] == "read-only-adapter-shape"
    assert positive_doc["adapter"] == "mcp"
    assert positive_doc["mcpToolCount"] == 1
    assert positive_doc["networkAccess"] is False
    assert positive_doc["mcpInvocation"] is False
    assert positive_doc["paymentAccess"] is False
    assert positive_doc["findings"] == []

    negative = run_case("examples/unsafe/mcp-live-server-fixture.yaml")
    assert negative.returncode == 2
    negative_doc = parse_json(negative)
    assert negative_doc["status"] == "fail"
    assert negative_doc["networkAccess"] is False
    assert negative_doc["mcpInvocation"] is False
    assert negative_doc["paymentAccess"] is False
    assert negative_doc["findings"][0]["toolId"] == "live_docs_search"
    assert "live execution fields" in negative_doc["findings"][0]["reason"]
    assert negative_doc["findings"][0]["fields"] == ["command", "env", "serverUrl"]

    print("PASS adapter readiness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
