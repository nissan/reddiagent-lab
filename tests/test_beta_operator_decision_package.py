#!/usr/bin/env python3
"""Check beta operator decision package evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-operator-decision-package.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-decision-package-scenarios.json"


def run_decision_package() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_operator_decision_package.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_decision_package_for_scenarios(doc: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "scenarios.json"
        path.write_text(json.dumps(doc))
        proc = subprocess.run(
            [PYTHON, "scripts/beta_operator_decision_package.py", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    assert proc.returncode == 3, proc.stdout
    return json.loads(proc.stdout)


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = scenarios["scenarios"][0]
    mutator(positive)
    doc = run_decision_package_for_scenarios(scenarios)
    result = doc["results"][0]
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_decision_package()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-operator-decision-package"
    assert doc["issue"] == 256
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"]["operatorDecisionPackage"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert "not approved" in doc["mainnetStatement"]

    review = doc["reviewPackageEvidence"]
    assert review["status"] == "pass"
    assert review["currentEvidenceMatchesPinned"] is True
    assert review["sourcePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
    assert review["selectedAdlPath"] == "examples/tool-agent.yaml"

    assert doc["summary"] == {
        "approveDecisions": 6,
        "holdDecisions": 2,
        "rollbackDecisions": 2,
        "positiveScenarios": 3,
        "negativeScenarios": 7,
        "failClosedScenarios": 7,
    }
    results = {result["id"]: result for result in doc["results"]}
    for result_id in {
        "operator-approve-decision-pass",
        "operator-hold-decision-pass",
        "operator-rollback-decision-pass",
    }:
        result = results[result_id]
        assert result["status"] == "pass"
        assert result["releaseId"] == "reddiagent-beta-0"
        assert result["selectedAdlPath"] == "examples/tool-agent.yaml"
        assert result["sourcePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
        assert result["operatorIdentity"] == "operator://local-beta"
        assert result["decisionTimestamp"].startswith("fixture://")
        assert result["rollbackCue"] == "rollback://beta-0/local-operator-control-drill"
        assert all(item["exists"] and item["sha256"] for item in result["evidenceHashes"])

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "rollbackCue" in finding_paths["missing-rollback-cue-denied"]
    assert "releaseId" in finding_paths["stale-review-package-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-runtime-request-denied"]
    assert "boundaryStatus.liveRuntimeActivation" in finding_paths["live-runtime-request-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-production-claim-denied"]
    assert "productionEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "mainnetEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "scenario.rawSecret" in finding_paths["credential-like-payload-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorIdentity": ""}), "operatorIdentity")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourcePackagePath": "tests/fixtures/stale.json"}), "sourcePackagePath")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"decisionTimestamp": ""}), "decisionTimestamp")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"liveRuntimeRequested": 1}), "liveRuntimeRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": 1}), "devnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": 1}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"productionEnabled": 1}), "productionEnabled")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetEnabled": 1}), "mainnetEnabled")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"apiKey": "redacted fixture marker"}), "scenario.apiKey")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"Authorization": "redacted fixture marker"}), "scenario.Authorization")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"private_key": "redacted fixture marker"}), "scenario.private_key")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"decisionNote": "Bearer local-fixture-redacted"}), "scenario.decisionNote")
    assert_positive_mutation_fails(
        lambda scenario: scenario["boundaryStatus"].update({"credentialAccess": True}),
        "boundaryStatus.credentialAccess",
    )
    print("PASS beta operator decision package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
