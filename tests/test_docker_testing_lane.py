#!/usr/bin/env python3
"""Docker local/VPS lane evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "docker-testing-lane.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "docker-testing-lane-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import docker_testing_lane  # noqa: E402


def run_lane() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/docker_testing_lane.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_positive_mutation_fails(mutator, expected_path: str, scenario_index: int = 0) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = docker_testing_lane.merge_scenario(scenarios["defaults"], scenarios["scenarios"][scenario_index])
    mutator(positive)
    result = docker_testing_lane.build_result(positive)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_lane()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "docker-local-vps-testing-lane"
    assert doc["issue"] == 249
    assert doc["parentEpic"] == 247
    assert doc["relatedEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["selectionPolicy"]["preferred"] == "local-docker"
    assert "Mainnet" in doc["mainnetStatement"]
    assert doc["boundaries"] == {
        "deterministicLocalEvidenceOnly": True,
        "dockerPulledByThisScript": False,
        "containerStartedByThisScript": False,
        "vpsMutatedByThisScript": False,
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
        "negativeScenarios": 9,
        "failClosedScenarios": 9,
        "localDockerPassScenarios": 1,
        "vpsDockerPassScenarios": 1,
    }

    results = {result["id"]: result for result in doc["results"]}
    local = results["local-docker-static-pass"]
    vps = results["vps-docker-selection-pass"]
    assert local["status"] == "pass"
    assert local["environment"] == "local-docker"
    assert local["evidence"]["images"][0]["reference"].endswith(local["evidence"]["images"][0]["digest"])
    assert local["evidence"]["envContract"][1]["secretHandling"] == "provided-out-of-band"
    assert all("value" not in item for item in local["evidence"]["envContract"])
    assert local["evidence"]["network"]["exposure"] == "loopback-only"
    assert local["evidence"]["network"]["hostNetwork"] is False
    assert local["evidence"]["network"]["publishedPorts"] == []
    assert local["evidence"]["logs"]["redacted"] is True
    assert local["evidence"]["volumes"]["cleanupVerified"] is True
    assert local["evidence"]["teardown"]["containersRemoved"] is True
    assert local["evidence"]["rollback"]["cleanupVerified"] is True
    assert all("--no-pull" in step["command"] or "config --no-interpolate" in step["command"] or "--dry-run" in step["command"] for step in local["evidence"]["commands"])
    assert vps["status"] == "pass"
    assert vps["environment"] == "vps-docker"
    assert "long-running" in vps["selectionCriteria"]["selectedBecause"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "images[0].digest" in finding_paths["unpinned-image-denied"]
    assert "images[0].pullAllowed" in finding_paths["dependency-pull-denied"]
    assert "boundaryStatus.dependencyPulls" in finding_paths["dependency-pull-denied"]
    assert "network.exposure" in finding_paths["host-network-denied"]
    assert "network.hostNetwork" in finding_paths["host-network-denied"]
    assert "network.publishedPorts" in finding_paths["host-network-denied"]
    assert "envContract[0].value" in finding_paths["secret-env-value-denied"]
    assert "scenario.envContract[0].value" in finding_paths["secret-env-value-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "volumes.cleanupVerified" in finding_paths["missing-cleanup-denied"]
    assert "teardown.captured" in finding_paths["missing-cleanup-denied"]
    assert "teardown.containersRemoved" in finding_paths["missing-cleanup-denied"]
    assert "rollback.cleanupVerified" in finding_paths["missing-cleanup-denied"]
    assert "devnetRequested" in finding_paths["live-network-denied"]
    assert "mainnetRequested" in finding_paths["live-network-denied"]
    assert "liveNetworkEnabled" in finding_paths["live-network-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["live-network-denied"]
    assert "boundaryStatus.mainnetAccess" in finding_paths["live-network-denied"]
    assert "productionClaimed" in finding_paths["production-deployment-claim-denied"]
    assert "deploymentClaimed" in finding_paths["production-deployment-claim-denied"]
    assert "boundaryStatus.vpsMutation" in finding_paths["production-deployment-claim-denied"]
    assert "boundaryStatus.deploymentPublished" in finding_paths["production-deployment-claim-denied"]
    assert "walletRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentRailRequested" in finding_paths["payment-settlement-request-denied"]
    assert "paymentAccessRequested" in finding_paths["payment-settlement-request-denied"]
    assert "facilitatorRequested" in finding_paths["payment-settlement-request-denied"]
    assert "settlementRequested" in finding_paths["payment-settlement-request-denied"]
    assert "settlementClaimed" in finding_paths["payment-settlement-request-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"environment": "kubernetes"}), "environment")
    assert_positive_mutation_fails(lambda scenario: scenario["selectionCriteria"].update({"useLocalWhen": ""}), "selectionCriteria.useLocalWhen")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"images": []}), "images")
    assert_positive_mutation_fails(lambda scenario: scenario["images"][0].update({"reference": "python:latest"}), "images[0].digest")
    assert_positive_mutation_fails(lambda scenario: scenario["images"][0].update({"reference": "python:3.14.3-slim@sha256:", "digest": "sha256:"}), "images[0].digest")
    assert_positive_mutation_fails(lambda scenario: scenario["images"][0].update({"digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}), "images[0].digest")
    assert_positive_mutation_fails(lambda scenario: scenario["images"][0].update({"pullAllowed": True}), "images[0].pullAllowed")
    assert_positive_mutation_fails(lambda scenario: scenario["network"].update({"hostNetwork": True}), "network.hostNetwork")
    assert_positive_mutation_fails(lambda scenario: scenario["envContract"][0].update({"value": "local-only"}), "envContract[0].value")
    assert_positive_mutation_fails(lambda scenario: scenario["logs"].update({"redacted": False}), "logs.redacted")
    assert_positive_mutation_fails(lambda scenario: scenario["volumes"].update({"cleanupVerified": False}), "volumes.cleanupVerified")
    assert_positive_mutation_fails(lambda scenario: scenario["teardown"].update({"captured": False}), "teardown.captured")
    assert_positive_mutation_fails(lambda scenario: scenario["rollback"].update({"cleanupVerified": False}), "rollback.cleanupVerified")
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
    assert_positive_mutation_fails(lambda scenario: scenario["boundaryStatus"].update({"containerStarted": True}), "boundaryStatus.containerStarted")
    print("PASS Docker testing lane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
