#!/usr/bin/env python3
"""Check RAP x402/AP2 audit-prep alignment evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "rap-x402-ap2-audit-prep-alignment-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import rap_x402_ap2_audit_prep_alignment_packet as packet  # noqa: E402


def run_packet(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/rap_x402_ap2_audit_prep_alignment_packet.py", *extra_args],
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
        "roadmap": packet.artifact_binding(packet.ROADMAP_PACKET_PATH, issue=356),
        "localnetRehearsal": packet.artifact_binding(packet.LOCALNET_PACKET_PATH, issue=359),
        "devnetTesterGate": packet.artifact_binding(packet.DEVNET_GATE_PATH, issue=360),
        "rapBridgeReady": packet.artifact_binding(packet.RAP_BRIDGE_READY_PATH),
        "ap2X402MandateReady": packet.artifact_binding(packet.AP2_X402_READY_PATH),
        "mcpRuntimeHandoffReady": packet.artifact_binding(packet.MCP_HANDOFF_READY_PATH),
    }
    roadmap_text = (ROOT / packet.ROADMAP_PACKET_PATH).read_text(encoding="utf-8")
    localnet_doc = packet.load_json(ROOT / packet.LOCALNET_PACKET_PATH)
    devnet_doc = packet.load_json(ROOT / packet.DEVNET_GATE_PATH)
    rap_ready_doc = packet.load_json(ROOT / packet.RAP_BRIDGE_READY_PATH)
    ap2_ready_doc = packet.load_json(ROOT / packet.AP2_X402_READY_PATH)
    boundaries = packet.boundaries()
    layers = packet.layer_contract()
    mappings = packet.source_field_mapping()
    deltas = packet.audit_deltas()
    scenarios = [packet.build_scenario_result(scenario) for scenario in packet.default_scenarios()]
    mutator(
        roadmap_text,
        artifacts,
        localnet_doc,
        devnet_doc,
        rap_ready_doc,
        ap2_ready_doc,
        boundaries,
        layers,
        mappings,
        deltas,
        scenarios,
    )
    findings = packet.collect_packet_findings(
        roadmap_text,
        artifacts,
        localnet_doc,
        devnet_doc,
        rap_ready_doc,
        ap2_ready_doc,
        boundaries,
        layers,
        mappings,
        deltas,
        scenarios,
    )
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_packet()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "rap-x402-ap2-audit-prep-alignment-packet"
    assert doc["issue"] == 361
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [356, 359, 360]
    assert doc["status"] == "pass"
    assert doc["decision"] == "audit-prep-ready"
    assert doc["packetId"] == "reddiagent-rap-x402-ap2-audit-prep-alignment"
    assert "Mainnet remains blocked" in doc["mainnetStatement"]

    artifacts = doc["artifacts"]
    assert artifacts["roadmap"]["issue"] == 356
    assert artifacts["localnetRehearsal"]["issue"] == 359
    assert artifacts["devnetTesterGate"]["issue"] == 360
    for artifact in artifacts.values():
        assert artifact["exists"] is True
        assert artifact["sha256"]
        assert artifact["sizeBytes"]

    layers = {entry["layer"]: entry for entry in doc["layerContract"]}
    assert set(layers) == {
        "delegatedAuthority",
        "resourceAccess",
        "paymentEvidence",
        "settlementProof",
        "receiptAccountingReputation",
    }
    assert "authority.mandateId" in layers["delegatedAuthority"]["adlRapFields"]
    assert "policy.resourceAccess" in layers["resourceAccess"]["adlRapFields"]
    assert "x402.PaymentResponse.transactionRef" in layers["paymentEvidence"]["adlRapFields"]
    assert "settlement.signature" in layers["settlementProof"]["adlRapFields"]
    assert "reputation.signals" in layers["receiptAccountingReputation"]["adlRapFields"]

    mappings = {entry["standard"]: entry for entry in doc["sourceFieldMapping"]}
    assert set(mappings) == {
        "x402",
        "AP2/FIDO/Verifiable Intent",
        "MCP authorization",
        "Solana payment proof",
        "RAP receipt/accounting/reputation",
    }
    assert "PAYMENT-REQUIRED / PaymentRequired.accepts" in mappings["x402"]["standardFields"]
    assert "payment-identifier" in mappings["x402"]["standardFields"]
    assert "IntentMandate" in mappings["AP2/FIDO/Verifiable Intent"]["standardFields"]
    assert "verifiable credential issuer/subject" in mappings["AP2/FIDO/Verifiable Intent"]["standardFields"]
    assert "OAuth protected resource metadata" in mappings["MCP authorization"]["standardFields"]
    assert "authorization_servers" in mappings["MCP authorization"]["standardFields"]
    assert "confirmationStatus" in mappings["Solana payment proof"]["standardFields"]
    assert "mint" in mappings["Solana payment proof"]["standardFields"]
    assert "required_eval_gate_pass" in doc["scenarios"][0]["inputs"]["receipt"]["reputationSignals"]

    for area in (
        "invariants",
        "replayResistance",
        "atomicity",
        "delegatedAuthority",
        "spendLimits",
        "privacyPii",
        "receiptSettlementProof",
        "rollbackKillSwitch",
    ):
        assert area in doc["auditDeltas"]
        assert doc["auditDeltas"][area]["mustProve"]
        assert doc["auditDeltas"][area]["readyWhen"]

    assert doc["scenarioSummary"] == {
        "atomicityScenarios": 1,
        "failClosedScenarios": 5,
        "negativeScenarios": 5,
        "positiveScenarios": 1,
        "privacyScenarios": 1,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["complete-authorized-paid-service-bundle"]["status"] == "pass"
    positive = scenarios["complete-authorized-paid-service-bundle"]["inputs"]
    assert positive["x402"]["selectedRail"] == "solana-devnet-usdc"
    assert positive["mcp"]["resourceAccessAuthorized"] is True
    assert positive["settlement"]["cluster"] == "devnet"
    assert positive["receipt"]["serviceResultStatus"] == "pass"
    assert positive["privacy"]["rawPiiStored"] is False
    assert positive["rollback"]["killSwitchArmed"] is True
    assert positive["boundaries"]["realValueTransfer"] is False

    assert scenarios["payment-settled-service-failed"]["status"] == "fail"
    assert "scenarios.payment-settled-service-failed.receipt.serviceResultStatus" in {
        finding["path"] for finding in scenarios["payment-settled-service-failed"]["findings"]
    }
    assert scenarios["valid-authorization-wrong-purpose"]["status"] == "fail"
    assert "scenarios.valid-authorization-wrong-purpose.authority.purpose" in {
        finding["path"] for finding in scenarios["valid-authorization-wrong-purpose"]["findings"]
    }
    assert scenarios["stale-replayed-mandate"]["status"] == "fail"
    assert scenarios["stale-replayed-mandate"]["inputs"]["replay"]["previousReceiptId"] == "receipt-audit-prior"
    assert scenarios["devnet-mainnet-confusion"]["status"] == "fail"
    assert scenarios["devnet-mainnet-confusion"]["inputs"]["boundaries"]["mainnetUsed"] is True
    assert scenarios["raw-pii-in-receipt"]["status"] == "fail"

    for key, expected in {
        "deterministicAuditPrepPacket": True,
        "researchSpecAuditPrepOnly": True,
        "liveRuntimeActivation": False,
        "hostedDeployment": False,
        "dockerSurfpoolCoolifyMutation": False,
        "credentialAccess": False,
        "liveMcpInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "walletAccess": False,
        "paymentFacilitatorSettlementAction": False,
        "packagePublishing": False,
        "productionGatewayMutation": False,
    }.items():
        assert doc["boundaries"][key] is expected

    assert run_packet("--requested-decision", "hold")["decision"] == "hold"
    assert run_packet("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert packet.decision_for([{"path": "x", "reason": "y"}], "audit-prep-ready") == "hold"

    assert_scenario_mutation_fails(0, lambda scenario: scenario["receipt"].update({"serviceResultStatus": "fail"}), "scenarios.complete-authorized-paid-service-bundle.receipt.serviceResultStatus")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["receipt"].update({"requiredEvalGateStatus": "fail"}), "scenarios.complete-authorized-paid-service-bundle.receipt.requiredEvalGateStatus")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["authority"].update({"purpose": "wrong-purpose"}), "scenarios.complete-authorized-paid-service-bundle.authority.purpose")
    assert_scenario_mutation_fails(0, lambda scenario: scenario.update({"replay": {"nonceSeen": True}}), "scenarios.complete-authorized-paid-service-bundle.replay.nonceSeen")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["settlement"].update({"cluster": "mainnet-beta"}), "scenarios.complete-authorized-paid-service-bundle.settlement.cluster")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["privacy"].update({"rawPiiStored": True}), "scenarios.complete-authorized-paid-service-bundle.privacy.rawPiiStored")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["boundaries"].update({"realValueTransfer": True}), "scenarios.complete-authorized-paid-service-bundle.boundaries.realValueTransfer")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["boundaries"].update({"liveFacilitatorUsed": True}), "scenarios.complete-authorized-paid-service-bundle.boundaries.liveFacilitatorUsed")

    assert_packet_mutation_fails(lambda _roadmap, artifacts, *_: artifacts["roadmap"].update({"sha256": ""}), "artifacts.roadmap")
    assert_packet_mutation_fails(lambda _roadmap, _artifacts, localnet_doc, *_: localnet_doc.update({"decision": "hold"}), "localnet.decision")
    assert_packet_mutation_fails(lambda _roadmap, _artifacts, _localnet, devnet_doc, *_: devnet_doc.update({"decision": "hold"}), "devnet.decision")
    assert_packet_mutation_fails(lambda _roadmap, _artifacts, _localnet, _devnet, rap_ready_doc, *_: rap_ready_doc["conformance"].update({"liveBridgeAllowed": True}), "rapBridge.conformance.liveBridgeAllowed")
    assert_packet_mutation_fails(lambda _roadmap, _artifacts, _localnet, _devnet, _rap, ap2_ready_doc, *_: ap2_ready_doc["ap2"]["mandates"]["PaymentMandate"].pop("revocationRef"), "ap2X402.ap2.mandates.PaymentMandate")
    assert_packet_mutation_fails(lambda *_args: _args[6].update({"mainnetRun": True}), "boundaries.mainnetRun")
    assert_packet_mutation_fails(lambda *_args: _args[7].pop(), "layerContract")
    assert_packet_mutation_fails(lambda *_args: _args[8].pop(), "sourceFieldMapping")
    assert_packet_mutation_fails(lambda *_args: _args[9].pop("atomicity"), "auditDeltas")
    assert_packet_mutation_fails(lambda *_args: _args[10][0].update({"status": "fail"}), "scenarios.complete-authorized-paid-service-bundle.status")
    assert_packet_mutation_fails(lambda *_args: _args[10][1].update({"status": "pass", "findings": []}), "scenarios.payment-settled-service-failed.status")

    print("PASS RAP x402/AP2 audit-prep alignment packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
