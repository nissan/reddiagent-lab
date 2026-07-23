#!/usr/bin/env python3
"""Check smart-contract audit-readiness freeze packet evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "smart-contract-audit-readiness-freeze-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import smart_contract_audit_readiness_freeze_packet as packet  # noqa: E402


def run_packet(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/smart_contract_audit_readiness_freeze_packet.py", *extra_args],
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
        "rapX402Ap2AuditPrep": packet.artifact_binding(packet.AUDIT_PREP_PATH, issue=361),
        "externalTesterMvp": packet.artifact_binding(packet.TESTER_MVP_PATH, issue=365),
        "roadmap": packet.artifact_binding(packet.ROADMAP_PATH),
        "readme": packet.artifact_binding(packet.README_PATH),
    }
    roadmap_text = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in (packet.ROADMAP_PATH, packet.README_PATH))
    audit_doc = packet.load_json(ROOT / packet.AUDIT_PREP_PATH)
    tester_doc = packet.load_json(ROOT / packet.TESTER_MVP_PATH)
    boundary_doc = packet.boundaries()
    checklist = packet.freeze_checklist()
    evidence = packet.evidence_requirements()
    threats = packet.threat_model()
    limitations = packet.known_limitations()
    blockers = packet.blocker_catalog()
    scenarios = [packet.build_scenario_result(scenario) for scenario in packet.default_scenarios()]
    mutator(artifacts, roadmap_text, audit_doc, tester_doc, boundary_doc, checklist, evidence, threats, limitations, blockers, scenarios)
    findings = packet.collect_packet_findings(
        artifacts,
        roadmap_text,
        audit_doc,
        tester_doc,
        boundary_doc,
        checklist,
        evidence,
        threats,
        limitations,
        blockers,
        scenarios,
    )
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_packet()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "smart-contract-audit-readiness-freeze-packet"
    assert doc["issue"] == 366
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [361, 365]
    assert doc["status"] == "pass"
    assert doc["decision"] == "audit-freeze-ready"
    assert doc["packetId"] == "reddiagent-smart-contract-audit-readiness-freeze"
    assert "Mainnet remains blocked" in doc["mainnetStatement"]
    assert "does not authorize smart-contract deployment" in doc["executionStatement"]

    artifacts = doc["artifacts"]
    assert artifacts["rapX402Ap2AuditPrep"]["issue"] == 361
    assert artifacts["externalTesterMvp"]["issue"] == 365
    for artifact in artifacts.values():
        assert artifact["exists"] is True
        assert artifact["sha256"]
        assert artifact["sizeBytes"]

    for area in packet.FREEZE_AREAS:
        assert area in doc["freezeChecklist"]
        assert doc["freezeChecklist"][area]["criteria"]
        assert doc["freezeChecklist"][area]["evidence"]
        assert doc["freezeChecklist"][area]["blockers"]

    evidence_names = {item["name"] for item in doc["evidenceRequirements"]}
    for item in packet.REQUIRED_EVIDENCE:
        assert item in evidence_names
    for blocker in packet.REQUIRED_BLOCKERS:
        assert blocker in doc["blockers"]

    assert doc["scenarioSummary"] == {
        "failClosedScenarios": 6,
        "mainnetAmbiguityScenarios": 1,
        "negativeScenarios": 6,
        "positiveScenarios": 1,
        "privacyScenarios": 1,
    }
    scenarios = {scenario["id"]: scenario for scenario in doc["scenarios"]}
    assert scenarios["freeze-ready-baseline"]["status"] == "pass"
    assert scenarios["unclear-authority-blocked"]["status"] == "fail"
    assert scenarios["replayed-mandate-blocked"]["status"] == "fail"
    assert scenarios["devnet-mainnet-ambiguity-blocked"]["status"] == "fail"
    assert "scenarios.devnet-mainnet-ambiguity-blocked.boundaries.mainnetRun" in {
        finding["path"] for finding in scenarios["devnet-mainnet-ambiguity-blocked"]["findings"]
    }
    assert scenarios["unbounded-spend-blocked"]["status"] == "fail"
    assert scenarios["rollback-evidence-missing-blocked"]["status"] == "fail"
    assert scenarios["privacy-leak-blocked"]["status"] == "fail"

    for key, expected in {
        "deterministicPacketOnly": True,
        "consumesPriorEvidenceOnly": True,
        "officialAuditRequiredBeforePaymentCapablePublicBeta": True,
        "explicitGoLiveReadinessRequired": True,
        "smartContractDeployment": False,
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
        "externalTesterExecution": False,
        "externalSpend": False,
    }.items():
        assert doc["boundaries"][key] is expected

    assert run_packet("--requested-decision", "hold")["decision"] == "hold"
    assert run_packet("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert packet.decision_for([{"path": "x", "reason": "y"}], "audit-freeze-ready") == "hold"

    assert_scenario_mutation_fails(0, lambda scenario: scenario["freezeAreas"].remove("privacyPii"), "scenarios.freeze-ready-baseline.freezeAreas.privacyPii")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["evidence"].remove("threat model"), "scenarios.freeze-ready-baseline.evidence.threat model")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["blockers"].remove("unbounded spend"), "scenarios.freeze-ready-baseline.blockers.unbounded spend")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["authority"].update({"auditRef": False}), "scenarios.freeze-ready-baseline.authority.auditRef")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["replay"].update({"duplicateReceiptAccepted": True}), "scenarios.freeze-ready-baseline.replay.idempotency")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["allowlist"].update({"programAllowed": False}), "scenarios.freeze-ready-baseline.allowlist.programAllowed")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["caps"].update({"boundedSpend": False}), "scenarios.freeze-ready-baseline.caps.boundedSpend")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["proof"].update({"paymentServiceEvalAgree": False}), "scenarios.freeze-ready-baseline.proof.paymentServiceEvalAgree")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["privacy"].update({"productionWalletMaterialCaptured": True}), "scenarios.freeze-ready-baseline.privacy.productionWalletMaterialCaptured")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["rollback"].update({"killSwitchArmed": False}), "scenarios.freeze-ready-baseline.rollback.killSwitchArmed")
    assert_scenario_mutation_fails(0, lambda scenario: scenario["boundaries"].update({"devnetRun": True}), "scenarios.freeze-ready-baseline.boundaries.devnetRun")

    assert_packet_mutation_fails(lambda artifacts, *_: artifacts["externalTesterMvp"].update({"sha256": ""}), "artifacts.externalTesterMvp")
    assert_packet_mutation_fails(lambda _artifacts, _roadmap, audit_doc, *_: audit_doc.update({"decision": "hold"}), "auditPrep.decision")
    assert_packet_mutation_fails(lambda _artifacts, _roadmap, _audit, tester_doc, *_: tester_doc.update({"decision": "hold"}), "testerMvp.decision")
    assert_packet_mutation_fails(lambda *_args: _args[4].update({"mainnetRun": True}), "boundaries.mainnetRun")
    assert_packet_mutation_fails(lambda *_args: _args[5].pop("replayIdempotency"), "freezeChecklist.replayIdempotency")
    assert_packet_mutation_fails(lambda *_args: _args[6].pop(), "evidenceRequirements.no-mainnet boundary proof")
    assert_packet_mutation_fails(lambda *_args: _args[7].clear(), "threatModel.authorityMandateBinding")
    assert_packet_mutation_fails(lambda *_args: _args[8].clear(), "knownLimitations.officialAudit")
    assert_packet_mutation_fails(lambda *_args: _args[9].pop("unbounded spend"), "blockers.unbounded spend")
    assert_packet_mutation_fails(lambda *_args: _args[10][1].update({"status": "pass"}), "scenarios.unclear-authority-blocked.status")

    print("PASS smart-contract audit-readiness freeze packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
