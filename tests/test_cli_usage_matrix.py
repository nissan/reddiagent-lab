#!/usr/bin/env python3
"""CLI usage matrix checks for the local ReddiAgent runner."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"
RUNNER = "scripts/run_local_agent.py"


def run_case(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, RUNNER, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    validation = run_case("examples/invalid/bad-tool-id.yaml")
    assert validation.returncode == 1
    assert validation.stdout.startswith("FAIL examples/invalid/bad-tool-id.yaml")
    assert "Reference: specs/TOOL-REGISTRY-v0.1.md" in validation.stdout
    assert validation.stderr == ""

    strict_denied = run_case("examples/unsafe/undeclared-tool-fixture.yaml", "--execute-tools")
    assert strict_denied.returncode == 2
    assert strict_denied.stdout == ""
    assert strict_denied.stderr.startswith("DENIED examples/unsafe/undeclared-tool-fixture.yaml")
    assert "Why it matters" in strict_denied.stderr

    allowed_denied = run_case(
        "examples/unsafe/undeclared-tool-fixture.yaml",
        "--execute-tools",
        "--allow-denied-tools",
    )
    assert allowed_denied.returncode == 0
    allowed_doc = parse_json(allowed_denied)
    assert allowed_doc["completion"]["status"] == "fail"
    assert allowed_doc["toolExecution"]["deniedCount"] == 1
    assert allowed_doc["toolExecution"]["results"][0]["guidance"]["reference"] == (
        "specs/TOOL-REGISTRY-v0.1.md"
    )

    source_failure = run_case(
        "examples/unsafe/unapproved-source-fixture.yaml",
        "--execute-tools",
        "--allow-denied-tools",
    )
    assert source_failure.returncode == 0
    source_doc = parse_json(source_failure)
    assert source_doc["completion"]["status"] == "fail"
    assert source_doc["sourceCheckSummary"]["requiredFailureCount"] == 1
    assert source_doc["sourceChecks"][0]["guidance"]["reference"] == (
        "specs/DATA-SOURCE-CONTRACT-v0.1.md"
    )

    required_gate_shell_failure = run_case(
        "examples/unsafe/unapproved-source-fixture.yaml",
        "--execute-tools",
        "--allow-denied-tools",
        "--fail-on-required-gate",
    )
    assert required_gate_shell_failure.returncode == 3
    shell_doc = parse_json(required_gate_shell_failure)
    assert shell_doc["completion"]["transportStatus"] == "pass"
    assert shell_doc["completion"]["requiredGateStatus"] == "fail"
    assert shell_doc["completion"]["status"] == "fail"

    print("PASS CLI usage matrix")
    return 0


if __name__ == "__main__":
    sys.exit(main())
