#!/usr/bin/env python3
"""Level 1 dry-run conformance checks for ReddiAgent examples."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_example(name: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/run_local_agent.py", f"examples/{name}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_fixture(path: str) -> dict:
    proc = subprocess.run(
        [
            PYTHON,
            "scripts/run_local_agent.py",
            path,
            "--execute-tools",
            "--allow-denied-tools",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_level1(doc: dict) -> None:
    assert doc["mode"] == "dry-run"
    assert doc["level"] == 1
    assert doc["runtime"] == "local-python"
    assert isinstance(doc["trace"], list)
    events = [event["event"] for event in doc["trace"]]
    assert events == [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "task.dry_run_completed",
    ]
    trace_ids = {event["traceId"] for event in doc["trace"]}
    assert len(trace_ids) == 1
    assert doc["completion"]["transportStatus"] == "pass"
    assert doc["completion"]["requiredGateStatus"] == "pass"


def assert_fixture_gate_completion() -> None:
    approved = run_fixture("examples/tool-agent.yaml")
    assert approved["completion"]["transportStatus"] == "pass"
    assert approved["completion"]["requiredGateStatus"] == "pass"
    assert approved["sourceCheckSummary"]["requiredFailureCount"] == 0

    unapproved = run_fixture("examples/unsafe/unapproved-source-fixture.yaml")
    assert unapproved["completion"]["transportStatus"] == "pass"
    assert unapproved["completion"]["requiredGateStatus"] == "fail"
    assert unapproved["sourceCheckSummary"]["requiredFailureCount"] == 1

    denied = run_fixture("examples/unsafe/undeclared-tool-fixture.yaml")
    assert denied["completion"]["transportStatus"] == "pass"
    assert denied["completion"]["requiredGateStatus"] == "fail"
    assert denied["toolExecution"]["deniedCount"] == 1


def main() -> int:
    for example in ["simple-agent.yaml", "tool-agent.yaml"]:
        doc = run_example(example)
        assert_level1(doc)
        print(f"PASS Level 1 {example}")
    assert_fixture_gate_completion()
    print("PASS Level 1 fixture gate completion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
