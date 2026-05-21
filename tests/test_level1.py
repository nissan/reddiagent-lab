#!/usr/bin/env python3
"""Level 1 dry-run conformance checks for ReddiAgent examples."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_example(name: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/run_local_agent.py", f"examples/{name}"],
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


def main() -> int:
    for example in ["simple-agent.yaml", "tool-agent.yaml"]:
        doc = run_example(example)
        assert_level1(doc)
        print(f"PASS Level 1 {example}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

