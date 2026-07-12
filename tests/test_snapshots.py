#!/usr/bin/env python3
"""Compare deterministic dry-run outputs to committed snapshots."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_json(args: list[str]) -> object:
    proc = subprocess.run([PYTHON, *args], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def assert_snapshot(name: str, value: object) -> None:
    path = ROOT / "tests" / "snapshots" / name
    expected = json.loads(path.read_text())
    assert value == expected, f"snapshot mismatch: {name}"


def main() -> int:
    assert_snapshot("simple-agent.trace.json", run_json(["scripts/run_local_agent.py", "examples/simple-agent.yaml"]))
    assert_snapshot("tool-agent.trace.json", run_json(["scripts/run_local_agent.py", "examples/tool-agent.yaml"]))
    assert_snapshot(
        "tool-agent.executed.trace.json",
        run_json(["scripts/run_local_agent.py", "examples/tool-agent.yaml", "--execute-tools"]),
    )
    assert_snapshot("provider-compatibility.json", run_json(["scripts/provider_compatibility.py"]))
    assert_snapshot("payment-agent.receipt.json", run_json(["scripts/dry_run_receipt.py"]))
    print("PASS snapshots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
