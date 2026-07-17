#!/usr/bin/env python3
"""Beta release readiness guard checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-release-readiness.json"


def run_checker(path: Path = FIXTURE) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/beta_release_readiness.py", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def load_ready() -> dict:
    return json.loads(FIXTURE.read_text())


def main() -> int:
    proc = run_checker()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(proc.stdout)
    assert report["mode"] == "beta-release-readiness-check"
    assert report["releaseId"] == "reddiagent-beta-0"
    assert report["status"] == "pass"
    assert report["findings"] == []
    assert report["summary"]["mainnetApproved"] is False
    assert report["summary"]["operatorControls"] >= 6
    assert report["summary"]["sampleTraceEvents"] >= 11

    ready = load_ready()
    assert ready["approvals"]["devnetApproved"] is True
    assert ready["approvals"]["mainnetApproved"] is False
    assert "separate signoff" in ready["approvals"]["mainnetStatement"]
    assert "tests/LIVE-MCP-DEVNET-HANDOFF-PROTOTYPE-REPORT.md" in ready["requiredReleaseEvidence"]
    assert "tests/BETA-RELEASE-READINESS-REPORT.md" in ready["requiredReleaseEvidence"]
    assert "tests/fixtures/beta-release-readiness.json" in ready["requiredReleaseEvidence"]
    assert ready["observability"]["rawSecretLoggingAllowed"] is False
    assert ready["observability"]["rawPromptLoggingDefault"] == "redacted"
    assert ready["rollback"]["stopFirst"] is True
    assert ready["rollback"]["mainnetRollback"] == "not-applicable-mainnet-not-approved"

    unsafe = copy.deepcopy(ready)
    unsafe["approvals"]["mainnetApproved"] = True
    unsafe["operatorControls"] = [control for control in unsafe["operatorControls"] if control["id"] != "pause-payment-handoff"]
    unsafe["observability"]["rawSecretLoggingAllowed"] = True
    unsafe["requiredReleaseEvidence"].remove("tests/BETA-RELEASE-READINESS-REPORT.md")
    unsafe["requiredReleaseEvidence"].remove("tests/fixtures/beta-release-readiness.json")
    unsafe["sampleTraceEvents"] = [
        event for event in unsafe["sampleTraceEvents"] if event["event"] != "runtime.disabled"
    ]

    with tempfile.TemporaryDirectory() as tmp:
        unsafe_path = Path(tmp) / "unsafe.json"
        unsafe_path.write_text(json.dumps(unsafe))
        unsafe_proc = run_checker(unsafe_path)
    assert unsafe_proc.returncode == 3
    unsafe_report = json.loads(unsafe_proc.stdout)
    assert unsafe_report["status"] == "fail"
    finding_paths = {finding["path"] for finding in unsafe_report["findings"]}
    assert "approvals.mainnetApproved" in finding_paths
    assert "requiredReleaseEvidence" in finding_paths
    assert "operatorControls" in finding_paths
    assert "observability.rawSecretLoggingAllowed" in finding_paths
    assert "sampleTraceEvents" in finding_paths

    print("PASS beta release readiness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
