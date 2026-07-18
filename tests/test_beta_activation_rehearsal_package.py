#!/usr/bin/env python3
"""Beta activation rehearsal package checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-activation-rehearsal.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-rehearsal-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_rehearsal_package  # noqa: E402


def run_rehearsal() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_activation_rehearsal_package.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def source_context() -> tuple[dict, dict]:
    pinned_preflight = beta_activation_rehearsal_package.load_json(
        beta_activation_rehearsal_package.PINNED_PREFLIGHT_PACKAGE
    )
    current_preflight = beta_activation_rehearsal_package.current_preflight_package()
    return pinned_preflight, current_preflight


def assert_positive_mutation_fails(mutator, expected_path: str, context: tuple[dict, dict]) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = beta_activation_rehearsal_package.merge_scenario(scenarios["defaults"], scenarios["scenarios"][0])
    mutator(positive)
    result = beta_activation_rehearsal_package.build_result(positive, *context)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_rehearsal()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-activation-rehearsal-package"
    assert doc["issue"] == 260
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"]["activationRehearsalPackage"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    evidence = doc["sourcePackageEvidence"]["preflightPackage"]
    assert evidence["source"] == "tests/fixtures/beta-activation-preflight.json"
    assert evidence["status"] == "pass"
    assert evidence["currentEvidenceMatchesPinned"] is True

    assert doc["summary"] == {
        "approveRehearsals": 12,
        "holdRehearsals": 1,
        "rollbackRehearsals": 2,
        "positiveScenarios": 3,
        "negativeScenarios": 12,
        "failClosedScenarios": 12,
    }
    results = {result["id"]: result for result in doc["results"]}
    expected_rehearsal_status = {
        "activation-approve-rehearsal-pass": "approve-rehearsal-ready",
        "activation-hold-rehearsal-pass": "hold-rehearsal-ready",
        "activation-rollback-rehearsal-pass": "rollback-rehearsal-ready",
    }
    for result_id, rehearsal_status in expected_rehearsal_status.items():
        result = results[result_id]
        assert result["status"] == "pass"
        assert result["rehearsalStatus"] == rehearsal_status
        assert result["releaseId"] == "reddiagent-beta-0"
        assert result["selectedAdlPath"] == "examples/tool-agent.yaml"
        assert result["sourcePreflightPackagePath"] == "tests/fixtures/beta-activation-preflight.json"
        assert result["sourceDecisionPackagePath"] == "tests/fixtures/beta-operator-decision-package.json"
        assert result["sourceReviewPackagePath"] == "tests/fixtures/beta-review-ui.json"
        assert result["sourceRuntimePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
        assert result["operatorIdentity"] == "operator://local-beta"
        assert result["rehearsalTimestamp"].startswith("fixture://")
        assert result["rollbackCue"] == "rollback://beta-0/local-operator-control-drill"
        assert result["rollbackDisableEvidence"]["disableVerified"] is True
        assert result["rollbackDisableEvidence"]["dryRunOnly"] is True
        assert result["rollbackDisableEvidence"]["liveRuntimeEnabled"] is False
        assert result["liveRuntimeEnablementClaim"] == "none"
        assert all(step["liveRuntimeEnabled"] is False and "--dry-run" in step["command"] for step in result["operatorTranscript"])
        assert any(step["event"] == "rehearsal.rollback_disable_evidence_verified" for step in result["operatorTranscript"])
        assert all(item["status"] == "pass" for item in result["operatorChecklist"])
        assert all(item["exists"] and item["sha256"] for item in result["evidenceHashes"])

    assert "--cue activate://beta-0/local-rehearsal-only" in results["activation-approve-rehearsal-pass"]["operatorTranscript"][1]["command"]
    assert results["activation-hold-rehearsal-pass"]["operatorTranscript"][1]["event"] == "rehearsal.hold_cue_recorded"
    assert "--cue rollback://beta-0/local-operator-control-drill" in results["activation-rollback-rehearsal-pass"]["operatorTranscript"][1]["command"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "sourcePreflightPackagePath" in finding_paths["missing-preflight-evidence-denied"]
    assert "releaseId" in finding_paths["mismatched-release-id-denied"]
    assert "selectedAdlPath" in finding_paths["mismatched-adl-path-denied"]
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "activationCue" in finding_paths["missing-activation-cue-denied"]
    assert "rollbackCue" in finding_paths["missing-rollback-cue-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-runtime-request-denied"]
    assert "boundaryStatus.liveRuntimeActivation" in finding_paths["live-runtime-request-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-production-claim-denied"]
    assert "productionEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "mainnetEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "rollbackDisableEvidence.disableVerified" in finding_paths["missing-rollback-disable-evidence-denied"]
    assert "claimsLiveRuntimeEnablement" in finding_paths["live-runtime-enable-claim-denied"]

    context = source_context()
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorIdentity": ""}), "operatorIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourcePreflightPackagePath": "tests/fixtures/stale.json"}), "sourcePreflightPackagePath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"selectedAdlPath": "examples/simple-agent.yaml"}), "selectedAdlPath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"activationCue": ""}), "activationCue", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"liveRuntimeRequested": 1}), "liveRuntimeRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": 1}), "devnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": 1}), "mainnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"apiKey": "redacted fixture marker"}), "scenario.apiKey", context)
    assert_positive_mutation_fails(
        lambda scenario: scenario["rollbackDisableEvidence"].update({"disableVerified": False}),
        "rollbackDisableEvidence.disableVerified",
        context,
    )
    assert_positive_mutation_fails(
        lambda scenario: scenario["boundaryStatus"].update({"credentialAccess": True}),
        "boundaryStatus.credentialAccess",
        context,
    )
    print("PASS beta activation rehearsal package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
