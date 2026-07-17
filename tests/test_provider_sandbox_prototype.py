#!/usr/bin/env python3
"""Provider-backed sandbox prototype evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "provider-sandbox-prototype.json"


def run_prototype() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/provider_sandbox_prototype.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_prototype()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["status"] == "pass"
    assert doc["mode"] == "provider-backed-sandbox-prototype"
    assert doc["costEvidence"] == {
        "hostedProviderCalls": 0,
        "externalSpendUsd": 0,
        "simulatedEstimatedCostUsd": 0.0001,
        "pricingModel": "fake local USD 0.000001 per token for deterministic budget evidence",
    }
    assert doc["boundaries"] == {
        "providerSandboxExecutionAllowed": True,
        "hostedProviderModelApiCalls": False,
        "networkAccess": False,
        "credentialAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "externalSpendUsd": 0,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    passing = scenarios["simple-agent-fake-provider-pass"]
    budget_fail = scenarios["simple-agent-fake-provider-budget-fail"]
    assert passing["completion"]["status"] == "pass"
    assert passing["budget"]["status"] == "pass"
    assert passing["evals"]["status"] == "pass"
    assert passing["provider"]["hostedProviderCall"] is False
    assert passing["provider"]["credentialAccess"] is False
    assert [event["event"] for event in passing["trace"]] == [
        "provider.sandbox_started",
        "provider.prompt_prepared",
        "provider.response_received",
        "budget.checked",
        "eval.checked",
        "provider.sandbox_completed",
    ]
    assert budget_fail["completion"]["status"] == "fail"
    assert budget_fail["budget"]["status"] == "fail"
    assert budget_fail["evals"]["status"] == "pass"
    failed_budget_ids = {
        check["id"] for check in budget_fail["budget"]["checks"] if check["status"] == "fail"
    }
    assert failed_budget_ids == {
        "prompt-token-budget",
        "completion-token-budget",
        "total-token-budget",
        "estimated-cost-budget",
    }
    print("PASS provider sandbox prototype")
    return 0


if __name__ == "__main__":
    sys.exit(main())
