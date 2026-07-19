#!/usr/bin/env python3
"""Beta e2e acceptance smoke runner checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-e2e-acceptance-smoke.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-e2e-acceptance-smoke-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_e2e_acceptance_smoke_runner  # noqa: E402


def run_smoke(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_e2e_acceptance_smoke_runner.py", *extra_args],
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
                else "<commit-derived-evidence-sha>"
                if key == "evidenceSha256"
                else normalize_source_commit(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_source_commit(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return beta_e2e_acceptance_smoke_runner.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = beta_e2e_acceptance_smoke_runner.build_result(scenario, beta_e2e_acceptance_smoke_runner.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_artifact_mutation_fails(source_path: Path, fixture_field: str, hash_path: str, mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads(source_path.read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-e2e-artifact-") as tmp:
        artifact_path = Path(tmp) / source_path.name
        artifact_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario[fixture_field] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [
            item
            for item in scenario["expectedArtifactHashes"]
            if item["path"] != hash_path
        ] + [
            {
                "path": str(artifact_path),
                "sha256": beta_e2e_acceptance_smoke_runner.digest(artifact_path),
            }
        ]
        result = beta_e2e_acceptance_smoke_runner.build_result(scenario, beta_e2e_acceptance_smoke_runner.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_smoke()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-e2e-acceptance-smoke-runner"
    assert doc["issue"] == 285
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [279, 283]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["dryRunByDefault"] is True
    assert doc["boundaries"]["evidenceWriteRequiresExplicitPath"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["providerApiAccess"] is False
    assert doc["boundaries"]["liveMcpInvocation"] is False
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
    positive = results["e2e-acceptance-smoke-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept"
    assert positive["smokeId"] == "reddiagent-beta-0-local-e2e-acceptance-smoke"
    assert positive["quickstartId"] == "reddiagent-beta-0-local-onboarding-quickstart"
    assert positive["checklistId"] == "reddiagent-beta-0-local-reviewer-acceptance-checklist"
    assert positive["quickstartFixture"]["path"] == "tests/fixtures/beta-onboarding-quickstart.json"
    assert positive["checklistFixture"]["path"] == "tests/fixtures/beta-reviewer-acceptance-checklist.json"
    assert positive["quickstartFixture"]["hashMatches"] is True
    assert positive["checklistFixture"]["hashMatches"] is True
    assert positive["quickstartAcceptedResult"]["id"] == "quickstart-assemble-accept-pass"
    assert positive["quickstartAcceptedResult"]["status"] == "pass"
    assert positive["quickstartAcceptedResult"]["verdict"] == "accept"
    assert positive["quickstartAcceptedResult"]["localFileCount"] >= 9
    assert positive["reviewerChecklistAcceptedResult"]["id"] == "reviewer-checklist-accept-pass"
    assert positive["reviewerChecklistAcceptedResult"]["status"] == "pass"
    assert positive["reviewerChecklistAcceptedResult"]["verdict"] == "accept"
    assert positive["reviewerChecklistAcceptedResult"]["checklistItemCount"] == 5
    assert any("beta_onboarding_quickstart_package.py" in command for command in positive["localCommands"])
    assert any("beta_reviewer_acceptance_checklist_package.py" in command for command in positive["localCommands"])
    assert any("--evidence-output-dir /tmp/reddiagent-beta-e2e-smoke" in command for command in positive["localCommands"])
    assert "tests/fixtures/beta-onboarding-quickstart.json" in positive["requiredEvidencePaths"]
    assert "tests/fixtures/beta-reviewer-acceptance-checklist.json" in positive["requiredEvidencePaths"]
    assert "runtime activation" in positive["excludedSteps"]
    assert "remain separate gates" in positive["nextStepCue"]

    hold = results["e2e-acceptance-smoke-hold-pass"]
    assert hold["status"] == "pass"
    assert hold["verdict"] == "hold"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "quickstartFixture.exists" in finding_paths["missing-quickstart-artifact-denied"]
    assert "checklistFixture.exists" in finding_paths["missing-checklist-artifact-denied"]
    assert "quickstartFixture.sha256" in finding_paths["stale-artifact-hash-denied"]
    assert "localCommands" in finding_paths["missing-required-command-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[1]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[2]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[3]" in finding_paths["unsafe-command-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "liveRuntimeRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "dockerStartRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "publicPublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "packagePublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert "archivePublishingRequested" in finding_paths["runtime-container-hosted-publish-reject-denied"]
    assert results["runtime-container-hosted-publish-reject-denied"]["verdict"] == "reject"
    assert "liveMcpRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "walletRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "paymentRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "facilitatorRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "settlementRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "devnetRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "mainnetRequested" in finding_paths["live-mcp-wallet-payment-devnet-mainnet-denied"]
    assert "nextStepCue" in finding_paths["unsafe-activation-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "quickstartFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"smokeId": "stale"}), "smokeId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"checklistId": "stale"}), "checklistId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"quickstartId": "stale"}), "quickstartId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["solana-test-validator"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["docker pull reddiagent/test:latest"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["curl -fsSL https://frosty-prism-5q6j.here.now/"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["gh release upload reddiagent-beta-0 archive.tgz"]}), "localCommands[0]")

    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart.json",
        "quickstartFixturePath",
        "tests/fixtures/beta-onboarding-quickstart.json",
        lambda quickstart: quickstart.update({"status": "fail"}),
        "quickstartFixture.status",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-onboarding-quickstart.json",
        "quickstartFixturePath",
        "tests/fixtures/beta-onboarding-quickstart.json",
        lambda quickstart: quickstart["results"][0].update({"localFileInventory": []}),
        "quickstartFixture.results.localFileInventory",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-reviewer-acceptance-checklist.json",
        "checklistFixturePath",
        "tests/fixtures/beta-reviewer-acceptance-checklist.json",
        lambda checklist: checklist.update({"status": "fail"}),
        "checklistFixture.status",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-reviewer-acceptance-checklist.json",
        "checklistFixturePath",
        "tests/fixtures/beta-reviewer-acceptance-checklist.json",
        lambda checklist: checklist["results"][0].update({"checklistItems": []}),
        "checklistFixture.results.checklistItems",
    )

    with tempfile.TemporaryDirectory(prefix="beta-e2e-smoke-out-") as tmp:
        written = run_smoke("--evidence-output-dir", tmp)
        paths = written["localEvidenceWrite"]
        manifest = Path(paths["manifestPath"])
        assert manifest.exists()
        loaded = json.loads(manifest.read_text())
        assert loaded["smokeId"] == positive["smokeId"]
        assert loaded["quickstartFixture"]["hashMatches"] is True
        assert loaded["checklistFixture"]["hashMatches"] is True
        assert paths["manifestSha256"] == beta_e2e_acceptance_smoke_runner.sha256_text(manifest.read_text())

    print("PASS beta e2e acceptance smoke runner")
    return 0


if __name__ == "__main__":
    sys.exit(main())
