#!/usr/bin/env python3
"""Check ADL v0.2 local beta release signoff packet evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-adl-v02-release-signoff-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_signoff_packet as signoff  # noqa: E402


def run_signoff(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_adl_v02_release_signoff_packet.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    binding = signoff.rc_gate_binding()
    rc_doc = signoff.load_json(ROOT / signoff.REQUIRED_RC_GATE_PATH)
    boundaries = signoff.signoff_boundaries()
    mutator(rc_doc, binding, boundaries)
    findings = signoff.collect_findings(rc_doc, binding, boundaries)
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_signoff()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "adl-v02-local-beta-release-signoff-packet"
    assert doc["issue"] == 351
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337, 339, 341, 343, 345, 347, 349]
    assert doc["status"] == "pass"
    assert doc["decision"] == "release-ready"
    assert doc["releaseSignoffPacketId"] == "reddiagent-beta-0-adl-v02-local-release-signoff-packet"
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    rc_gate = doc["releaseCandidateGate"]
    assert rc_gate["path"] == "tests/fixtures/beta-adl-v02-release-candidate-gate.json"
    assert rc_gate["issue"] == 349
    assert rc_gate["status"] == "pass"
    assert rc_gate["decision"] == "rc-ready"
    assert rc_gate["sha256"] == doc["artifactHashes"]["tests/fixtures/beta-adl-v02-release-candidate-gate.json"]

    handoff = doc["acceptedBaselineHandoff"]
    assert handoff["path"] == "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"
    assert handoff["issue"] == 347
    assert handoff["status"] == "pass"
    assert handoff["decision"] == "continue"

    acceptance_smoke = doc["baselineAcceptanceSmoke"]
    assert acceptance_smoke["path"] == "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"
    assert acceptance_smoke["issue"] == 345
    assert acceptance_smoke["status"] == "pass"
    assert acceptance_smoke["decision"] == "accept"

    upstream = doc["upstreamPromotionPacket"]
    assert upstream["path"] == "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"
    assert upstream["issue"] == 343
    assert upstream["status"] == "pass"
    assert upstream["decision"] == "promote"

    chain = {item["issue"]: item for item in doc["evidenceChain"]}
    assert chain[337]["path"] == "tests/fixtures/beta-release-handoff.json"
    assert chain[339]["path"] == "tests/fixtures/beta-reviewer-walkthrough-smoke.json"
    assert chain[341]["path"] == "tests/fixtures/beta-adl-v02-local-readiness-gate.json"
    assert chain[343]["path"] == "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"
    assert chain[345]["path"] == "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"
    assert chain[347]["path"] == "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"
    assert chain[349]["path"] == "tests/fixtures/beta-adl-v02-release-candidate-gate.json"
    assert all(item["sha256"] and item["sizeBytes"] for item in chain.values())

    assert doc["artifactHashes"]["examples/v0.2/memory-observability-agent.yaml"] == "ae0659fae7e216b6f4e252bd7e5a88de3f08168c45234931a129effdba3a2499"
    assert doc["artifactHashes"]["examples/invalid/adl-v0.2-x402-missing-authority.yaml"] == "eb4387034bcd29b76ac561bd99bbf59986f7078ed6bd74b404419a85236deca8"
    assert doc["artifactHashes"]["tests/fixtures/beta-release-handoff.json"] == "83bb49d081367800ea24a7dbf2587550291099f8045f735dd67ff5e2588db8dd"
    assert doc["artifactHashes"]["tests/fixtures/beta-reviewer-walkthrough-smoke.json"] == "5086e1121e7ac967471bb2618ea9edc7b847ee119b7fe4b804b58418ebde2d19"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-local-readiness-gate.json"] == "56534c3e8baed48dd5044c36e2571f53d6b2d5e1b83aab1532ca1db419b00c03"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"] == "eb7bbfb8cee6eb6942fc832d7718f98df101fcce9678379cb050474ba97d546b"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"] == "626c2e02b52d66591a90083429b9a68b98a565be34ce5c0c2e48e6399c1f5156"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"] == "c39bf9aa725c6b0137270d8d7dd26d446bc64f3a52b9628f01199c431ca09431"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-release-candidate-gate.json"] == "378932dc7cc9c48eb7e7c5b15a68e8f25a330fba14bebad844e309ff593c27b0"

    baseline = doc["adlV02RuntimeBaseline"]
    assert baseline["validRuntimeExample"]["adl"] == "examples/v0.2/memory-observability-agent.yaml"
    assert baseline["validRuntimeExample"]["status"] == "pass"
    assert baseline["validRuntimeExample"]["exitCode"] == 0
    assert baseline["invalidDiagnosticSample"]["adl"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"
    assert baseline["invalidDiagnosticSample"]["exitCode"] == 1
    assert baseline["invalidDiagnosticSample"]["stableFields"] == ["code", "severity", "category", "path", "line", "column"]
    assert baseline["invalidDiagnosticSample"]["diagnostics"][0] == {
        "code": "adl_v0_2_schema.required.extensions_x402_intents_0_authority",
        "severity": "error",
        "category": "payment",
        "path": "extensions.x402.intents.0.authority",
        "line": 22,
        "column": 9,
    }

    for key, expected in {
        "deterministicLocalReleaseSignoffPacket": True,
        "consumesReleaseCandidateGateOnly": True,
        "releaseSignoffDecisionOnly": True,
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

    assert run_signoff("--requested-decision", "hold")["decision"] == "hold"
    assert run_signoff("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert signoff.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc.update({"decision": "hold"}),
        "releaseCandidateGate.decision",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc.update({"status": "fail"}),
        "releaseCandidateGate.status",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["acceptedBaselineHandoff"].update({"decision": "hold"}),
        "releaseCandidateGate.acceptedBaselineHandoff.decision",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["baselineAcceptanceSmoke"].update({"decision": "hold"}),
        "releaseCandidateGate.baselineAcceptanceSmoke.decision",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["upstreamPromotionPacket"].update({"decision": "hold"}),
        "releaseCandidateGate.upstreamPromotionPacket.decision",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["evidenceChain"][5].update({"sha256": ""}),
        "releaseCandidateGate.evidenceChain.347.sha256",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["artifactHashes"].update({"examples/v0.2/memory-observability-agent.yaml": ""}),
        "releaseCandidateGate.artifactHashes.examples/v0.2/memory-observability-agent.yaml",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["adlV02RuntimeBaseline"]["validRuntimeExample"].update({"exitCode": 1}),
        "releaseCandidateGate.adlV02RuntimeBaseline.validRuntimeExample.exitCode",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["adlV02RuntimeBaseline"]["invalidDiagnosticSample"]["diagnostics"][0].pop("column"),
        "releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].column",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: rc_doc["boundaries"].update({"networkAccess": True}),
        "releaseCandidateGate.boundaries.networkAccess",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: boundaries.update({"dockerMutation": True}),
        "boundaries.dockerMutation",
    )
    assert_finding_after_mutation(
        lambda rc_doc, binding, boundaries: binding.update({"sha256": ""}),
        "releaseCandidateGate.sha256",
    )

    print("PASS ADL v0.2 local beta release signoff packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
