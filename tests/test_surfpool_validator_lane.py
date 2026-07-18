#!/usr/bin/env python3
"""Surfpool local validator lane evidence checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "surfpool-validator-lane.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "surfpool-validator-lane-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import surfpool_validator_lane  # noqa: E402


def run_lane() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/surfpool_validator_lane.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_positive_mutation_fails(mutator, expected_path: str, scenario_index: int = 0) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = surfpool_validator_lane.merge_scenario(scenarios["defaults"], scenarios["scenarios"][scenario_index])
    mutator(positive)
    result = surfpool_validator_lane.build_result(positive)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_lane()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "surfpool-local-validator-testing-lane"
    assert doc["issue"] == 248
    assert doc["parentEpic"] == 247
    assert doc["relatedEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["validatorPreference"]["preferred"] == "surfpool-local"
    assert doc["validatorPreference"]["fallback"] == "solana-test-validator-fallback"
    assert "Mainnet" in doc["mainnetStatement"]
    assert doc["boundaries"] == {
        "deterministicLocalEvidenceOnly": True,
        "validatorStartedByThisScript": False,
        "dependenciesInstalled": False,
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
        "surfpoolPassScenarios": 1,
        "fallbackPassScenarios": 1,
    }

    results = {result["id"]: result for result in doc["results"]}
    surfpool = results["surfpool-local-receipt-pass"]
    fallback = results["solana-test-validator-fallback-pass"]
    assert surfpool["status"] == "pass"
    assert surfpool["evidence"]["validatorMode"] == "surfpool-local"
    assert surfpool["evidence"]["cluster"]["source"] == "localnet"
    assert surfpool["evidence"]["cluster"]["endpoint"] == "127.0.0.1"
    assert surfpool["evidence"]["receipt"]["liveSettlement"] is False
    assert surfpool["evidence"]["receipt"]["devnetUsed"] is False
    assert surfpool["evidence"]["receipt"]["mainnetUsed"] is False
    assert surfpool["evidence"]["stateDeltas"]["lamportsDelta"] == -5000
    assert surfpool["evidence"]["stateDeltas"]["tokenDelta"] == 0
    assert all("--dry-run" in step["command"] or "solana-test-validator" in step["command"] for step in surfpool["evidence"]["commands"])
    assert surfpool["evidence"]["teardown"]["ledgerCleaned"] is True
    assert surfpool["evidence"]["rollback"]["cleanupVerified"] is True

    assert fallback["status"] == "pass"
    assert fallback["evidence"]["validatorMode"] == "solana-test-validator-fallback"
    assert fallback["fallbackRationale"].startswith("Surfpool binary unavailable")
    assert fallback["evidence"]["cluster"]["endpoint"] == "localhost"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "surfpoolEvidencePresent" in finding_paths["missing-surfpool-evidence-denied"]
    assert "fallbackRationale" in finding_paths["fallback-without-rationale-denied"]
    assert "cluster.source" in finding_paths["unsafe-cluster-selection-denied"]
    assert "mainnetRequested" in finding_paths["unsafe-cluster-selection-denied"]
    assert "boundaryStatus.mainnetAccess" in finding_paths["unsafe-cluster-selection-denied"]
    assert "teardown.captured" in finding_paths["missing-teardown-denied"]
    assert "teardown.ledgerCleaned" in finding_paths["missing-teardown-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "walletRequested" in finding_paths["wallet-request-denied"]
    assert "boundaryStatus.walletAccess" in finding_paths["wallet-request-denied"]
    assert "paymentRequested" in finding_paths["payment-facilitator-request-denied"]
    assert "paymentRailRequested" in finding_paths["payment-facilitator-request-denied"]
    assert "paymentAccessRequested" in finding_paths["payment-facilitator-request-denied"]
    assert "facilitatorRequested" in finding_paths["payment-facilitator-request-denied"]
    assert "settlementRequested" in finding_paths["payment-facilitator-request-denied"]
    assert "settlementClaimed" in finding_paths["payment-facilitator-request-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "stateDeltas.lamports" in finding_paths["missing-state-deltas-denied"]
    assert "stateDeltas.tokens" in finding_paths["missing-state-deltas-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"surfpoolEvidencePresent": False}), "surfpoolEvidencePresent")
    assert_positive_mutation_fails(lambda scenario: scenario["cluster"].update({"source": "devnet"}), "cluster.source")
    assert_positive_mutation_fails(lambda scenario: scenario["cluster"].update({"endpoint": "api.devnet.solana.com"}), "cluster.endpoint")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"accounts": []}), "accounts")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"programs": []}), "programs")
    assert_positive_mutation_fails(lambda scenario: scenario["teardown"].update({"captured": False}), "teardown.captured")
    assert_positive_mutation_fails(lambda scenario: scenario["rollback"].update({"cleanupVerified": False}), "rollback.cleanupVerified")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"walletRequested": True}), "walletRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRailRequested": True}), "paymentRailRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentAccessRequested": True}), "paymentAccessRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"facilitatorRequested": True}), "facilitatorRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"settlementRequested": True}), "settlementRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"settlementClaimed": True}), "settlementClaimed")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": True}), "devnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"private_key": "redacted fixture marker"}), "scenario.private_key")
    assert_positive_mutation_fails(lambda scenario: scenario["boundaryStatus"].update({"credentialAccess": True}), "boundaryStatus.credentialAccess")
    print("PASS Surfpool validator lane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
