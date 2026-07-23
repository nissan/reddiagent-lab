#!/usr/bin/env python3
"""Check Solana devnet external tester gate design evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-solana-devnet-external-tester-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_solana_devnet_external_tester_gate as gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_solana_devnet_external_tester_gate.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_scenario_mutation_fails(index: int, mutator, expected_path: str) -> None:
    scenario = json.loads(json.dumps(gate.default_scenarios()[index]))
    mutator(scenario)
    findings = gate.scenario_findings(scenario)
    assert expected_path in {finding["path"] for finding in findings}


def assert_packet_mutation_fails(mutator, expected_path: str) -> None:
    rehearsal_binding = gate.artifact_binding(gate.LOCALNET_REHEARSAL_PATH)
    roadmap_binding = gate.artifact_binding(gate.ROADMAP_PACKET_PATH)
    rehearsal_doc = gate.load_json(ROOT / gate.LOCALNET_REHEARSAL_PATH)
    roadmap_text = (ROOT / gate.ROADMAP_PACKET_PATH).read_text(encoding="utf-8")
    boundaries = gate.gate_boundaries()
    scenarios = [gate.build_scenario_result(scenario) for scenario in gate.default_scenarios()]
    mutator(rehearsal_doc, rehearsal_binding, roadmap_text, roadmap_binding, boundaries, scenarios)
    findings = gate.collect_packet_findings(rehearsal_doc, rehearsal_binding, roadmap_text, roadmap_binding, boundaries, scenarios)
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_gate()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "solana-devnet-external-tester-gate-design"
    assert doc["issue"] == 360
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [359, 356]
    assert doc["status"] == "pass"
    assert doc["decision"] == "devnet-tester-gate-ready"
    assert doc["gateId"] == "reddiagent-beta-0-solana-devnet-external-tester-gate"
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    rehearsal = doc["inputs"]["localnetRehearsalPacket"]
    assert rehearsal["path"] == "tests/fixtures/beta-surfpool-localnet-rehearsal-packet.json"
    assert rehearsal["issue"] == 359
    assert rehearsal["status"] == "pass"
    assert rehearsal["decision"] == "localnet-rehearsal-ready"
    assert rehearsal["sha256"]
    assert rehearsal["sizeBytes"]

    roadmap = doc["inputs"]["agenticPaymentsRoadmap"]
    assert roadmap["path"] == "research/2026-07-23-agentic-payments-roadmap-recalibration.md"
    assert roadmap["issue"] == 356
    assert "devnet-only labels" in roadmap["requiredTerms"]
    assert "payment-settled/service-failed" in roadmap["requiredTerms"]
    assert "no mainnet" in roadmap["requiredTerms"]

    cohort = doc["testerGate"]["cohort"]
    assert cohort["name"] == "devnet-external-feedback-cohort-0"
    assert cohort["size"] == {"maximum": 5, "minimum": 3}
    assert cohort["roles"] == ["builder", "protocol-reviewer", "operator"]
    assert "successful cohort-0 closeout" in cohort["expansionRequires"]
    assert len(doc["testerGate"]["onboardingChecklist"]) >= 6
    assert "transaction signature or expected fail-closed code" in doc["testerGate"]["feedbackLoop"]["requiredFields"]
    assert doc["testerGate"]["supportPath"]["killSwitchOwner"] == "operator"

    controls = doc["controls"]
    assert controls["labels"] == {
        "environment": "solana-devnet-only",
        "mainnet": "mainnet-blocked-until-audit",
        "value": "no-real-value",
        "wallet": "dedicated-devnet-wallet-only",
    }
    assert controls["walletSeparation"]["devnetWalletRequired"] is True
    assert controls["walletSeparation"]["productionKeyImportAllowed"] is False
    assert controls["caps"]["perAttemptMinorUnits"] == 100_000
    assert controls["caps"]["capEnforcedBeforeSigning"] is True
    assert controls["caps"]["capRecheckedBeforeReceipt"] is True
    assert controls["allowlists"]["cluster"] == "devnet"
    assert controls["allowlists"]["mints"][0]["mint"] == "DevnetMint111111111111111111111111111111111"
    assert controls["allowlists"]["programs"][0]["programId"] == "DevnetProgram111111111111111111111111111111"
    assert controls["proofRequirements"]["confirmation"]["minimumCommitment"] == "confirmed"
    assert controls["proofRequirements"]["confirmation"]["finalizedRequiredForCloseout"] is True
    assert "authorityState" in controls["proofRequirements"]
    assert "rollbackEvidence" in controls["proofRequirements"]

    assert doc["scenarioSummary"] == {
        "failClosedScenarios": 5,
        "negativeScenarios": 5,
        "positiveScenarios": 2,
        "receiptProofScenarios": 3,
        "rollbackScenarios": 7,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["devnet-onboarding-ready"]["status"] == "pass"
    assert scenarios["devnet-onboarding-ready"]["inputs"]["labels"] == [
        "solana-devnet-only",
        "dedicated-devnet-wallet-only",
        "no-real-value",
    ]
    assert scenarios["devnet-onboarding-ready"]["inputs"]["transaction"] == {
        "confirmationStatus": "confirmed",
        "err": None,
        "signature": "devnet-sig-onboarding-ready",
        "slot": 49_000,
    }
    assert scenarios["devnet-confirmation-and-receipt-pass"]["status"] == "pass"
    assert scenarios["devnet-confirmation-and-receipt-pass"]["inputs"]["attempt"]["amountMinorUnits"] == 75_000
    assert scenarios["devnet-confirmation-and-receipt-pass"]["inputs"]["receipt"]["settlementProof"] == "devnet-signature-only"
    assert scenarios["expired-mandate-denied"]["status"] == "fail"
    assert "scenarios.expired-mandate-denied.attempt.slot" in {finding["path"] for finding in scenarios["expired-mandate-denied"]["findings"]}
    assert scenarios["replayed-request-denied"]["status"] == "fail"
    assert scenarios["replayed-request-denied"]["inputs"]["replay"]["previousReceiptId"] == "receipt-devnet-confirmation-pass"
    assert "scenarios.replayed-request-denied.replay.previousNonceSeen" in {finding["path"] for finding in scenarios["replayed-request-denied"]["findings"]}
    assert scenarios["over-budget-denied"]["status"] == "fail"
    assert "scenarios.over-budget-denied.attempt.amountMinorUnits" in {finding["path"] for finding in scenarios["over-budget-denied"]["findings"]}
    assert scenarios["wrong-mint-program-denied"]["status"] == "fail"
    wrong_paths = {finding["path"] for finding in scenarios["wrong-mint-program-denied"]["findings"]}
    assert "scenarios.wrong-mint-program-denied.authority.mint" in wrong_paths
    assert "scenarios.wrong-mint-program-denied.authority.programId" in wrong_paths
    assert scenarios["payment-settled-service-failed-denied"]["status"] == "fail"
    atomicity_paths = {finding["path"] for finding in scenarios["payment-settled-service-failed-denied"]["findings"]}
    assert "scenarios.payment-settled-service-failed-denied.receipt.serviceOutcome" in atomicity_paths
    assert "scenarios.payment-settled-service-failed-denied.receipt.evalStatus" in atomicity_paths
    assert scenarios["payment-settled-service-failed-denied"]["inputs"]["rollback"]["receiptMarkedForReview"] is True

    for key, expected in {
        "deterministicDevnetGateDesign": True,
        "consumesLocalnetAndRoadmapOnly": True,
        "externalTesterGateDesignOnly": True,
        "devnetExecution": False,
        "mainnetAccess": False,
        "productionCredentialAccess": False,
        "realValueWalletAccess": False,
        "facilitatorAction": False,
        "settlementAction": False,
        "hostedDeployment": False,
        "packagePublished": False,
        "productionGatewayMutation": False,
        "runtimeActivation": False,
        "providerApiAccess": False,
        "mcpInvocation": False,
        "externalSpend": False,
    }.items():
        assert doc["boundaries"][key] is expected

    assert run_gate("--requested-decision", "hold")["decision"] == "hold"
    assert run_gate("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert gate.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_scenario_mutation_fails(0, lambda scenario: scenario["boundaries"].update({"mainnetUsed": True}), "scenarios.devnet-onboarding-ready.boundaries.mainnetUsed")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["labels"].remove("solana-devnet-only"), "scenarios.devnet-onboarding-ready.labels.solana-devnet-only")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["rollback"].update({"killSwitchState": "disabled"}), "scenarios.devnet-onboarding-ready.rollback.killSwitchState")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["transaction"].update({"confirmationStatus": "processed"}), "scenarios.devnet-confirmation-and-receipt-pass.transaction.confirmationStatus")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["receipt"].update({"settlementProof": "mainnet-signature"}), "scenarios.devnet-confirmation-and-receipt-pass.receipt.settlementProof")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["authority"].update({"payee": "unknown"}), "scenarios.devnet-confirmation-and-receipt-pass.authority.payee")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["boundaries"].update({"productionKeyUsed": True}), "scenarios.devnet-confirmation-and-receipt-pass.boundaries.productionKeyUsed")

    assert_packet_mutation_fails(lambda rehearsal_doc, *_: rehearsal_doc.update({"decision": "hold"}), "localnetRehearsalPacket.decision")
    assert_packet_mutation_fails(lambda rehearsal_doc, *_: rehearsal_doc["acceptanceEvidence"].update({"readyForDevnetGate": False}), "localnetRehearsalPacket.acceptanceEvidence.readyForDevnetGate")
    assert_packet_mutation_fails(lambda rehearsal_doc, *_: rehearsal_doc["boundaries"].update({"devnetAccess": True}), "localnetRehearsalPacket.boundaries.devnetAccess")
    assert_packet_mutation_fails(lambda _rehearsal_doc, _rehearsal_binding, _roadmap_text, roadmap_binding, *_: roadmap_binding.update({"sha256": ""}), "roadmapPacket.sha256")
    assert_packet_mutation_fails(lambda *_args: _args[4].update({"devnetExecution": True}), "boundaries.devnetExecution")
    assert_packet_mutation_fails(lambda *_args: _args[5][0].update({"status": "fail"}), "scenarios.devnet-onboarding-ready.status")
    assert_packet_mutation_fails(lambda *_args: _args[5][2].update({"status": "pass"}), "scenarios.expired-mandate-denied.status")

    print("PASS Solana devnet external tester gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
