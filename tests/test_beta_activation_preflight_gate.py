#!/usr/bin/env python3
"""Beta activation preflight gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-activation-preflight.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-preflight-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_preflight_gate  # noqa: E402


def run_preflight() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_activation_preflight_gate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def source_context() -> tuple[dict, dict, dict, dict, dict, dict]:
    pinned_decision = beta_activation_preflight_gate.load_json(beta_activation_preflight_gate.PINNED_DECISION_PACKAGE)
    current_decision = beta_activation_preflight_gate.current_decision_package()
    pinned_review = beta_activation_preflight_gate.load_json(beta_activation_preflight_gate.PINNED_REVIEW_PACKAGE)
    current_review = beta_activation_preflight_gate.current_review_package()
    pinned_runtime = beta_activation_preflight_gate.load_json(beta_activation_preflight_gate.PINNED_RUNTIME_PACKAGE)
    current_runtime = beta_activation_preflight_gate.current_runtime_package()
    return pinned_decision, current_decision, pinned_review, current_review, pinned_runtime, current_runtime


def assert_positive_mutation_fails(mutator, expected_path: str, context: tuple[dict, dict, dict, dict, dict, dict]) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = scenarios["scenarios"][0]
    mutator(positive)
    result = beta_activation_preflight_gate.build_result(positive, *context)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_preflight()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-activation-preflight-gate"
    assert doc["issue"] == 258
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"]["activationPreflightPackage"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    evidence = doc["sourcePackageEvidence"]
    assert evidence["decisionPackage"]["status"] == "pass"
    assert evidence["decisionPackage"]["currentEvidenceMatchesPinned"] is True
    assert evidence["reviewPackage"]["currentEvidenceMatchesPinned"] is True
    assert evidence["runtimePackage"]["currentEvidenceMatchesPinned"] is True

    assert doc["summary"] == {
        "approvePreflights": 8,
        "holdPreflights": 2,
        "rollbackPreflights": 2,
        "positiveScenarios": 3,
        "negativeScenarios": 9,
        "failClosedScenarios": 9,
    }
    results = {result["id"]: result for result in doc["results"]}
    expected_activation_status = {
        "activation-approve-preflight-pass": "approve-preflight",
        "activation-hold-preflight-pass": "hold-preflight",
        "activation-rollback-preflight-pass": "rollback-preflight",
    }
    for result_id, activation_status in expected_activation_status.items():
        result = results[result_id]
        assert result["status"] == "pass"
        assert result["activationStatus"] == activation_status
        assert result["releaseId"] == "reddiagent-beta-0"
        assert result["selectedAdlPath"] == "examples/tool-agent.yaml"
        assert result["sourceDecisionPackagePath"] == "tests/fixtures/beta-operator-decision-package.json"
        assert result["sourceReviewPackagePath"] == "tests/fixtures/beta-review-ui.json"
        assert result["sourceRuntimePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
        assert result["operatorIdentity"] == "operator://local-beta"
        assert result["sourceDecisionTimestamp"].startswith("fixture://")
        assert result["preflightTimestamp"].startswith("fixture://")
        assert result["rollbackCue"] == "rollback://beta-0/local-operator-control-drill"
        assert result["sourceDecision"]["status"] == "pass"
        assert all(item["exists"] and item["sha256"] for item in result["evidenceHashes"])

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "sourceDecisionPackagePath" in finding_paths["missing-decision-package-evidence-denied"]
    assert "releaseId" in finding_paths["mismatched-release-id-denied"]
    assert "selectedAdlPath" in finding_paths["mismatched-adl-path-denied"]
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "rollbackCue" in finding_paths["missing-rollback-cue-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-runtime-request-denied"]
    assert "boundaryStatus.liveRuntimeActivation" in finding_paths["live-runtime-request-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-production-claim-denied"]
    assert "productionEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "mainnetEnabled" in finding_paths["mainnet-production-claim-denied"]

    context = source_context()
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorIdentity": ""}), "operatorIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceDecisionPackagePath": "tests/fixtures/stale.json"}), "sourceDecisionPackagePath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"selectedAdlPath": "examples/simple-agent.yaml"}), "selectedAdlPath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceDecisionTimestamp": ""}), "sourceDecisionTimestamp", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"liveRuntimeRequested": 1}), "liveRuntimeRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": 1}), "devnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": 1}), "mainnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"apiKey": "redacted fixture marker"}), "scenario.apiKey", context)
    assert_positive_mutation_fails(
        lambda scenario: scenario["boundaryStatus"].update({"credentialAccess": True}),
        "boundaryStatus.credentialAccess",
        context,
    )
    print("PASS beta activation preflight gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
