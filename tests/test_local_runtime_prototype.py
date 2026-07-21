#!/usr/bin/env python3
"""Executable local ADL runtime prototype evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "local-executable-runtime-prototype.json"


def run_prototype() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/local_runtime_prototype.py"],
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
    assert doc["mode"] == "local-executable-adl-runtime-prototype"
    assert doc["boundaries"] == {
        "localRuntimeExecutionAllowed": True,
        "deterministicLocalFixturesOnly": True,
        "networkAccess": False,
        "paymentAccess": False,
        "credentialAccess": False,
        "mcpInvocation": False,
        "mainnetAccess": False,
        "externalExecutionAllowed": False,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["simple-agent-dry-run"]["completion"]["status"] == "pass"
    assert scenarios["tool-agent-execute-tools"]["toolExecution"] == {
        "mode": "local-fixture",
        "networkAccess": False,
        "paymentAccess": False,
        "deniedCount": 0,
    }
    assert scenarios["tool-agent-execute-tools"]["sourceCheckSummary"]["status"] == "pass"
    assert scenarios["adl-v02-memory-observability-dry-run"]["completion"]["status"] == "pass"
    assert scenarios["adl-v02-memory-observability-dry-run"]["adl"] == "examples/v0.2/memory-observability-agent.yaml"
    assert scenarios["unsupported-tool-strict-denial"]["exitCode"] == 2
    assert scenarios["unsupported-tool-strict-denial"]["stderrFirstLine"].startswith("DENIED ")
    assert scenarios["unapproved-source-report-mode"]["completion"]["status"] == "fail"
    assert scenarios["unapproved-source-report-mode"]["sourceCheckSummary"]["requiredFailureCount"] == 1
    assert scenarios["invalid-runtime-validation"]["exitCode"] == 1
    assert scenarios["invalid-runtime-validation"]["stdoutFirstLine"].startswith("FAIL ")
    diagnostics = scenarios["invalid-adl-v02-payment-diagnostics"]["validationDiagnostics"]
    assert diagnostics
    first = diagnostics[0]
    assert first["code"].startswith("adl_v0_2_schema.")
    assert first["severity"] == "error"
    assert first["category"] == "payment"
    assert first["path"] == "extensions.x402.intents.0.authority"
    assert isinstance(first["line"], int)
    assert isinstance(first["column"], int)
    assert first["message"]
    print("PASS local executable ADL runtime prototype")
    return 0


if __name__ == "__main__":
    sys.exit(main())
