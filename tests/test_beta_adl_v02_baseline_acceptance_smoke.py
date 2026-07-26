#!/usr/bin/env python3
"""Check ADL v0.2 local beta baseline acceptance smoke evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-adl-v02-baseline-acceptance-smoke.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_baseline_acceptance_smoke as smoke  # noqa: E402


def run_smoke(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_adl_v02_baseline_acceptance_smoke.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    binding = smoke.promotion_binding()
    promotion_doc = smoke.load_json(ROOT / smoke.REQUIRED_PROMOTION_PATH)
    boundaries = smoke.acceptance_boundaries()
    mutator(promotion_doc, binding, boundaries)
    findings = smoke.collect_findings(promotion_doc, binding, boundaries)
    assert expected_path in {finding["path"] for finding in findings}


def main() -> int:
    doc = run_smoke()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "adl-v02-local-beta-baseline-acceptance-smoke"
    assert doc["issue"] == 345
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337, 339, 341, 343]
    assert doc["status"] == "pass"
    assert doc["decision"] == "accept"
    assert doc["acceptanceSmokeId"] == "reddiagent-beta-0-adl-v02-local-baseline-acceptance-smoke"
    assert doc["baselinePromotionPacket"]["path"] == "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"
    assert doc["baselinePromotionPacket"]["issue"] == 343
    assert doc["baselinePromotionPacket"]["status"] == "pass"
    assert doc["baselinePromotionPacket"]["decision"] == "promote"
    assert doc["baselinePromotionPacket"]["sha256"] == doc["artifactHashes"]["tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"]
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    chain = {item["issue"]: item for item in doc["evidenceChain"]}
    assert chain[337]["path"] == "tests/fixtures/beta-release-handoff.json"
    assert chain[339]["path"] == "tests/fixtures/beta-reviewer-walkthrough-smoke.json"
    assert chain[341]["path"] == "tests/fixtures/beta-adl-v02-local-readiness-gate.json"
    assert chain[343]["path"] == "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"
    assert all(item["sha256"] and item["sizeBytes"] for item in chain.values())

    assert doc["artifactHashes"]["examples/v0.2/memory-observability-agent.yaml"] == "ae0659fae7e216b6f4e252bd7e5a88de3f08168c45234931a129effdba3a2499"
    assert doc["artifactHashes"]["examples/invalid/adl-v0.2-x402-missing-authority.yaml"] == "eb4387034bcd29b76ac561bd99bbf59986f7078ed6bd74b404419a85236deca8"
    assert doc["artifactHashes"]["tests/fixtures/beta-release-handoff.json"] == "83bb49d081367800ea24a7dbf2587550291099f8045f735dd67ff5e2588db8dd"
    assert doc["artifactHashes"]["tests/fixtures/beta-reviewer-walkthrough-smoke.json"] == "4245bb0e5eb0407883e7fee6ec1fe8600b27257284426d769321b820d833aee6"
    assert doc["artifactHashes"]["tests/fixtures/beta-adl-v02-local-readiness-gate.json"] == "760b4ef16370e0c21c4fc03333276bd8d88dda78886c316397e9391289244ffe"

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
        "deterministicLocalSmoke": True,
        "consumesPromotionPacketOnly": True,
        "acceptHoldRollbackDecisionOnly": True,
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

    assert run_smoke("--requested-decision", "hold")["decision"] == "hold"
    assert run_smoke("--requested-decision", "rollback-required")["decision"] == "rollback-required"
    assert smoke.decision_for([{"path": "x", "reason": "y"}]) == "hold"

    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc.update({"decision": "hold"}),
        "baselinePromotionPacket.decision",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc.update({"status": "fail"}),
        "baselinePromotionPacket.status",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc["evidenceChain"][0].update({"sha256": ""}),
        "baselinePromotionPacket.evidenceChain.337.sha256",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc["artifactHashes"].update({"examples/v0.2/memory-observability-agent.yaml": ""}),
        "baselinePromotionPacket.artifactHashes.examples/v0.2/memory-observability-agent.yaml",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc["adlV02RuntimeBaseline"]["validRuntimeExample"].update({"exitCode": 1}),
        "baselinePromotionPacket.adlV02RuntimeBaseline.validRuntimeExample.exitCode",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc["adlV02RuntimeBaseline"]["invalidDiagnosticSample"]["diagnostics"][0].pop("column"),
        "baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].column",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: promotion_doc["boundaries"].update({"networkAccess": True}),
        "baselinePromotionPacket.boundaries.networkAccess",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: boundaries.update({"dockerMutation": True}),
        "boundaries.dockerMutation",
    )
    assert_finding_after_mutation(
        lambda promotion_doc, binding, boundaries: binding.update({"sha256": ""}),
        "baselinePromotionPacket.sha256",
    )

    print("PASS ADL v0.2 local beta baseline acceptance smoke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
