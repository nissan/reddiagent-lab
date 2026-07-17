#!/usr/bin/env python3
"""Beta operator-control harness checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-control-scenarios.json"
FIXTURE = ROOT / "tests" / "fixtures" / "beta-operator-control-harness.json"


def run_harness(path: Path = SCENARIOS) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/beta_operator_control_harness.py", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def main() -> int:
    proc = run_harness()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(proc.stdout)
    assert report == json.loads(FIXTURE.read_text())
    assert report["mode"] == "beta-operator-control-harness"
    assert report["issue"] == 235
    assert report["status"] == "pass"
    assert report["findings"] == []
    assert report["summary"] == {
        "failClosedScenarios": 4,
        "mainnetApproved": False,
        "negativeScenarios": 4,
        "positiveScenarios": 1,
    }
    assert report["boundaries"] == {
        "credentialAccess": False,
        "externalSpend": False,
        "localOnly": True,
        "mainnetAccess": False,
        "mcpInvocation": False,
        "networkAccess": False,
        "paymentAccess": False,
        "providerApiAccess": False,
    }

    results = {result["id"]: result for result in report["results"]}
    assert results["local-operator-control-drill"]["completionStatus"] == "pass"
    assert results["local-operator-control-drill"]["enabledRuntimePath"] == "local-runtime-prototype"
    assert results["mainnet-enable-denied"]["reason"] == "mainnet-not-approved"
    assert results["mainnet-enable-denied"]["failClosed"] is True
    assert results["rollback-stop-missing"]["reason"] == "rollback-stop-not-verified"
    assert results["cost-ceiling-forces-local-only"]["reason"] == "cost-ceiling-exceeded"
    assert results["privacy-payload-denied"]["reason"] == "sensitive-payload-denied"
    all_events = {event["event"] for result in report["results"] for event in result["traceEvents"]}
    assert set(report["requiredEvents"]) <= all_events

    unsafe = json.loads(SCENARIOS.read_text())
    unsafe["approvals"]["mainnetApproved"] = True
    unsafe["approvals"]["mainnetStatement"] = "Mainnet is approved."
    unsafe["boundaries"]["mainnetAccess"] = True
    unsafe["scenarios"] = [copy.deepcopy(unsafe["scenarios"][0])]
    unsafe["scenarios"][0]["expectedCompletionStatus"] = "fail"
    with tempfile.TemporaryDirectory() as tmp:
        unsafe_path = Path(tmp) / "unsafe.json"
        unsafe_path.write_text(json.dumps(unsafe))
        unsafe_proc = run_harness(unsafe_path)
    assert unsafe_proc.returncode == 3
    unsafe_report = json.loads(unsafe_proc.stdout)
    finding_paths = {finding["path"] for finding in unsafe_report["findings"]}
    assert "approvals.mainnetApproved" in finding_paths
    assert "approvals.mainnetStatement" in finding_paths
    assert "boundaries.mainnetAccess" in finding_paths
    assert "scenarios" in finding_paths
    assert "results[0].completionStatus" in finding_paths

    print("PASS beta operator-control harness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
