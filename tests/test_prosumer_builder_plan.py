#!/usr/bin/env python3
"""Check static Prosumer Builder MVP plan output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_plan(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/prosumer_builder_plan.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/prosumer_builder_plan.py", *args],
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


def step(plan: dict, step_id: str) -> dict:
    matches = [item for item in plan["flow"] if item["id"] == step_id]
    assert len(matches) == 1
    return matches[0]


def main() -> int:
    plans = run_plan(
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
    )
    by_agent = {plan["agent"]: plan for plan in plans}

    simple = by_agent["simple-research-helper"]
    assert simple["format"] == "prosumer-builder-mvp-plan"
    assert simple["supported"] is True
    assert simple["source"] == "examples/simple-agent.yaml"
    assert step(simple, "choose_job")["selection"]["agentName"] == "simple-research-helper"
    assert step(simple, "model_profile")["selection"]["preferredProvider"] == "openai"
    assert step(simple, "tool")["selection"]["toolCount"] == 0
    assert step(simple, "validate")["status"] == "pass"
    assert step(simple, "dry_run")["status"] == "ready"
    assert step(simple, "dry_run")["completionPreview"]["reason"] == (
        "dry-run transport completed and required gates passed"
    )
    assert step(simple, "dry_run")["tracePreview"][-1]["event"] == "task.dry_run_completed"
    assert step(simple, "trace")["expectedEvents"] == [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "task.dry_run_completed",
    ]
    assert step(simple, "export")["targets"][0]["target"] == "agent-spec"
    assert_static_boundaries(simple)

    tool = by_agent["source-checker"]
    assert step(tool, "tool")["selection"]["toolCount"] == 1
    assert step(tool, "tool")["selection"]["deterministicFixtureIds"] == ["search_docs"]
    assert "--execute-tools --fail-on-required-gate" in step(tool, "dry_run")["command"]
    assert step(tool, "dry_run")["completionPreview"] == {
        "transportStatus": "pass",
        "requiredGateStatus": "pass",
        "status": "pass",
        "reason": "dry-run transport completed and required gates passed",
    }
    assert step(tool, "dry_run")["toolExecutionPreview"] == {
        "mode": "local-fixture",
        "networkAccess": False,
        "paymentAccess": False,
        "deniedCount": 0,
        "resultCount": 1,
        "resultStatuses": [{"toolId": "search_docs", "status": "success"}],
    }
    assert step(tool, "dry_run")["sourceCheckSummaryPreview"] == {
        "total": 1,
        "passCount": 1,
        "failCount": 0,
        "requiredFailureCount": 0,
        "status": "pass",
    }
    assert [event["event"] for event in step(tool, "dry_run")["tracePreview"]] == [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "tool.executed",
        "source.checked",
        "task.dry_run_completed",
    ]
    assert step(tool, "trace")["expectedEvents"] == [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "tool.executed",
        "source.checked",
        "task.dry_run_completed",
    ]
    assert_static_boundaries(tool)

    payment = by_agent["paid-specialist-researcher"]
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    assert step(payment, "validate")["status"] == "pass"
    assert step(payment, "dry_run")["completionPreview"]["requiredGateStatus"] == "pass"
    assert step(payment, "dry_run")["toolExecutionPreview"] is None
    assert step(payment, "export")["targets"][2]["target"] == "agent-skills-skill-md"
    assert_static_boundaries(payment)

    invalid = run_command("--single", "examples/invalid/missing-instructions.yaml")
    assert invalid.returncode == 1
    invalid_plan = json.loads(invalid.stdout)
    assert invalid_plan["supported"] is False
    assert step(invalid_plan, "validate")["status"] == "fail"
    assert step(invalid_plan, "dry_run")["status"] == "blocked"
    assert step(invalid_plan, "dry_run")["completionPreview"] is None
    assert step(invalid_plan, "dry_run")["tracePreview"] == []
    assert step(invalid_plan, "trace")["status"] == "blocked"
    assert invalid_plan["runtimeExecutionAllowed"] is False
    assert invalid_plan["networkAccess"] is False
    assert invalid_plan["paymentAccess"] is False
    assert invalid_plan["mcpInvocation"] is False

    print("PASS Prosumer Builder MVP plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
