#!/usr/bin/env python3
"""Check static starter-code review manifest output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_plan(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/starter_code_plan.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/starter_code_plan.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_static_boundaries(plan: dict) -> None:
    assert plan["runtimeExecutionAllowed"] is False
    assert plan["networkAccess"] is False
    assert plan["paymentAccess"] is False
    assert plan["mcpInvocation"] is False
    assert plan["writesFiles"] is False
    assert plan["installsDependencies"] is False


def file_paths(plan: dict) -> list[str]:
    return [item["path"] for item in plan["plannedFiles"]]


def gate_ids(plan: dict) -> list[str]:
    return [item["id"] for item in plan["blockedGatesBeforeGeneration"]]


def main() -> int:
    plans = run_plan(
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
    )
    by_agent = {plan["agent"]: plan for plan in plans}

    simple = by_agent["simple-research-helper"]
    assert simple["format"] == "starter-code-review-manifest"
    assert simple["supported"] is True
    assert simple["target"] == {
        "language": "python",
        "packageLayout": "single-agent-starter",
        "generationMode": "manifest-only",
        "outputRoot": "starter/simple-research-helper",
    }
    assert simple["validation"]["status"] == "pass"
    assert simple["tools"]["toolCount"] == 0
    assert "starter/simple-research-helper/src/agent_harness.py" in file_paths(simple)
    assert "starter/simple-research-helper/.env.example" in file_paths(simple)
    assert "provider-runtime-review" in gate_ids(simple)
    assert_static_boundaries(simple)

    tool = by_agent["source-checker"]
    assert tool["tools"] == {
        "toolCount": 1,
        "toolIds": ["search_docs"],
        "fixtureCount": 1,
        "fixtureToolIds": ["search_docs"],
    }
    assert "starter/source-checker/fixtures/tools.json" in file_paths(tool)
    assert "starter/source-checker/tests/test_policy_eval_gates.py" in file_paths(tool)
    assert tool["metadataOnlyExtensions"] == []
    assert_static_boundaries(tool)

    payment = by_agent["paid-specialist-researcher"]
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    assert "runtime-target-review" in gate_ids(payment)
    assert "payment-rail-review" in gate_ids(payment)
    assert "starter/paid-specialist-researcher/tests/test_policy_eval_gates.py" in file_paths(payment)
    assert_static_boundaries(payment)

    invalid = run_command("--single", "examples/invalid/missing-instructions.yaml")
    assert invalid.returncode == 1
    invalid_plan = json.loads(invalid.stdout)
    assert invalid_plan["supported"] is False
    assert invalid_plan["validation"]["status"] == "fail"
    assert invalid_plan["plannedFiles"] == []
    assert "generator-implementation-review" in gate_ids(invalid_plan)
    assert_static_boundaries(invalid_plan)

    bad_single = run_command("--single", "examples/simple-agent.yaml", "examples/tool-agent.yaml")
    assert bad_single.returncode == 2
    assert "--single requires exactly one ADL path" in bad_single.stderr

    print("PASS starter code review manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
