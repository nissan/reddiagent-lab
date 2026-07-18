#!/usr/bin/env python3
"""Beta onboarding quickstart package checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_onboarding_quickstart_package  # noqa: E402


def run_quickstart(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_onboarding_quickstart_package.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def normalize_source_commit(value):
    if isinstance(value, dict):
        return {
            key: (
                "<current-git-head>"
                if key == "sourceCommit"
                else "<commit-derived-manifest-sha>"
                if key == "manifestSha256"
                else normalize_source_commit(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_source_commit(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return beta_onboarding_quickstart_package.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = beta_onboarding_quickstart_package.build_result(scenario, beta_onboarding_quickstart_package.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_archive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads((ROOT / "tests" / "fixtures" / "beta-release-archive-assembler.json").read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-quickstart-archive-") as tmp:
        archive_path = Path(tmp) / "archive.json"
        archive_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["archiveManifestPath"] = str(archive_path)
        scenario["localFilePathOverrides"] = {"archiveManifest": str(archive_path)}
        scenario["expectedLocalFileHashes"] = copy.deepcopy(scenario["expectedLocalFileHashes"])
        scenario["expectedLocalFileHashes"].append(
            {
                "path": str(archive_path),
                "sha256": beta_onboarding_quickstart_package.digest(archive_path),
            }
        )
        result = beta_onboarding_quickstart_package.build_result(scenario, beta_onboarding_quickstart_package.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_quickstart()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-onboarding-quickstart-package"
    assert doc["issue"] == 279
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [275, 277]
    assert doc["relatedEpic"] == 247
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["dryRunByDefault"] is True
    assert doc["boundaries"]["quickstartWriteRequiresExplicitPath"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["providerApiAccess"] is False
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["dockerStarted"] is False
    assert doc["boundaries"]["surfpoolStarted"] is False
    assert doc["boundaries"]["coolifyDeployment"] is False
    assert doc["boundaries"]["walletAccess"] is False
    assert doc["boundaries"]["paymentAccess"] is False
    assert doc["boundaries"]["facilitatorAccess"] is False
    assert doc["boundaries"]["settlementAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert doc["boundaries"]["packagePublished"] is False
    assert doc["boundaries"]["archivePublished"] is False
    assert doc["boundaries"]["publicPublished"] is False
    assert doc["boundaries"]["externalSpend"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["summary"] == {
        "acceptVerdicts": 1,
        "holdVerdicts": 12,
        "rejectVerdicts": 1,
        "positiveScenarios": 1,
        "negativeScenarios": 13,
        "failClosedScenarios": 13,
    }

    results = {result["id"]: result for result in doc["results"]}
    positive = results["quickstart-assemble-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept"
    assert positive["quickstartId"] == "reddiagent-beta-0-local-onboarding-quickstart"
    assert positive["releaseId"] == "reddiagent-beta-0"
    assert positive["releaseCandidateId"] == "reddiagent-beta-0-rc-local-1"
    assert positive["releaseArchive"]["path"] == "tests/fixtures/beta-release-archive-assembler.json"
    assert positive["releaseArchive"]["hashMatches"] is True
    assert positive["releaseArchive"]["archiveId"] == "reddiagent-beta-0-rc-local-1-local-review-archive"
    assert positive["publicDemoMetadata"]["publicDemoUrl"] == "https://frosty-prism-5q6j.here.now/"
    assert positive["publicDemoMetadata"]["publicVideoUrl"].endswith("/media/reddiagent-demo-story-cut.mp4")
    assert positive["publicDemoMetadata"]["metadataOnly"] is True
    assert positive["publicDemoMetadata"]["fetchedDuringQuickstart"] is False
    assert positive["publicDemoMetadata"]["publishedDuringQuickstart"] is False
    assert positive["localEntrypoint"]["defaultWrite"] is False
    assert positive["localEntrypoint"]["writeRequiresExplicitOutputDir"] is True
    assert positive["localEntrypoint"]["htmlName"].endswith(".html")
    assert all(item["exists"] and item["hashMatches"] and item["sha256"] for item in positive["localFileInventory"])
    assert all(item["exists"] and item["hashMatches"] and item["sha256"] for item in positive["selectedAdls"])
    assert {item["path"] for item in positive["selectedAdls"]} == {
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
    }
    assert any("validate_examples.py" in command for command in positive["commands"])
    assert any("--quickstart-output-dir /tmp/reddiagent-beta-quickstart" in command for command in positive["commands"])
    assert "Docker image pull or container start" in positive["excludedSteps"]
    assert "Open the generated local quickstart file" in positive["operatorNextStep"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "archiveManifest.exists" in finding_paths["missing-archive-manifest-denied"]
    assert "archiveManifest.sha256" in finding_paths["stale-archive-manifest-denied"]
    assert "localFiles.pitchPage.exists" in finding_paths["missing-pitch-page-denied"]
    assert "localFiles.pitchVideoScript.sha256" in finding_paths["stale-pitch-video-script-denied"]
    assert "selectedAdls" in finding_paths["missing-selected-adl-denied"]
    assert "selectedAdls.examples/payment-agent.yaml.sha256" in finding_paths["stale-selected-adl-hash-denied"]
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
    assert "commands[0]" in finding_paths["unsafe-command-denied"]
    assert "commands[1]" in finding_paths["unsafe-command-denied"]
    assert "commands[2]" in finding_paths["unsafe-command-denied"]
    assert "publicPublishingRequested" in finding_paths["unsafe-public-demo-mutation-reject-denied"]
    assert "publicDemoMetadata.metadataOnly" in finding_paths["unsafe-public-demo-mutation-reject-denied"]
    assert results["unsafe-public-demo-mutation-reject-denied"]["verdict"] == "reject"

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedLocalFileHashes": []}), "archiveManifest.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedAdlHashes": []}), "selectedAdls.examples/payment-agent.yaml.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorNextStep": "Archive published."}), "operatorNextStep")
    assert_positive_mutation_fails(lambda scenario: scenario.setdefault("unsafeEnvValues", {}).update({"API_TOKEN": "secret-value"}), "unsafeEnvValues.API_TOKEN")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"quickstartId": "stale"}), "quickstartId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseCandidateId": ""}), "releaseCandidateId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"commands": ["solana-test-validator"]}), "commands[0]")
    assert_positive_mutation_fails(
        lambda scenario: scenario.update({"publicDemoMetadata": {"publicDemoUrl": "https://example.com/", "publicVideoUrl": "https://example.com/video.mp4", "metadataOnly": True, "fetchedDuringQuickstart": False, "publishedDuringQuickstart": False}}),
        "publicDemoMetadata.publicDemoUrl",
    )
    assert_archive_mutation_fails(lambda archive: archive.update({"status": "fail"}), "archiveManifest.status")
    assert_archive_mutation_fails(lambda archive: archive["boundaries"].update({"networkAccess": True}), "archiveManifest.boundaries.networkAccess")
    assert_archive_mutation_fails(lambda archive: archive["results"][0].update({"releaseCandidateId": "stale"}), "archiveManifest.results.releaseCandidateId")

    with tempfile.TemporaryDirectory(prefix="beta-quickstart-out-") as tmp:
        written = run_quickstart("--quickstart-output-dir", tmp)
        paths = written["localQuickstartWrite"]
        manifest = Path(paths["manifestPath"])
        html = Path(paths["htmlPath"])
        assert manifest.exists()
        assert html.exists()
        assert json.loads(manifest.read_text())["quickstartId"] == positive["quickstartId"]
        assert "ReddiAgent Local Beta Quickstart" in html.read_text()
        assert paths["manifestSha256"] == beta_onboarding_quickstart_package.sha256_text(manifest.read_text())
        assert paths["htmlSha256"] == beta_onboarding_quickstart_package.digest(html)

    print("PASS beta onboarding quickstart package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
