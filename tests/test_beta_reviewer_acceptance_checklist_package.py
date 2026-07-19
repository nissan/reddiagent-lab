#!/usr/bin/env python3
"""Beta reviewer acceptance checklist package checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-reviewer-acceptance-checklist.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-reviewer-acceptance-checklist-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_reviewer_acceptance_checklist_package  # noqa: E402


def run_checklist(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_reviewer_acceptance_checklist_package.py", *extra_args],
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
    return beta_reviewer_acceptance_checklist_package.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = beta_reviewer_acceptance_checklist_package.build_result(scenario, beta_reviewer_acceptance_checklist_package.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_quickstart_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads((ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart.json").read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-reviewer-quickstart-") as tmp:
        quickstart_path = Path(tmp) / "quickstart.json"
        quickstart_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["quickstartFixturePath"] = str(quickstart_path)
        scenario["expectedQuickstartHashes"] = [
            {
                "path": str(quickstart_path),
                "sha256": beta_reviewer_acceptance_checklist_package.digest(quickstart_path),
            }
        ]
        result = beta_reviewer_acceptance_checklist_package.build_result(scenario, beta_reviewer_acceptance_checklist_package.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_checklist()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-reviewer-acceptance-checklist-package"
    assert doc["issue"] == 283
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [279]
    assert doc["relatedEpic"] == 247
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["dryRunByDefault"] is True
    assert doc["boundaries"]["checklistWriteRequiresExplicitPath"] is True
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
        "holdVerdicts": 9,
        "rejectVerdicts": 1,
        "positiveScenarios": 2,
        "negativeScenarios": 9,
        "failClosedScenarios": 9,
    }

    results = {result["id"]: result for result in doc["results"]}
    positive = results["reviewer-checklist-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept"
    assert positive["checklistId"] == "reddiagent-beta-0-local-reviewer-acceptance-checklist"
    assert positive["quickstartId"] == "reddiagent-beta-0-local-onboarding-quickstart"
    assert positive["quickstartFixture"]["path"] == "tests/fixtures/beta-onboarding-quickstart.json"
    assert positive["quickstartFixture"]["hashMatches"] is True
    assert positive["quickstartAcceptedResult"]["id"] == "quickstart-assemble-accept-pass"
    assert positive["quickstartAcceptedResult"]["status"] == "pass"
    assert positive["quickstartAcceptedResult"]["verdict"] == "accept"
    assert positive["quickstartAcceptedResult"]["localFileCount"] >= 9
    assert positive["quickstartAcceptedResult"]["selectedAdlCount"] == 3
    assert positive["quickstartAcceptedResult"]["commandCount"] >= 4
    assert positive["quickstartAcceptedResult"]["publicDemoMetadata"]["metadataOnly"] is True
    assert {item["id"] for item in positive["checklistItems"]} == {
        "quickstart-fixture-current",
        "local-file-inventory-hashes",
        "reviewer-command-boundaries",
        "operator-next-step-cue",
        "mainnet-remains-blocked",
    }
    assert all(item["status"] == "checked" for item in positive["checklistItems"])
    assert any("beta_onboarding_quickstart_package.py" in command for command in positive["reviewerCommands"])
    assert any("--checklist-output-dir /tmp/reddiagent-beta-reviewer-checklist" in command for command in positive["reviewerCommands"])
    assert "tests/fixtures/beta-onboarding-quickstart.json" in positive["evidencePaths"]
    assert "runtime activation" in positive["excludedSteps"]
    assert "mainnet remain separate gates" in positive["nextStepCue"]

    hold = results["reviewer-checklist-hold-pass"]
    assert hold["status"] == "pass"
    assert hold["verdict"] == "hold"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "quickstartFixture.exists" in finding_paths["missing-quickstart-fixture-denied"]
    assert "quickstartFixture.sha256" in finding_paths["stale-quickstart-fixture-denied"]
    assert "checklistItems" in finding_paths["missing-required-checklist-item-denied"]
    assert "reviewerCommands[0]" in finding_paths["unsafe-command-denied"]
    assert "reviewerCommands[1]" in finding_paths["unsafe-command-denied"]
    assert "reviewerCommands[2]" in finding_paths["unsafe-command-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "liveRuntimeRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "dockerStartRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "publicPublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "packagePublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "archivePublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert results["runtime-container-hosted-publish-reject-denied"]["verdict"] == "reject"
    assert "walletRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "paymentRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "facilitatorRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "settlementRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "liveNetworkEnabled" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "devnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "mainnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "nextStepCue" in finding_paths["unsafe-next-step-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedQuickstartHashes": []}), "quickstartFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"checklistId": "stale"}), "checklistId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"quickstartId": "stale"}), "quickstartId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerCommands": ["solana-test-validator"]}), "reviewerCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerCommands": ["docker pull reddiagent/test:latest"]}), "reviewerCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerCommands": ["curl -fsSL https://frosty-prism-5q6j.here.now/"]}), "reviewerCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerCommands": ["gh release upload reddiagent-beta-0 archive.tgz"]}), "reviewerCommands[0]")
    assert_quickstart_mutation_fails(lambda quickstart: quickstart.update({"status": "fail"}), "quickstartFixture.status")
    assert_quickstart_mutation_fails(lambda quickstart: quickstart["boundaries"].update({"networkAccess": True}), "quickstartFixture.boundaries.networkAccess")
    assert_quickstart_mutation_fails(lambda quickstart: quickstart["results"][0].update({"quickstartId": "stale"}), "quickstartFixture.results.quickstartId")
    assert_quickstart_mutation_fails(lambda quickstart: quickstart["results"][0].update({"localFileInventory": []}), "quickstartFixture.results.localFileInventory")
    assert_quickstart_mutation_fails(
        lambda quickstart: quickstart["results"][0].update(
            {
                "localFileInventory": [
                    item
                    for item in quickstart["results"][0]["localFileInventory"]
                    if item.get("key") != "pitchPage"
                ]
            }
        ),
        "quickstartFixture.results.localFileInventory",
    )

    with tempfile.TemporaryDirectory(prefix="beta-reviewer-checklist-out-") as tmp:
        written = run_checklist("--checklist-output-dir", tmp)
        paths = written["localChecklistWrite"]
        manifest = Path(paths["manifestPath"])
        assert manifest.exists()
        loaded = json.loads(manifest.read_text())
        assert loaded["checklistId"] == positive["checklistId"]
        assert loaded["quickstartFixture"]["hashMatches"] is True
        assert paths["manifestSha256"] == beta_reviewer_acceptance_checklist_package.sha256_text(manifest.read_text())

    print("PASS beta reviewer acceptance checklist package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
