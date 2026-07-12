#!/usr/bin/env python3
"""Static MCP runtime handoff package checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_case(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/mcp_runtime_handoff_package.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    ready = run_case("tests/fixtures/mcp-runtime-handoff-ready.json")
    assert ready.returncode == 0
    ready_doc = parse_json(ready)
    assert ready_doc["mode"] == "static-mcp-runtime-handoff-package-check"
    assert ready_doc["status"] == "pass"
    assert ready_doc["handoffReady"] is True
    assert ready_doc["runtimeExecutionAllowed"] is False
    assert ready_doc["networkAccess"] is False
    assert ready_doc["paymentAccess"] is False
    assert ready_doc["mcpInvocation"] is False
    assert ready_doc["findings"] == []

    unsafe = run_case("tests/fixtures/mcp-runtime-handoff-unsafe.json")
    assert unsafe.returncode == 2
    unsafe_doc = parse_json(unsafe)
    assert unsafe_doc["status"] == "fail"
    assert unsafe_doc["handoffReady"] is False
    reasons = [finding["reason"] for finding in unsafe_doc["findings"]]
    assert "MCP runtime handoff package must use mode=static-report-only." in reasons
    assert "MCP runtime handoff package must set runtime/network/payment/MCP access flags to false." in reasons
    assert "MCP runtime handoff packages must not include live runtime, credential, payment, or raw prompt fields." in reasons
    assert "Missing required MCP runtime handoff evidence gate: mcp-adapter-aggregation." in reasons
    assert "Server manifest resolutionMode must be static-reviewed." in reasons
    assert "MCP runtime handoff constraints must fail closed." in reasons
    assert "Missing required MCP readiness trace event: mcp.adapter_aggregation_checked." in reasons
    assert "Readiness trace events must preserve static access flags." in reasons

    print("PASS MCP runtime handoff package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
