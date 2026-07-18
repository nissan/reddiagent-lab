#!/usr/bin/env python3
"""Beta release verification CLI checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-release-verification.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-verification-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_release_verification_cli  # noqa: E402


def run_verifier() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_release_verification_cli.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def source_context() -> tuple[dict, str]:
    return json.loads(SCENARIOS.read_text()), subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def normalize_source_commit(value):
    if isinstance(value, dict):
        return {key: ("<current-git-head>" if key == "sourceCommit" else normalize_source_commit(child)) for key, child in value.items()}
    if isinstance(value, list):
        return [normalize_source_commit(child) for child in value]
    return value


def positive_scenario(profile: str = "local-only") -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    scenario = {"id": f"mutation-{profile}", "profile": profile}
    return beta_release_verification_cli.merge_scenario(scenarios["defaults"], scenario)


def assert_positive_mutation_fails(mutator, expected_path: str, profile: str = "local-only") -> None:
    scenario = positive_scenario(profile)
    mutator(scenario)
    result = beta_release_verification_cli.build_result(scenario, beta_release_verification_cli.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_verifier()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-release-verification-cli"
    assert doc["issue"] == 269
    assert doc["parentEpic"] == 220
    assert doc["relatedEpic"] == 247
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["summary"] == {
        "acceptVerdicts": 5,
        "holdVerdicts": 5,
        "rejectVerdicts": 1,
        "positiveScenarios": 5,
        "negativeScenarios": 6,
        "failClosedScenarios": 6,
    }

    results = {result["id"]: result for result in doc["results"]}
    assert results["local-only-verification-accept-pass"]["status"] == "pass"
    assert results["local-only-verification-accept-pass"]["verdict"] == "accept"
    assert results["full-profile-verification-accept-pass"]["profile"] == "full"
    assert "tests/fixtures/surfpool-validator-lane.json" in results["full-profile-verification-accept-pass"]["requiredArtifactPaths"]
    assert "tests/fixtures/docker-testing-lane.json" in results["full-profile-verification-accept-pass"]["requiredArtifactPaths"]
    assert "tests/fixtures/coolify-staging-lane.json" in results["full-profile-verification-accept-pass"]["requiredArtifactPaths"]
    assert all(item["exists"] and item["hashMatches"] and item["sha256"] for item in results["full-profile-verification-accept-pass"]["evidenceHashes"])
    assert "planning only" in results["local-only-verification-accept-pass"]["operatorNextStep"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "artifacts.handoff.exists" in finding_paths["missing-handoff-denied"]
    assert "artifacts.handoff.sha256" in finding_paths["stale-handoff-hash-denied"]
    assert "artifacts.surfpool.expectedSha256" in finding_paths["missing-rollback-teardown-evidence-denied"]
    assert "artifacts.docker.expectedSha256" in finding_paths["missing-rollback-teardown-evidence-denied"]
    assert "artifacts.coolify.expectedSha256" in finding_paths["missing-rollback-teardown-evidence-denied"]
    assert "operatorFacingNextStep" in finding_paths["unsafe-activation-deployment-claim-denied"]
    assert "liveNetworkEnabled" in finding_paths["unsafe-network-payment-credential-mainnet-flags-denied"]
    assert "paymentRequested" in finding_paths["unsafe-network-payment-credential-mainnet-flags-denied"]
    assert "mainnetRequested" in finding_paths["unsafe-network-payment-credential-mainnet-flags-denied"]
    assert "scenario.apiKey" in finding_paths["unsafe-network-payment-credential-mainnet-flags-denied"]
    assert "deploymentClaimed" in finding_paths["unsafe-reject-verdict-denied"]
    assert results["unsafe-reject-verdict-denied"]["verdict"] == "reject"

    assert_positive_mutation_fails(
        lambda scenario: scenario.update({"expectedArtifactHashes": [{"path": "tests/fixtures/beta-release-handoff.json", "sha256": "0" * 64}]}),
        "artifacts.handoff.sha256",
    )
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "redacted fixture marker"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorFacingNextStep": "Deployment completed."}), "operatorFacingNextStep")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "artifacts.handoff.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "artifacts.surfpool.expectedSha256", "full")

    print("PASS beta release verification CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
