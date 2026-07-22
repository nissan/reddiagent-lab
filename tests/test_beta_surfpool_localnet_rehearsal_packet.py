#!/usr/bin/env python3
"""Check Surfpool/localnet external beta rehearsal packet evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-surfpool-localnet-rehearsal-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_surfpool_localnet_rehearsal_packet as rehearsal  # noqa: E402


def run_packet(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_surfpool_localnet_rehearsal_packet.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_scenario_mutation_fails(index: int, mutator, expected_path: str) -> None:
    scenario = json.loads(json.dumps(rehearsal.default_scenarios()[index]))
    mutator(scenario)
    findings = rehearsal.scenario_findings(scenario)
    assert expected_path in {finding["path"] for finding in findings}


def assert_packet_mutation_fails(mutator, expected_path: str) -> None:
    archive_binding = rehearsal.artifact_binding(rehearsal.ARCHIVE_PACKET_PATH)
    roadmap_binding = rehearsal.artifact_binding(rehearsal.ROADMAP_PACKET_PATH)
    surfpool_binding = rehearsal.artifact_binding(rehearsal.SURFPOOL_LANE_PATH)
    archive_doc = rehearsal.load_json(ROOT / rehearsal.ARCHIVE_PACKET_PATH)
    roadmap_text = (ROOT / rehearsal.ROADMAP_PACKET_PATH).read_text(encoding="utf-8")
    surfpool_doc = rehearsal.load_json(ROOT / rehearsal.SURFPOOL_LANE_PATH)
    boundaries = rehearsal.rehearsal_boundaries()
    scenarios = [rehearsal.build_scenario_result(scenario) for scenario in rehearsal.default_scenarios()]
    mutator(archive_doc, archive_binding, roadmap_text, roadmap_binding, surfpool_doc, surfpool_binding, boundaries, scenarios)
    findings = rehearsal.collect_packet_findings(
        archive_doc,
        archive_binding,
        roadmap_text,
        roadmap_binding,
        surfpool_doc,
        surfpool_binding,
        boundaries,
        scenarios,
    )
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_packet()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "surfpool-localnet-external-beta-rehearsal-packet"
    assert doc["issue"] == 359
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [355, 356]
    assert doc["status"] == "pass"
    assert doc["decision"] == "localnet-rehearsal-ready"
    assert doc["rehearsalPacketId"] == "reddiagent-beta-0-surfpool-localnet-external-rehearsal"
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    archive = doc["inputs"]["releaseArchivePacket"]
    assert archive["path"] == "tests/fixtures/beta-adl-v02-release-archive-packet.json"
    assert archive["issue"] == 355
    assert archive["status"] == "pass"
    assert archive["decision"] == "archive-ready"
    assert archive["sha256"]
    assert archive["sizeBytes"]

    roadmap = doc["inputs"]["agenticPaymentsRoadmap"]
    assert roadmap["path"] == "research/2026-07-23-agentic-payments-roadmap-recalibration.md"
    assert roadmap["issue"] == 356
    assert "delegated authority" in roadmap["requiredTerms"]
    assert "no mainnet" in roadmap["requiredTerms"]

    surfpool = doc["inputs"]["surfpoolValidatorLane"]
    assert surfpool["path"] == "tests/fixtures/surfpool-validator-lane.json"
    assert surfpool["issue"] == 248
    assert surfpool["status"] == "pass"
    assert surfpool["preferred"] == "surfpool-local"
    assert surfpool["fallback"] == "solana-test-validator-fallback"

    assert doc["setupAssumptions"] == {
        "environment": "Surfpool/localnet first, solana-test-validator fallback only if Surfpool is unavailable.",
        "endpoint": "loopback only: 127.0.0.1 or localhost.",
        "ledger": "resettable local ledger under .tmp; no reusable validator state.",
        "accounts": "fixture-funded tester principal, agent spender, and merchant service accounts only.",
        "mints": "fixture localnet mint rUSD-L only; no devnet/mainnet mint IDs.",
        "commandsAreIllustrative": True,
    }
    assert doc["acceptanceEvidence"]["operatorAcceptance"] is True
    assert doc["acceptanceEvidence"]["readyForDevnetGate"] is True
    assert doc["acceptanceEvidence"]["devnetRequiresSeparateIssue"] == 360
    assert doc["acceptanceEvidence"]["mainnetBlockedUntilAudit"] is True
    assert doc["scenarioSummary"] == {
        "positiveScenarios": 2,
        "negativeScenarios": 3,
        "failClosedScenarios": 3,
        "receiptScenarios": 1,
        "replayScenarios": 1,
    }

    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["localnet-setup-pass"]["status"] == "pass"
    assert scenarios["localnet-setup-pass"]["kind"] == "setup"
    assert scenarios["delegated-authority-pass"]["status"] == "pass"
    assert scenarios["delegated-authority-pass"]["receiptRef"] == "receipt-authority-pass"
    assert scenarios["replay-denied"]["status"] == "fail"
    assert "scenarios.replay-denied.replay.previousNonceSeen" in {finding["path"] for finding in scenarios["replay-denied"]["findings"]}
    assert scenarios["over-cap-denied"]["status"] == "fail"
    assert "scenarios.over-cap-denied.attempt.amount" in {finding["path"] for finding in scenarios["over-cap-denied"]["findings"]}
    assert scenarios["receipt-mismatch-denied"]["status"] == "fail"
    assert "scenarios.receipt-mismatch-denied.receipt.bindsResponseHash" in {finding["path"] for finding in scenarios["receipt-mismatch-denied"]["findings"]}

    for key, expected in {
        "deterministicLocalnetRehearsalPacket": True,
        "consumesReleaseArchiveAndRoadmapOnly": True,
        "usesSurfpoolLaneAsStaticInput": True,
        "externalBetaRehearsalEvidenceOnly": True,
        "fullHistoricalBetaChainReplay": False,
        "liveRuntimeActivation": False,
        "hostedDeployment": False,
        "dockerMutation": False,
        "surfpoolMutation": False,
        "coolifyMutation": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "walletAccess": False,
        "facilitatorAccess": False,
        "settlementAccess": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "deploymentPublished": False,
        "packagePublished": False,
        "archivePublished": False,
        "publicPublished": False,
        "externalSpend": False,
        "productionGatewayMutation": False,
    }.items():
        assert doc["boundaries"][key] is expected

    assert run_packet("--requested-decision", "hold")["decision"] == "hold"
    assert run_packet("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert rehearsal.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_scenario_mutation_fails(0, lambda scenario: scenario["cluster"].update({"endpoint": "api.devnet.solana.com"}), "scenarios.localnet-setup-pass.cluster.endpoint")
    assert_scenario_mutation_fails(0, lambda scenario: scenario.update({"fixtureAccounts": []}), "scenarios.localnet-setup-pass.fixtureAccounts")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["boundaries"].update({"devnetUsed": True}), "scenarios.localnet-setup-pass.boundaries.devnetUsed")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["attempt"].update({"slot": 9001}), "scenarios.delegated-authority-pass.attempt.slot")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["authority"].update({"revocable": False}), "scenarios.delegated-authority-pass.authority.revocable")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["receipt"].update({"bindsMandateId": False}), "scenarios.delegated-authority-pass.receipt.bindsMandateId")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["rollback"].update({"verified": False}), "scenarios.delegated-authority-pass.rollback.verified")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["boundaries"].update({"mainnetUsed": True}), "scenarios.delegated-authority-pass.boundaries.mainnetUsed")

    assert_packet_mutation_fails(lambda archive_doc, *_: archive_doc.update({"decision": "hold"}), "releaseArchivePacket.decision")
    assert_packet_mutation_fails(lambda archive_doc, *_: archive_doc["archiveSummary"].update({"readyForOfflineInspection": False}), "releaseArchivePacket.archiveSummary.readyForOfflineInspection")
    assert_packet_mutation_fails(lambda _archive_doc, _archive_binding, _roadmap_text, roadmap_binding, *_: roadmap_binding.update({"sha256": ""}), "roadmapPacket.sha256")
    assert_packet_mutation_fails(lambda _archive_doc, _archive_binding, _roadmap_text, _roadmap_binding, surfpool_doc, *_: surfpool_doc.update({"status": "fail"}), "surfpoolValidatorLane.status")
    assert_packet_mutation_fails(lambda _archive_doc, _archive_binding, _roadmap_text, _roadmap_binding, surfpool_doc, *_: surfpool_doc["boundaries"].update({"devnetAccessUsed": True}), "surfpoolValidatorLane.boundaries.devnetAccessUsed")
    assert_packet_mutation_fails(lambda *_args: _args[6].update({"devnetAccess": True}), "boundaries.devnetAccess")
    assert_packet_mutation_fails(lambda *_args: _args[7][0].update({"status": "fail"}), "scenarios.localnet-setup-pass.status")
    assert_packet_mutation_fails(lambda *_args: _args[7][2].update({"status": "pass"}), "scenarios.replay-denied.status")

    print("PASS Surfpool/localnet external beta rehearsal packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
