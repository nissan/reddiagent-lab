#!/usr/bin/env python3
"""Check ADL v0.2 local beta release-candidate gate evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-adl-v02-release-candidate-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_candidate_gate as rc_gate  # noqa: E402


def run_rc_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_adl_v02_release_candidate_gate.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    binding = rc_gate.handoff_binding()
    handoff_doc = rc_gate.load_json(ROOT / rc_gate.REQUIRED_HANDOFF_PATH)
    boundaries = rc_gate.rc_boundaries()
    mutator(handoff_doc, binding, boundaries)
    findings = rc_gate.collect_findings(handoff_doc, binding, boundaries)
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_rc_gate()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "adl-v02-local-beta-release-candidate-gate"
    assert doc["issue"] == 349
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337, 339, 341, 343, 345, 347]
    assert doc["status"] == "pass"
    assert doc["decision"] == "rc-ready"
    assert doc["releaseCandidateGateId"] == "reddiagent-beta-0-adl-v02-local-release-candidate-gate"
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    handoff = doc["acceptedBaselineHandoff"]
    assert handoff["path"] == "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"
    assert handoff["issue"] == 347
    assert handoff["status"] == "pass"
    assert handoff["decision"] == "continue"
    assert handoff["sha256"] == doc["artifactHashes"]["tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"]

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
    assert all(item["sha256"] and item["sizeBytes"] for item in chain.values())

    assert doc["artifactHashes"]["examples/v0.2/memory-observability-agent.yaml"] == "ae0659fae7e216b6f4e252bd7e5a88de3f08168c45234931a129effdba3a2499"
    assert doc["artifactHashes"]["examples/invalid/adl-v0.2-x402-missing-authority.yaml"] == "eb4387034bcd29b76ac561bd99bbf59986f7078ed6bd74b404419a85236deca8"
    assert doc["artifactHashes"]["tests/fixtures/beta-release-handoff.json"] == "83bb49d081367800ea24a7dbf2587550291099f8045f735dd67ff5e2588db8dd"
    assert doc["artifactHashes"]["tests/fixtures/beta-reviewer-walkthrough-smoke.json"] == "4245bb0e5eb0407883e7fee6ec1fe8600b27257284426d769321b820d833aee6"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-local-readiness-gate.json"] == "760b4ef16370e0c21c4fc03333276bd8d88dda78886c316397e9391289244ffe"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"] == "4925690506e7eb6f829f868c8314aee5a64af8220153cc6cf6142bcbf26fa513"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"] == "3f6abeaaa116d8ee88991659d0daf4e36c3a90348775101f075fad94328e4c4f"

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
        "deterministicLocalReleaseCandidateGate": True,
        "consumesAcceptedBaselineHandoffOnly": True,
        "releaseCandidateDecisionOnly": True,
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

    assert run_rc_gate("--requested-decision", "hold")["decision"] == "hold"
    assert run_rc_gate("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert rc_gate.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc.update({"decision": "hold"}),
        "acceptedBaselineHandoff.decision",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc.update({"status": "fail"}),
        "acceptedBaselineHandoff.status",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["baselineAcceptanceSmoke"].update({"decision": "hold"}),
        "acceptedBaselineHandoff.baselineAcceptanceSmoke.decision",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["upstreamPromotionPacket"].update({"decision": "hold"}),
        "acceptedBaselineHandoff.upstreamPromotionPacket.decision",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["evidenceChain"][4].update({"sha256": ""}),
        "acceptedBaselineHandoff.evidenceChain.345.sha256",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["artifactHashes"].update({"examples/v0.2/memory-observability-agent.yaml": ""}),
        "acceptedBaselineHandoff.artifactHashes.examples/v0.2/memory-observability-agent.yaml",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["adlV02RuntimeBaseline"]["validRuntimeExample"].update({"exitCode": 1}),
        "acceptedBaselineHandoff.adlV02RuntimeBaseline.validRuntimeExample.exitCode",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["adlV02RuntimeBaseline"]["invalidDiagnosticSample"]["diagnostics"][0].pop("column"),
        "acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].column",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: handoff_doc["boundaries"].update({"networkAccess": True}),
        "acceptedBaselineHandoff.boundaries.networkAccess",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: boundaries.update({"dockerMutation": True}),
        "boundaries.dockerMutation",
    )
    assert_finding_after_mutation(
        lambda handoff_doc, binding, boundaries: binding.update({"sha256": ""}),
        "acceptedBaselineHandoff.sha256",
    )

    print("PASS ADL v0.2 local beta release-candidate gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
