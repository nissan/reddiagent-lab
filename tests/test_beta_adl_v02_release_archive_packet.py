#!/usr/bin/env python3
"""Check ADL v0.2 local beta release archive packet evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-adl-v02-release-archive-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_archive_packet as archive  # noqa: E402


def run_archive(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_adl_v02_release_archive_packet.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    binding = archive.handoff_packet_binding()
    source_doc = archive.load_json(ROOT / archive.REQUIRED_HANDOFF_PACKET_PATH)
    boundaries = archive.archive_boundaries()
    mutator(source_doc, binding, boundaries)
    findings = archive.collect_findings(source_doc, binding, boundaries)
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_archive()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "adl-v02-local-beta-release-archive-packet"
    assert doc["issue"] == 355
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337, 339, 341, 343, 345, 347, 349, 351, 353]
    assert doc["status"] == "pass"
    assert doc["decision"] == "archive-ready"
    assert doc["releaseArchivePacketId"] == "reddiagent-beta-0-adl-v02-local-release-archive-packet"
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    handoff_packet = doc["releaseHandoffPacket"]
    assert handoff_packet["path"] == "tests/fixtures/beta-adl-v02-release-handoff-packet.json"
    assert handoff_packet["issue"] == 353
    assert handoff_packet["status"] == "pass"
    assert handoff_packet["decision"] == "handoff-ready"
    assert handoff_packet["sha256"] == doc["artifactHashes"]["tests/fixtures/beta-adl-v02-release-handoff-packet.json"]

    signoff_packet = doc["releaseSignoffPacket"]
    assert signoff_packet["issue"] == 351
    assert signoff_packet["status"] == "pass"
    assert signoff_packet["decision"] == "release-ready"

    accepted_handoff = doc["acceptedBaselineHandoff"]
    assert accepted_handoff["issue"] == 347
    assert accepted_handoff["status"] == "pass"
    assert accepted_handoff["decision"] == "continue"

    acceptance_smoke = doc["baselineAcceptanceSmoke"]
    assert acceptance_smoke["issue"] == 345
    assert acceptance_smoke["status"] == "pass"
    assert acceptance_smoke["decision"] == "accept"

    upstream = doc["upstreamPromotionPacket"]
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
    assert chain[351]["path"] == "tests/fixtures/beta-adl-v02-release-signoff-packet.json"
    assert chain[353]["path"] == "tests/fixtures/beta-adl-v02-release-handoff-packet.json"
    assert all(item["sha256"] and item["sizeBytes"] for item in chain.values())

    assert doc["artifactHashes"]["examples/v0.2/memory-observability-agent.yaml"] == "ae0659fae7e216b6f4e252bd7e5a88de3f08168c45234931a129effdba3a2499"
    assert doc["artifactHashes"]["examples/invalid/adl-v0.2-x402-missing-authority.yaml"] == "eb4387034bcd29b76ac561bd99bbf59986f7078ed6bd74b404419a85236deca8"
    assert doc["artifactHashes"]["tests/fixtures/beta-release-handoff.json"] == "83bb49d081367800ea24a7dbf2587550291099f8045f735dd67ff5e2588db8dd"
    assert doc["artifactHashes"]["tests/fixtures/beta-reviewer-walkthrough-smoke.json"] == "4245bb0e5eb0407883e7fee6ec1fe8600b27257284426d769321b820d833aee6"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-local-readiness-gate.json"] == "760b4ef16370e0c21c4fc03333276bd8d88dda78886c316397e9391289244ffe"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"] == "4925690506e7eb6f829f868c8314aee5a64af8220153cc6cf6142bcbf26fa513"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"] == "3f6abeaaa116d8ee88991659d0daf4e36c3a90348775101f075fad94328e4c4f"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"] == "27387879d49e990b018a7d449a4a68b6e987464c262c464b6941234390e33e73"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-release-candidate-gate.json"] == "d2da79826d73759ba3a859b1ba4018db407feb8b55b1b16bc5a59847c2ee118c"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-release-signoff-packet.json"] == "763ce8e993a2988a5e0918817573b5a0541a2ad0dff02c5bbfb3e04dd6ee9682"

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

    assert doc["archiveSummary"] == {
        "inputPacket": "tests/fixtures/beta-adl-v02-release-handoff-packet.json",
        "outputUse": "reviewer/operator handoff evidence for later local release archive packaging; no archive is published by this packet.",
        "readyForOfflineInspection": True,
        "requiredExamples": [
            "examples/v0.2/memory-observability-agent.yaml",
            "examples/invalid/adl-v0.2-x402-missing-authority.yaml",
        ],
        "stableDiagnosticFields": ["code", "severity", "category", "path", "line", "column"],
    }

    for key, expected in {
        "deterministicLocalReleaseArchivePacket": True,
        "consumesReleaseHandoffPacketOnly": True,
        "releaseArchiveDecisionOnly": True,
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

    assert run_archive("--requested-decision", "hold")["decision"] == "hold"
    assert run_archive("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert archive.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc.update({"decision": "hold"}),
        "releaseHandoffPacket.decision",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc.update({"status": "fail"}),
        "releaseHandoffPacket.status",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["releaseSignoffPacket"].update({"decision": "hold"}),
        "releaseHandoffPacket.releaseSignoffPacket.decision",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["acceptedBaselineHandoff"].update({"decision": "hold"}),
        "releaseHandoffPacket.acceptedBaselineHandoff.decision",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["baselineAcceptanceSmoke"].update({"decision": "hold"}),
        "releaseHandoffPacket.baselineAcceptanceSmoke.decision",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["upstreamPromotionPacket"].update({"decision": "hold"}),
        "releaseHandoffPacket.upstreamPromotionPacket.decision",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["evidenceChain"][7].update({"sha256": ""}),
        "releaseHandoffPacket.evidenceChain.351.sha256",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["artifactHashes"].update({"examples/v0.2/memory-observability-agent.yaml": ""}),
        "releaseHandoffPacket.artifactHashes.examples/v0.2/memory-observability-agent.yaml",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["adlV02RuntimeBaseline"]["validRuntimeExample"].update({"exitCode": 1}),
        "releaseHandoffPacket.adlV02RuntimeBaseline.validRuntimeExample.exitCode",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["adlV02RuntimeBaseline"]["invalidDiagnosticSample"]["diagnostics"][0].pop("column"),
        "releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].column",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: source_doc["boundaries"].update({"networkAccess": True}),
        "releaseHandoffPacket.boundaries.networkAccess",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: boundaries.update({"dockerMutation": True}),
        "boundaries.dockerMutation",
    )
    assert_finding_after_mutation(
        lambda source_doc, binding, boundaries: binding.update({"sha256": ""}),
        "releaseHandoffPacket.sha256",
    )

    print("PASS ADL v0.2 local beta release archive packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
