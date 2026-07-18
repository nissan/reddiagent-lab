#!/usr/bin/env python3
"""Beta release-candidate bundle checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-release-candidate-bundle.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-candidate-bundle-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_release_candidate_bundle  # noqa: E402


def run_bundle() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_release_candidate_bundle.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def normalize_source_commit(value):
    if isinstance(value, dict):
        return {
            key: ("<current-git-head>" if key == "sourceCommit" else normalize_source_commit(child))
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_source_commit(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return beta_release_candidate_bundle.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = beta_release_candidate_bundle.build_result(scenario, beta_release_candidate_bundle.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_verifier_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads((ROOT / "tests" / "fixtures" / "beta-release-verification.json").read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-rc-verifier-") as tmp:
        verifier_path = Path(tmp) / "verifier.json"
        verifier_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["artifactPathOverrides"] = {"verifier": str(verifier_path)}
        scenario["expectedEvidenceHashes"] = copy.deepcopy(scenario["expectedEvidenceHashes"])
        scenario["expectedEvidenceHashes"].append(
            {
                "path": str(verifier_path),
                "sha256": beta_release_candidate_bundle.digest(verifier_path),
            }
        )
        result = beta_release_candidate_bundle.build_result(scenario, beta_release_candidate_bundle.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_demo_mutation_fails(artifact_key: str, source_path: str, suffix: str, expected_path: str) -> None:
    scenario = positive_scenario()
    source = (ROOT / source_path).read_text()
    with tempfile.TemporaryDirectory(prefix="beta-rc-demo-") as tmp:
        demo_path = Path(tmp) / Path(source_path).name
        demo_path.write_text(source + suffix)
        scenario["artifactPathOverrides"] = {artifact_key: str(demo_path)}
        scenario["expectedEvidenceHashes"] = copy.deepcopy(scenario["expectedEvidenceHashes"])
        scenario["expectedEvidenceHashes"].append(
            {
                "path": str(demo_path),
                "sha256": beta_release_candidate_bundle.digest(demo_path),
            }
        )
        result = beta_release_candidate_bundle.build_result(scenario, beta_release_candidate_bundle.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_bundle()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-release-candidate-bundle"
    assert doc["issue"] == 273
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [269, 271]
    assert doc["relatedEpic"] == 247
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["walletAccess"] is False
    assert doc["boundaries"]["paymentAccess"] is False
    assert doc["boundaries"]["facilitatorAccess"] is False
    assert doc["boundaries"]["settlementAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert doc["boundaries"]["packagePublished"] is False
    assert doc["boundaries"]["externalSpend"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["summary"] == {
        "acceptVerdicts": 1,
        "holdVerdicts": 9,
        "rejectVerdicts": 1,
        "positiveScenarios": 1,
        "negativeScenarios": 10,
        "failClosedScenarios": 10,
    }

    results = {result["id"]: result for result in doc["results"]}
    positive = results["release-candidate-bundle-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept"
    assert positive["releaseCandidateId"] == "reddiagent-beta-0-rc-local-1"
    assert positive["publicDemoMetadata"]["publicDemoUrl"] == "https://present-hearth-vhey.here.now/"
    assert positive["publicDemoMetadata"]["publicVideoUrl"].endswith("/media/reddiagent-demo-walkthrough.mp4")
    assert "tests/fixtures/beta-release-verification.json" in positive["includedFiles"]
    assert "docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md" in positive["includedFiles"]
    assert "scripts/public_demo_walkthrough_video.sh" in positive["includedFiles"]
    assert "tests/fixtures/surfpool-validator-lane.json" in positive["includedFiles"]
    assert "devnet/mainnet transaction or settlement artifacts" in positive["excludedFiles"]
    assert all(item["exists"] and item["hashMatches"] and item["sha256"] for item in positive["artifactInventory"])
    assert positive["verifierEvidenceHashes"]
    assert "planning and review only" in positive["operatorNextStep"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "artifacts.verifier.exists" in finding_paths["missing-verifier-evidence-denied"]
    assert "artifacts.verifier.sha256" in finding_paths["stale-verifier-hash-denied"]
    assert "artifacts.demoPlan.exists" in finding_paths["missing-demo-plan-denied"]
    assert "publicDemoMetadata.videoEvidence.mp4Embedded" in finding_paths["missing-video-evidence-denied"]
    assert "operatorNextStep" in finding_paths["unsafe-activation-deployment-publishing-claim-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "unsafeEnvValues.OPENAI_API_KEY" in finding_paths["unsafe-env-values-denied"]
    assert "walletRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "paymentRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "facilitatorRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "settlementRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "liveNetworkEnabled" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "devnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "mainnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "deploymentClaimed" in finding_paths["unsafe-reject-verdict-denied"]
    assert results["unsafe-reject-verdict-denied"]["verdict"] == "reject"

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedEvidenceHashes": []}), "artifacts.verifier.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorNextStep": "Package published."}), "operatorNextStep")
    assert_positive_mutation_fails(lambda scenario: scenario.setdefault("unsafeEnvValues", {}).update({"API_TOKEN": "secret-value"}), "unsafeEnvValues.API_TOKEN")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseCandidateId": ""}), "releaseCandidateId")
    assert_verifier_mutation_fails(lambda verifier: verifier.update({"status": "fail"}), "verifier.status")
    assert_verifier_mutation_fails(lambda verifier: verifier["boundaries"].update({"networkAccess": True}), "verifier.boundaries.networkAccess")
    assert_demo_mutation_fails("demoPlan", "docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md", "\nDeployment completed.\n", "demoPlan")
    assert_demo_mutation_fails("demoBuilder", "scripts/public_demo_walkthrough_video.sh", "\ntoken=abc123\n", "demoBuilder")

    print("PASS beta release candidate bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
