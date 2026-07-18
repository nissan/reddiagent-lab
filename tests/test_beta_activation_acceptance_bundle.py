#!/usr/bin/env python3
"""Beta activation acceptance bundle checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-activation-acceptance.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-acceptance-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_acceptance_bundle  # noqa: E402


def run_acceptance() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_activation_acceptance_bundle.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def source_context() -> tuple[dict, dict]:
    pinned_rehearsal = beta_activation_acceptance_bundle.load_json(
        beta_activation_acceptance_bundle.PINNED_REHEARSAL_PACKAGE
    )
    current_rehearsal = beta_activation_acceptance_bundle.current_rehearsal_package()
    return pinned_rehearsal, current_rehearsal


def assert_positive_mutation_fails(mutator, expected_path: str, context: tuple[dict, dict]) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = beta_activation_acceptance_bundle.merge_scenario(scenarios["defaults"], scenarios["scenarios"][0])
    mutator(positive)
    result = beta_activation_acceptance_bundle.build_result(positive, *context)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_acceptance()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-activation-acceptance-bundle"
    assert doc["issue"] == 262
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"]["activationAcceptanceBundle"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    evidence = doc["sourcePackageEvidence"]["rehearsalPackage"]
    assert evidence["source"] == "tests/fixtures/beta-activation-rehearsal.json"
    assert evidence["status"] == "pass"
    assert evidence["currentEvidenceMatchesPinned"] is True

    assert doc["summary"] == {
        "acceptBundles": 14,
        "holdBundles": 1,
        "rollbackRequiredBundles": 2,
        "positiveScenarios": 3,
        "negativeScenarios": 14,
        "failClosedScenarios": 14,
    }
    results = {result["id"]: result for result in doc["results"]}
    expected_acceptance_status = {
        "activation-acceptance-pass": "acceptance-ready",
        "activation-hold-acceptance-pass": "acceptance-held",
        "activation-rollback-required-acceptance-pass": "rollback-required",
    }
    for result_id, acceptance_status in expected_acceptance_status.items():
        result = results[result_id]
        assert result["status"] == "pass"
        assert result["acceptanceStatus"] == acceptance_status
        assert result["releaseId"] == "reddiagent-beta-0"
        assert result["selectedAdlPath"] == "examples/tool-agent.yaml"
        assert result["sourceRehearsalPackagePath"] == "tests/fixtures/beta-activation-rehearsal.json"
        assert result["sourcePreflightPackagePath"] == "tests/fixtures/beta-activation-preflight.json"
        assert result["sourceDecisionPackagePath"] == "tests/fixtures/beta-operator-decision-package.json"
        assert result["sourceReviewPackagePath"] == "tests/fixtures/beta-review-ui.json"
        assert result["sourceRuntimePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
        assert result["operatorIdentity"] == "operator://local-beta"
        assert result["reviewerIdentity"] == "reviewer://oli-local-fixture"
        assert result["localApprovalFixture"].startswith("tests/fixtures/beta-activation-rehearsal.json#")
        assert result["acceptanceTimestamp"].startswith("fixture://")
        assert result["acceptedActivationCue"] == "activate://beta-0/local-rehearsal-only"
        assert result["rollbackCue"] == "rollback://beta-0/local-operator-control-drill"
        assert result["rollbackDisableEvidence"]["disableVerified"] is True
        assert result["rollbackDisableEvidence"]["dryRunOnly"] is True
        assert result["rollbackDisableEvidence"]["liveRuntimeEnabled"] is False
        assert result["liveRuntimeEnablementClaim"] == "none"
        assert "No live runtime enablement is claimed" in result["nextStepHandoff"]
        assert all(step["liveRuntimeEnabled"] is False and "--dry-run" in step["command"] for step in result["operatorTranscript"])
        assert any(step["event"] == "acceptance.no_live_enablement_handoff" for step in result["operatorTranscript"])
        assert all(item["status"] == "pass" for item in result["operatorChecklist"])
        assert all(item["exists"] and item["sha256"] for item in result["evidenceHashes"])

    assert "--cue activate://beta-0/local-rehearsal-only" in results["activation-acceptance-pass"]["operatorTranscript"][1]["command"]
    assert results["activation-hold-acceptance-pass"]["operatorTranscript"][1]["event"] == "acceptance.hold_recorded"
    assert "--cue rollback://beta-0/local-operator-control-drill" in results["activation-rollback-required-acceptance-pass"]["operatorTranscript"][1]["command"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "sourceRehearsalPackagePath" in finding_paths["missing-rehearsal-evidence-denied"]
    assert "releaseId" in finding_paths["mismatched-release-id-denied"]
    assert "selectedAdlPath" in finding_paths["mismatched-adl-path-denied"]
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "reviewerIdentity" in finding_paths["missing-reviewer-identity-denied"]
    assert "acceptedActivationCue" in finding_paths["missing-accepted-activation-cue-denied"]
    assert "rollbackCue" in finding_paths["missing-rollback-cue-denied"]
    assert "rollbackDisableEvidence.disableVerified" in finding_paths["missing-rollback-disable-evidence-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-runtime-request-denied"]
    assert "boundaryStatus.liveRuntimeActivation" in finding_paths["live-runtime-request-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-production-claim-denied"]
    assert "productionEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "mainnetEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "claimsLiveRuntimeEnablement" in finding_paths["live-runtime-enable-claim-denied"]
    assert "nextStepHandoff" in finding_paths["handoff-live-enable-claim-denied"]

    context = source_context()
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorIdentity": ""}), "operatorIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerIdentity": "", "localApprovalFixture": ""}), "reviewerIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceRehearsalPackagePath": "tests/fixtures/stale.json"}), "sourceRehearsalPackagePath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"selectedAdlPath": "examples/simple-agent.yaml"}), "selectedAdlPath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"acceptedActivationCue": ""}), "acceptedActivationCue", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"liveRuntimeRequested": 1}), "liveRuntimeRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": 1}), "devnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": 1}), "mainnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"apiKey": "redacted fixture marker"}), "scenario.apiKey", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepHandoff": "Activation completed."}), "nextStepHandoff", context)
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
    print("PASS beta activation acceptance bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
