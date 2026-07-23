#!/usr/bin/env python3
"""Check external tester MVP packet evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-tester-mvp-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_tester_mvp_packet as packet  # noqa: E402


def run_packet(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_external_tester_mvp_packet.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_scenario_mutation_fails(index: int, mutator, expected_path: str) -> None:
    scenario = json.loads(json.dumps(packet.default_scenarios()[index]))
    mutator(scenario["inputs"])
    findings = packet.scenario_findings(scenario)
    assert expected_path in {finding["path"] for finding in findings}


def assert_packet_mutation_fails(mutator, expected_path: str) -> None:
    artifacts = {
        "localnetRehearsal": packet.artifact_binding(packet.LOCALNET_PACKET_PATH, issue=359),
        "devnetTesterGate": packet.artifact_binding(packet.DEVNET_GATE_PATH, issue=360),
        "rapX402Ap2AuditPrep": packet.artifact_binding(packet.AUDIT_PREP_PATH, issue=361),
        "roadmap": packet.artifact_binding(packet.ROADMAP_PATH, issue=367),
        "visionRoadmap": packet.artifact_binding(packet.VISION_ROADMAP_PATH, issue=367),
        "docsIndex": packet.artifact_binding(packet.INDEX_PATH, issue=367),
        "readme": packet.artifact_binding(packet.README_PATH, issue=367),
    }
    roadmap_texts = {
        "roadmap": (ROOT / packet.ROADMAP_PATH).read_text(encoding="utf-8"),
        "visionRoadmap": (ROOT / packet.VISION_ROADMAP_PATH).read_text(encoding="utf-8"),
        "docsIndex": (ROOT / packet.INDEX_PATH).read_text(encoding="utf-8"),
        "readme": (ROOT / packet.README_PATH).read_text(encoding="utf-8"),
    }
    localnet_doc = packet.load_json(ROOT / packet.LOCALNET_PACKET_PATH)
    devnet_doc = packet.load_json(ROOT / packet.DEVNET_GATE_PATH)
    audit_doc = packet.load_json(ROOT / packet.AUDIT_PREP_PATH)
    boundaries = packet.boundaries()
    mvp = packet.tester_mvp()
    controls = packet.controls()
    matrix = packet.acceptance_matrix()
    scenarios = [packet.build_scenario_result(scenario) for scenario in packet.default_scenarios()]
    mutator(artifacts, roadmap_texts, localnet_doc, devnet_doc, audit_doc, boundaries, mvp, controls, matrix, scenarios)
    findings = packet.collect_packet_findings(
        artifacts,
        roadmap_texts,
        localnet_doc,
        devnet_doc,
        audit_doc,
        boundaries,
        mvp,
        controls,
        matrix,
        scenarios,
    )
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_packet()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "external-tester-mvp-packet"
    assert doc["issue"] == 365
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [359, 360, 361, 367]
    assert doc["status"] == "pass"
    assert doc["decision"] == "mvp-packet-ready"
    assert doc["packetId"] == "reddiagent-external-tester-mvp-cohort-0-packet"
    assert "Mainnet remains blocked" in doc["mainnetStatement"]
    assert "does not authorize external tester execution" in doc["executionStatement"]

    artifacts = doc["artifacts"]
    assert artifacts["localnetRehearsal"]["issue"] == 359
    assert artifacts["devnetTesterGate"]["issue"] == 360
    assert artifacts["rapX402Ap2AuditPrep"]["issue"] == 361
    assert artifacts["roadmap"]["issue"] == 367
    for artifact in artifacts.values():
        assert artifact["exists"] is True
        assert artifact["sha256"]
        assert artifact["sizeBytes"]

    mvp = doc["testerMvp"]
    assert mvp["cohort"]["name"] == "external-tester-mvp-cohort-0"
    assert mvp["cohort"]["size"] == {"maximum": 5, "minimum": 3}
    assert mvp["cohort"]["roles"] == ["builder", "operator", "protocol-reviewer"]
    assert "successful cohort-0 closeout" in mvp["cohort"]["expansionRequires"]
    assert len(mvp["onboardingPacket"]) >= 8
    assert "transaction signature or expected fail-closed code" in mvp["feedbackCapture"]["requiredFields"]
    assert "never capture secrets" in mvp["feedbackCapture"]["privacyRule"]
    assert mvp["support"]["safetyOwner"] == "operator"

    controls = doc["controls"]
    assert controls["labels"] == {
        "environment": "solana-devnet-only",
        "mainnet": "mainnet-blocked-until-official-audit-and-go-live-readiness",
        "value": "no-real-value",
        "wallet": "dedicated-devnet-wallet-only",
    }
    assert controls["walletKeySeparation"]["dedicatedDevnetWalletRequiredForFutureExecution"] is True
    assert controls["walletKeySeparation"]["productionKeyImportAllowed"] is False
    assert controls["walletKeySeparation"]["mainnetAddressAllowed"] is False
    assert controls["caps"]["perAttemptMinorUnits"] == 100_000
    assert controls["caps"]["preSignCapCheckRequired"] is True
    assert controls["caps"]["preReceiptCapCheckRequired"] is True
    assert controls["allowlists"]["cluster"] == "devnet"
    assert controls["allowlists"]["mints"] == ["DevnetMint111111111111111111111111111111111"]
    assert "rollback/kill-switch evidence" in controls["evidenceBundle"]

    matrix = doc["acceptanceMatrix"]
    assert "negative scenarios fail closed with rollback evidence" in matrix["accept"]
    assert "tester cannot confirm wallet/key separation" in matrix["hold"]
    assert "mainnet wallet/address/key material appears anywhere in the packet or feedback" in matrix["rollbackRequired"]

    assert doc["scenarioSummary"] == {
        "failClosedScenarios": 6,
        "mainnetAmbiguityScenarios": 1,
        "negativeScenarios": 6,
        "positiveScenarios": 2,
        "rollbackScenarios": 2,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["cohort-onboarding-ready"]["status"] == "pass"
    assert scenarios["receipt-eval-dispute-ready"]["status"] == "pass"
    assert scenarios["wallet-separation-missing"]["status"] == "fail"
    assert "scenarios.wallet-separation-missing.walletSeparation.dedicatedDevnetWallet" in {
        finding["path"] for finding in scenarios["wallet-separation-missing"]["findings"]
    }
    assert scenarios["mainnet-ambiguity-denied"]["status"] == "fail"
    assert "scenarios.mainnet-ambiguity-denied.boundaries.mainnetUsed" in {
        finding["path"] for finding in scenarios["mainnet-ambiguity-denied"]["findings"]
    }
    assert scenarios["over-cap-denied"]["status"] == "fail"
    assert scenarios["wrong-allowlist-denied"]["status"] == "fail"
    assert scenarios["payment-settled-service-failed-denied"]["status"] == "fail"
    assert "scenarios.payment-settled-service-failed-denied.receipt.atomicity" in {
        finding["path"] for finding in scenarios["payment-settled-service-failed-denied"]["findings"]
    }
    assert scenarios["rollback-evidence-missing-denied"]["status"] == "fail"
    assert "scenarios.rollback-evidence-missing-denied.rollback.rollbackEvidencePresent" in {
        finding["path"] for finding in scenarios["rollback-evidence-missing-denied"]["findings"]
    }

    for key, expected in {
        "deterministicPacketOnly": True,
        "consumesPriorEvidenceOnly": True,
        "laterBoundedExecutionDecisionRequired": True,
        "externalTesterExecution": False,
        "liveRuntimeActivation": False,
        "hostedDeployment": False,
        "dockerSurfpoolCoolifyMutation": False,
        "credentialAccess": False,
        "liveMcpInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "walletPaymentFacilitatorSettlementAction": False,
        "packageArchivePublishing": False,
        "productionGatewayMutation": False,
        "providerApiAccess": False,
        "externalSpend": False,
    }.items():
        assert doc["boundaries"][key] is expected

    assert run_packet("--requested-decision", "hold")["decision"] == "hold"
    assert run_packet("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert packet.decision_for([{"path": "x", "reason": "y"}], "mvp-packet-ready") == "hold"

    assert_scenario_mutation_fails(0, lambda scenario: scenario["labels"].remove("solana-devnet-only"), "scenarios.cohort-onboarding-ready.labels.solana-devnet-only")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["walletSeparation"].update({"productionKeyUsed": True}), "scenarios.cohort-onboarding-ready.walletSeparation.productionKeyUsed")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["allowlist"].update({"programAllowed": False}), "scenarios.cohort-onboarding-ready.allowlist.programAllowed")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["caps"].update({"withinGlobalCap": False}), "scenarios.cohort-onboarding-ready.caps.withinGlobalCap")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["receipt"].update({"evalOutcome": "fail"}), "scenarios.receipt-eval-dispute-ready.receipt.atomicity")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["rollback"].update({"killSwitchArmed": False}), "scenarios.receipt-eval-dispute-ready.rollback.killSwitchArmed")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["boundaries"].update({"devnetRunPerformed": True}), "scenarios.receipt-eval-dispute-ready.boundaries.externalTesterExecuted")
    assert_scenario_mutation_fails(1, lambda scenario: scenario["boundaries"].update({"realValueTransfer": True}), "scenarios.receipt-eval-dispute-ready.boundaries.mainnetUsed")

    assert_packet_mutation_fails(lambda artifacts, *_: artifacts["devnetTesterGate"].update({"sha256": ""}), "artifacts.devnetTesterGate")
    assert_packet_mutation_fails(
        lambda _artifacts, roadmap_texts, *_: roadmap_texts.update({key: "missing ladder" for key in roadmap_texts}),
        "roadmap.requiredTerms",
    )
    assert_packet_mutation_fails(lambda _artifacts, _roadmap, localnet_doc, *_: localnet_doc.update({"decision": "hold"}), "localnet.decision")
    assert_packet_mutation_fails(lambda _artifacts, _roadmap, _localnet, devnet_doc, *_: devnet_doc.update({"decision": "hold"}), "devnet.decision")
    assert_packet_mutation_fails(lambda _artifacts, _roadmap, _localnet, _devnet, audit_doc, *_: audit_doc.update({"decision": "hold"}), "auditPrep.decision")
    assert_packet_mutation_fails(lambda *_args: _args[5].update({"externalTesterExecution": True}), "boundaries.externalTesterExecution")
    assert_packet_mutation_fails(lambda *_args: _args[6]["cohort"].update({"size": {"minimum": 8, "maximum": 20}}), "testerMvp.cohort.size")
    assert_packet_mutation_fails(lambda *_args: _args[7]["walletKeySeparation"].update({"productionKeyImportAllowed": True}), "controls.walletKeySeparation.productionKeyImportAllowed")
    assert_packet_mutation_fails(lambda *_args: _args[8].update({"rollbackRequired": []}), "acceptanceMatrix.rollbackRequired")
    assert_packet_mutation_fails(lambda *_args: _args[9][0].update({"status": "fail"}), "scenarios.cohort-onboarding-ready.status")
    assert_packet_mutation_fails(lambda *_args: _args[9][2].update({"status": "pass"}), "scenarios.wallet-separation-missing.status")

    print("PASS external tester MVP packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
