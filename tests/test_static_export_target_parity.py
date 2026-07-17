#!/usr/bin/env python3
"""Check static export target parity matrix fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "static-export-target-parity-matrix.json"


def run_parity(*args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/static_export_target_parity.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def row(agent: dict, target: str) -> dict:
    matches = [item for item in agent["rows"] if item["target"] == target]
    assert len(matches) == 1
    return matches[0]


def summary(payload: dict, target: str) -> dict:
    matches = [item for item in payload["targetSummary"] if item["target"] == target]
    assert len(matches) == 1
    return matches[0]


def assert_static_boundaries(item: dict) -> None:
    assert item["runtimeExecutionAllowed"] is False
    assert item["networkAccess"] is False
    assert item["paymentAccess"] is False
    assert item["mcpInvocation"] is False


def main() -> int:
    payload = run_parity()
    fixture_payload = json.loads(FIXTURE.read_text())
    assert payload == fixture_payload

    assert payload["format"] == "static-export-target-parity-matrix"
    assert payload["issue"] == 196
    assert payload["sources"] == [
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
        "examples/invalid/missing-instructions.yaml",
    ]
    assert payload["targetOrder"] == [
        "agent-spec",
        "a2a-agent-card",
        "agent-skills-skill-md",
        "starter-manifest",
        "provider-compatibility",
        "rap-bridge",
        "vercel-eve",
    ]
    assert_static_boundaries(payload)

    by_agent = {agent["agent"]: agent for agent in payload["agents"]}
    simple = by_agent["simple-research-helper"]
    payment = by_agent["paid-specialist-researcher"]
    invalid = by_agent["invalid-missing-instructions"]

    assert row(simple, "vercel-eve")["readiness"] == "metadata-only"
    assert row(simple, "vercel-eve")["blockedBy"] == []
    assert row(simple, "vercel-eve")["authoritativeCheck"] == (
        "tests/test_eve_compatibility.py"
    )
    assert row(simple, "vercel-eve")["command"] == (
        "python3 scripts/eve_compatibility.py --single examples/simple-agent.yaml"
    )
    assert_static_boundaries(row(simple, "vercel-eve"))

    assert row(payment, "agent-spec")["readiness"] == "metadata-only"
    assert row(payment, "rap-bridge")["readiness"] == "report-ready"
    assert row(payment, "vercel-eve")["metadataOnlyExtensions"] == [
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert "extensions.x402" in row(payment, "vercel-eve")["metadataOnlySections"]
    assert row(payment, "vercel-eve")["readiness"] == "metadata-only"
    assert row(payment, "vercel-eve")["blockedBy"] == [
        "non_local_runtime_execution",
        "live_payment_execution",
    ]
    assert_static_boundaries(row(payment, "vercel-eve"))

    assert invalid["supported"] is False
    assert row(invalid, "agent-spec")["readiness"] == "blocked-by-validation"
    assert row(invalid, "vercel-eve")["readiness"] == "blocked-by-validation"
    assert row(invalid, "vercel-eve")["blockedBy"] == ["validation_failed"]
    assert_static_boundaries(row(invalid, "vercel-eve"))

    eve_summary = summary(payload, "vercel-eve")
    assert eve_summary["agentCount"] == 4
    assert eve_summary["readinessCounts"] == {
        "metadata-only": 3,
        "blocked-by-validation": 1,
    }
    assert eve_summary["blockedBy"] == [
        "live_payment_execution",
        "non_local_runtime_execution",
        "validation_failed",
    ]
    assert "extensions.reputation" in eve_summary["metadataOnly"]
    assert_static_boundaries(eve_summary)

    print("PASS static export target parity matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
