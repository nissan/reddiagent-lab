#!/usr/bin/env python3
"""Check beta operator local dry-run package evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package.json"


def run_package() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_operator_dry_run_package.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    doc = run_package()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-operator-dry-run-package"
    assert doc["issue"] == 240
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"] == {
        "operatorFacingLocalDryRun": True,
        "deterministicLocalFixturesOnly": True,
        "liveRuntimeActivation": False,
        "networkAccess": False,
        "credentialAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "providerApiAccess": False,
        "devnetAccess": False,
        "productionGatewayAccess": False,
        "mainnetAccess": False,
        "externalSpend": False,
    }
    assert "Mainnet deployment" in doc["mainnetStatement"]
    results = {result["id"]: result for result in doc["results"]}
    positive = results["local-operator-dry-run-package-pass"]
    assert positive["status"] == "pass"
    assert positive["operatorIdentity"] == "operator://local-beta"
    assert positive["selectedAdlPath"] == "examples/tool-agent.yaml"
    assert positive["rcGateEvidence"]["status"] == "pass"
    assert positive["rcGateEvidence"]["currentEvidenceMatchesPinned"] is True
    assert positive["rcGateEvidence"]["selectedRuntimeCompletion"] == "pass"
    assert len(positive["evidenceIndex"]) == 6
    assert all(item["exists"] and item["sha256"] for item in positive["evidenceIndex"])

    assert results["missing-operator-identity-denied"]["status"] == "fail"
    assert results["missing-selected-adl-path-denied"]["status"] == "fail"
    assert results["missing-stop-rollback-transcript-denied"]["status"] == "fail"
    assert results["stale-rc-gate-evidence-denied"]["status"] == "fail"
    assert results["non-local-runtime-request-denied"]["status"] == "fail"
    assert results["mainnet-request-denied"]["status"] == "fail"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "selectedAdlPath" in finding_paths["missing-selected-adl-path-denied"]
    assert "stopRollbackDryRunTranscript" in finding_paths["missing-stop-rollback-transcript-denied"]
    assert "rcGate.releaseId" in finding_paths["stale-rc-gate-evidence-denied"]
    assert "runtimeMode" in finding_paths["non-local-runtime-request-denied"]
    assert "liveRuntimeRequested" in finding_paths["non-local-runtime-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-request-denied"]
    print("PASS beta operator local dry-run package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
