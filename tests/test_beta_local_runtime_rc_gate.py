#!/usr/bin/env python3
"""Beta local runtime release-candidate gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-local-runtime-rc-gate.json"


def run_gate() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_local_runtime_rc_gate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_gate()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-runtime-release-candidate-gate"
    assert doc["issue"] == 237
    assert doc["status"] == "pass"
    assert doc["boundaries"] == {
        "localRuntimeExecutionAllowed": True,
        "deterministicLocalFixturesOnly": True,
        "networkAccess": False,
        "credentialAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "providerApiAccess": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "externalSpend": False,
    }
    assert "Mainnet deployment" in doc["mainnetStatement"]
    results = {result["id"]: result for result in doc["results"]}
    positive = results["local-tool-runtime-rc-pass"]
    assert positive["status"] == "pass"
    assert positive["selectedRuntime"]["completionStatus"] == "pass"
    assert positive["costEstimate"]["withinCeiling"] is True
    assert positive["privacyRedaction"]["rawPromptLogging"] == "redacted"
    assert positive["rollbackStopEvidence"]["stopFirst"] is True
    assert positive["mainnetApproval"]["approved"] is False
    assert positive["mainnetApproval"]["requested"] is False
    assert positive["operatorControlEvidence"]["traceEvents"]

    assert results["missing-enable-control-denied"]["status"] == "fail"
    assert results["missing-disable-control-denied"]["status"] == "fail"
    assert results["non-local-runtime-mode-denied"]["status"] == "fail"
    assert results["stale-readiness-evidence-denied"]["status"] == "fail"
    assert results["missing-rollback-stop-evidence-denied"]["status"] == "fail"
    assert results["mainnet-request-denied"]["status"] == "fail"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "operatorControls" in finding_paths["missing-enable-control-denied"]
    assert "operatorControls" in finding_paths["missing-disable-control-denied"]
    assert "runtimeMode" in finding_paths["non-local-runtime-mode-denied"]
    assert "readiness.releaseId" in finding_paths["stale-readiness-evidence-denied"]
    assert "rollback.stopFirst" in finding_paths["missing-rollback-stop-evidence-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-request-denied"]
    assert "readiness.approvals.mainnetApproved" in finding_paths["mainnet-request-denied"]
    print("PASS beta local runtime RC gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
