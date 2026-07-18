#!/usr/bin/env python3
"""Coolify hosted staging/operator UI lane evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "coolify-staging-lane.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "coolify-staging-lane-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import coolify_staging_lane  # noqa: E402


def run_lane() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/coolify_staging_lane.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_positive_mutation_fails(mutator, expected_path: str, scenario_index: int = 0) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = coolify_staging_lane.merge_scenario(scenarios["defaults"], scenarios["scenarios"][scenario_index])
    mutator(positive)
    result = coolify_staging_lane.build_result(positive)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_lane()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "coolify-staging-operator-ui-lane"
    assert doc["issue"] == 250
    assert doc["parentEpic"] == 247
    assert doc["relatedEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["selectionPolicy"]["preferred"] == "local-only"
    assert "Mainnet" in doc["mainnetStatement"]
    assert doc["boundaries"] == {
        "deterministicLocalEvidenceOnly": True,
        "coolifyMutatedByThisScript": False,
        "hostedServiceUsedByThisScript": False,
        "networkAccessUsed": False,
        "credentialAccessUsed": False,
        "walletAccessUsed": False,
        "paymentRailAccessUsed": False,
        "facilitatorAccessUsed": False,
        "settlementAccessUsed": False,
        "liveMcpInvocationUsed": False,
        "providerApiAccessUsed": False,
        "devnetAccessUsed": False,
        "mainnetAccessUsed": False,
        "deploymentPublished": False,
        "packagePublished": False,
        "externalSpendUsd": 0,
    }
    assert doc["summary"] == {
        "positiveScenarios": 2,
        "negativeScenarios": 10,
        "failClosedScenarios": 10,
        "localOnlyPassScenarios": 1,
        "coolifyStagingRequiredPassScenarios": 1,
    }

    results = {result["id"]: result for result in doc["results"]}
    local = results["local-static-ui-pass"]
    hosted = results["coolify-staging-required-pass"]
    assert local["status"] == "pass"
    assert local["laneMode"] == "local-only"
    assert local["evidence"]["image"] == {}
    assert hosted["status"] == "pass"
    assert hosted["laneMode"] == "coolify-staging-required"
    assert hosted["serviceBoundary"]["type"] == "coolify-app"
    assert hosted["evidence"]["source"]["commit"] == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert hosted["evidence"]["image"]["reference"].endswith(hosted["evidence"]["image"]["digest"])
    assert all("value" not in item for item in hosted["evidence"]["envContract"])
    assert hosted["evidence"]["envContract"][1]["secretHandling"] == "provided-out-of-band"
    assert hosted["evidence"]["network"]["publicExposure"] is False
    assert hosted["evidence"]["network"]["ingress"] == "operator-ip-allowlist"
    assert hosted["evidence"]["accessControls"]["authenticationRequired"] is True
    assert hosted["evidence"]["accessControls"]["operatorAllowlistRequired"] is True
    assert hosted["evidence"]["logs"]["redacted"] is True
    assert hosted["evidence"]["storage"]["cleanupVerified"] is True
    assert hosted["evidence"]["teardown"]["coolifyResourcesRemoved"] is True
    assert hosted["evidence"]["rollback"]["cleanupVerified"] is True
    assert hosted["evidence"]["operatorUiEvidence"]["screenshotRequired"] is True
    assert all("--no-mutate" in step["command"] or "--no-deploy" in step["command"] or "--dry-run" in step["command"] for step in hosted["evidence"]["commands"])

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "source.commit" in finding_paths["unpinned-source-denied"]
    assert "image.digest" in finding_paths["unpinned-image-denied"]
    assert "network.publicExposure" in finding_paths["public-exposure-denied"]
    assert "network.ingress" in finding_paths["public-exposure-denied"]
    assert "boundaryStatus.publicExposure" in finding_paths["public-exposure-denied"]
    assert "envContract[0].value" in finding_paths["secret-env-value-denied"]
    assert "scenario.envContract[0].value" in finding_paths["secret-env-value-denied"]
    assert "storage.persistentVolume" in finding_paths["missing-teardown-rollback-denied"]
    assert "storage.cleanupVerified" in finding_paths["missing-teardown-rollback-denied"]
    assert "teardown.captured" in finding_paths["missing-teardown-rollback-denied"]
    assert "teardown.coolifyResourcesRemoved" in finding_paths["missing-teardown-rollback-denied"]
    assert "rollback.available" in finding_paths["missing-teardown-rollback-denied"]
    assert "rollback.cleanupVerified" in finding_paths["missing-teardown-rollback-denied"]
    assert "devnetRequested" in finding_paths["live-network-denied"]
    assert "mainnetRequested" in finding_paths["live-network-denied"]
    assert "liveNetworkEnabled" in finding_paths["live-network-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["live-network-denied"]
    assert "boundaryStatus.mainnetAccess" in finding_paths["live-network-denied"]
    assert "productionClaimed" in finding_paths["production-deployment-claim-denied"]
    assert "deploymentClaimed" in finding_paths["production-deployment-claim-denied"]
    assert "boundaryStatus.coolifyMutated" in finding_paths["production-deployment-claim-denied"]
    assert "boundaryStatus.hostedServiceUsed" in finding_paths["production-deployment-claim-denied"]
    assert "boundaryStatus.deploymentPublished" in finding_paths["production-deployment-claim-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "operatorUiEvidence.requiredWhenHosted" in finding_paths["operator-ui-evidence-missing-denied"]
    assert "operatorUiEvidence.screenshotRequired" in finding_paths["operator-ui-evidence-missing-denied"]
    assert "operatorUiEvidence.accessLogRequired" in finding_paths["operator-ui-evidence-missing-denied"]
    assert "operatorUiEvidence.liveSettlementClaimed" in finding_paths["operator-ui-evidence-missing-denied"]
    assert "walletRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentRailRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentAccessRequested" in finding_paths["payment-settlement-request-denied"]
    assert "facilitatorRequested" in finding_paths["payment-settlement-request-denied"]
    assert "settlementRequested" in finding_paths["payment-settlement-request-denied"]
    assert "settlementClaimed" in finding_paths["payment-settlement-request-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"laneMode": "production"}), "laneMode")
    assert_positive_mutation_fails(lambda scenario: scenario["selectionCriteria"].update({"useCoolifyWhen": ""}), "selectionCriteria.useCoolifyWhen")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceBoundary"].update({"type": "production"}), "serviceBoundary.type")
    assert_positive_mutation_fails(lambda scenario: scenario["source"].update({"commit": "main"}), "source.commit")
    assert_positive_mutation_fails(lambda scenario: scenario["network"].update({"publicExposure": True}), "network.publicExposure")
    assert_positive_mutation_fails(lambda scenario: scenario["accessControls"].update({"authenticationRequired": False}), "accessControls.authenticationRequired")
    assert_positive_mutation_fails(lambda scenario: scenario["envContract"][0].update({"value": "local-only"}), "envContract[0].value")
    assert_positive_mutation_fails(lambda scenario: scenario["logs"].update({"redacted": False}), "logs.redacted")
    assert_positive_mutation_fails(lambda scenario: scenario["storage"].update({"persistentVolume": True}), "storage.persistentVolume")
    assert_positive_mutation_fails(lambda scenario: scenario["teardown"].update({"captured": False}), "teardown.captured")
    assert_positive_mutation_fails(lambda scenario: scenario["rollback"].update({"cleanupVerified": False}), "rollback.cleanupVerified")
    assert_positive_mutation_fails(lambda scenario: scenario["operatorUiEvidence"].update({"screenshotRequired": False}), "operatorUiEvidence.screenshotRequired")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": True}), "devnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"productionClaimed": True}), "productionClaimed")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"deploymentClaimed": True}), "deploymentClaimed")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"private_key": "redacted fixture marker"}), "scenario.private_key")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"walletRequested": True}), "walletRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRailRequested": True}), "paymentRailRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentAccessRequested": True}), "paymentAccessRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"facilitatorRequested": True}), "facilitatorRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"settlementRequested": True}), "settlementRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"settlementClaimed": True}), "settlementClaimed")
    assert_positive_mutation_fails(lambda scenario: scenario["boundaryStatus"].update({"coolifyMutated": True}), "boundaryStatus.coolifyMutated")
    print("PASS Coolify staging lane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
