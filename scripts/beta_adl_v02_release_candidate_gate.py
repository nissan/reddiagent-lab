#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta release-candidate gate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_accepted_baseline_handoff_packet as handoff  # noqa: E402


REQUIRED_RC_GATE_ID = "reddiagent-beta-0-adl-v02-local-release-candidate-gate"
REQUIRED_HANDOFF_PATH = "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json"
REQUIRED_HANDOFF_ID = handoff.REQUIRED_HANDOFF_ID
REQUIRED_VALID_ADL = handoff.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = handoff.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = handoff.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343, 345, 347]
CURRENT_ISSUE = 349
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = handoff.REQUIRED_BOUNDARY_FALSE + (
    "hostedDeployment",
    "dockerMutation",
    "surfpoolMutation",
    "coolifyMutation",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def handoff_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_HANDOFF_PATH
    return {
        "key": "acceptedBaselineHandoffPacket",
        "path": REQUIRED_HANDOFF_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": handoff.acceptance.promotion.readiness.digest(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def evidence_chain_by_issue(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        item["issue"]: item
        for item in doc.get("evidenceChain", [])
        if isinstance(item, dict) and isinstance(item.get("issue"), int)
    }


def rc_boundaries() -> dict[str, Any]:
    return {
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
    }


def expected_artifact_hashes(handoff_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for path, digest in handoff_doc.get("artifactHashes", {}).items():
        if isinstance(path, str):
            hashes[path] = digest
    return hashes


def collect_findings(
    handoff_doc: dict[str, Any],
    binding: dict[str, Any],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "acceptedBaselineHandoff.exists", "Pinned #347 handoff packet fixture must exist.")
    require(bool(binding.get("sha256")), "acceptedBaselineHandoff.sha256", "Pinned #347 handoff packet fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "acceptedBaselineHandoff.sizeBytes", "Pinned #347 handoff packet fixture must have a byte size.")

    require(handoff_doc.get("mode") == "adl-v02-local-beta-accepted-baseline-handoff-packet", "acceptedBaselineHandoff.mode", "RC gate must consume the #347 accepted-baseline handoff packet.")
    require(handoff_doc.get("issue") == 347, "acceptedBaselineHandoff.issue", "Accepted-baseline handoff must be issue #347.")
    require(handoff_doc.get("parentEpic") == PARENT_EPIC, "acceptedBaselineHandoff.parentEpic", "Accepted-baseline handoff must belong to #220.")
    require(handoff_doc.get("status") == "pass", "acceptedBaselineHandoff.status", "RC gate requires passing accepted-baseline handoff evidence.")
    require(handoff_doc.get("decision") == "continue", "acceptedBaselineHandoff.decision", "RC gate requires #347 decision=continue.")
    require(handoff_doc.get("handoffPacketId") == REQUIRED_HANDOFF_ID, "acceptedBaselineHandoff.handoffPacketId", "Accepted-baseline handoff ID must stay stable.")
    require(handoff_doc.get("follows") == [337, 339, 341, 343, 345], "acceptedBaselineHandoff.follows", "Accepted-baseline handoff must preserve the #337/#339/#341/#343/#345 chain.")

    acceptance_smoke = handoff_doc.get("baselineAcceptanceSmoke", {})
    require(acceptance_smoke.get("issue") == 345, "acceptedBaselineHandoff.baselineAcceptanceSmoke.issue", "Upstream acceptance smoke must be issue #345.")
    require(acceptance_smoke.get("status") == "pass", "acceptedBaselineHandoff.baselineAcceptanceSmoke.status", "Upstream acceptance smoke must pass.")
    require(acceptance_smoke.get("decision") == "accept", "acceptedBaselineHandoff.baselineAcceptanceSmoke.decision", "Upstream acceptance smoke must decide accept.")
    require(bool(acceptance_smoke.get("sha256")), "acceptedBaselineHandoff.baselineAcceptanceSmoke.sha256", "Upstream acceptance smoke must be pinned by sha256.")
    require(bool(acceptance_smoke.get("sizeBytes")), "acceptedBaselineHandoff.baselineAcceptanceSmoke.sizeBytes", "Upstream acceptance smoke must have a byte size.")

    promotion_packet = handoff_doc.get("upstreamPromotionPacket", {})
    require(promotion_packet.get("issue") == 343, "acceptedBaselineHandoff.upstreamPromotionPacket.issue", "Upstream promotion packet must be issue #343.")
    require(promotion_packet.get("status") == "pass", "acceptedBaselineHandoff.upstreamPromotionPacket.status", "Upstream promotion packet must pass.")
    require(promotion_packet.get("decision") == "promote", "acceptedBaselineHandoff.upstreamPromotionPacket.decision", "Upstream promotion packet must decide promote.")

    chain = evidence_chain_by_issue(handoff_doc)
    for issue, path_text in {
        337: "tests/fixtures/beta-release-handoff.json",
        339: "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        341: "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        343: "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
        345: "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json",
    }.items():
        item = chain.get(issue, {})
        require(item.get("path") == path_text, f"acceptedBaselineHandoff.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"acceptedBaselineHandoff.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"acceptedBaselineHandoff.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"acceptedBaselineHandoff.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

    artifact_hashes = handoff_doc.get("artifactHashes", {})
    for path_text in (
        REQUIRED_VALID_ADL,
        REQUIRED_INVALID_ADL,
        "tests/fixtures/beta-release-handoff.json",
        "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
        "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json",
    ):
        require(bool(artifact_hashes.get(path_text)), f"acceptedBaselineHandoff.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = handoff_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "acceptedBaselineHandoff.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "acceptedBaselineHandoff.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "acceptedBaselineHandoff.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "acceptedBaselineHandoff.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"acceptedBaselineHandoff.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = handoff_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalHandoff") is True, "acceptedBaselineHandoff.boundaries.deterministicLocalHandoff", "Source handoff packet must remain deterministic.")
    require(source_boundaries.get("consumesAcceptanceSmokeOnly") is True, "acceptedBaselineHandoff.boundaries.consumesAcceptanceSmokeOnly", "Source handoff packet must consume #345 only.")
    require(source_boundaries.get("acceptedBaselineInspectionOnly") is True, "acceptedBaselineHandoff.boundaries.acceptedBaselineInspectionOnly", "Source handoff packet must remain offline inspection evidence.")
    for key in handoff.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"acceptedBaselineHandoff.boundaries.{key}", f"Source handoff boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalReleaseCandidateGate") is True, "boundaries.deterministicLocalReleaseCandidateGate", "RC gate must be deterministic local evidence.")
    require(boundaries.get("consumesAcceptedBaselineHandoffOnly") is True, "boundaries.consumesAcceptedBaselineHandoffOnly", "RC gate must consume #347 without replaying historical evidence.")
    require(boundaries.get("releaseCandidateDecisionOnly") is True, "boundaries.releaseCandidateDecisionOnly", "RC gate must emit only release-candidate decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"RC gate boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "rc-ready"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = handoff_binding()
    handoff_doc = load_json(ROOT / REQUIRED_HANDOFF_PATH) if binding["exists"] else {}
    boundaries = rc_boundaries()
    findings = collect_findings(handoff_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-release-candidate-gate",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "releaseCandidateGateId": REQUIRED_RC_GATE_ID,
        "releaseId": handoff_doc.get("releaseId", handoff.acceptance.promotion.readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-release-candidate-gate",
        "findings": findings,
        "decisionCriteria": {
            "rc-ready": [
                "#347 accepted-baseline handoff fixture is present, passing, pinned by sha256, and decision=continue.",
                "Upstream #345 acceptance smoke remains status=pass and decision=accept.",
                "Upstream #343 baseline promotion packet remains status=pass and decision=promote.",
                "#337/#339/#341/#343/#345/#347 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required handoff, acceptance, promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-continue, non-accept, non-promote, or failing.",
                "Do not treat the accepted ADL v0.2 local beta baseline as an RC candidate until a replacement gate returns status=pass and decision=rc-ready.",
            ],
            "rollback-required": [
                "Use only if this accepted local beta baseline was already promoted to an RC candidate and a later RC gate fails.",
                "Rollback target is the last accepted local beta handoff packet; this gate does not execute rollback.",
            ],
        },
        "operatorActions": {
            "rc-ready": "Treat the pinned ADL v0.2 local beta accepted baseline as the current local release-candidate input for the next beta release step.",
            "hold": "Keep the accepted baseline out of RC flow and resolve listed findings before continuing.",
            "rollback-required": "Revert RC candidate selection to the last accepted local beta handoff packet; this gate does not execute rollback.",
        },
        "acceptedBaselineHandoff": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": handoff_doc.get("mode"),
            "issue": handoff_doc.get("issue"),
            "status": handoff_doc.get("status"),
            "decision": handoff_doc.get("decision"),
            "handoffPacketId": handoff_doc.get("handoffPacketId"),
        },
        "baselineAcceptanceSmoke": handoff_doc.get("baselineAcceptanceSmoke", {}),
        "upstreamPromotionPacket": handoff_doc.get("upstreamPromotionPacket", {}),
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **evidence_chain_by_issue(handoff_doc).get(337, {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **evidence_chain_by_issue(handoff_doc).get(339, {})},
            {"issue": 341, "name": "readinessGate", **evidence_chain_by_issue(handoff_doc).get(341, {})},
            {"issue": 343, "name": "baselinePromotionPacket", **evidence_chain_by_issue(handoff_doc).get(343, {})},
            {"issue": 345, "name": "baselineAcceptanceSmoke", **evidence_chain_by_issue(handoff_doc).get(345, {})},
            {"issue": 347, "name": "acceptedBaselineHandoffPacket", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(handoff_doc, binding),
        "adlV02RuntimeBaseline": handoff_doc.get("adlV02RuntimeBaseline", {}),
        "excludedActions": [
            "full historical beta chain replay",
            "live runtime activation",
            "hosted deployment",
            "Docker, Surfpool, or Coolify mutation",
            "credential lookup or storage",
            "provider/model/API product call",
            "live MCP invocation",
            "wallet/payment/facilitator/settlement action",
            "devnet or mainnet run",
            "package or archive publishing",
            "production gateway mutation",
        ],
        "boundaries": boundaries,
        "mainnetStatement": "This release-candidate gate is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated release-candidate gate JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("rc-ready", "hold", "rollback-required"),
        help="Optional operator-requested decision override for hold/rollback gate dry-runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(requested_decision=args.requested_decision)
    rendered = dump_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
