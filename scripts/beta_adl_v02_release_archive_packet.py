#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta release archive evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_handoff_packet as handoff_packet  # noqa: E402


REQUIRED_ARCHIVE_ID = "reddiagent-beta-0-adl-v02-local-release-archive-packet"
REQUIRED_HANDOFF_PACKET_PATH = "tests/fixtures/beta-adl-v02-release-handoff-packet.json"
REQUIRED_HANDOFF_PACKET_ID = handoff_packet.REQUIRED_HANDOFF_ID
REQUIRED_VALID_ADL = handoff_packet.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = handoff_packet.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = handoff_packet.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343, 345, 347, 349, 351, 353]
CURRENT_ISSUE = 355
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = handoff_packet.REQUIRED_BOUNDARY_FALSE


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


def handoff_packet_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_HANDOFF_PACKET_PATH
    return {
        "key": "releaseHandoffPacket",
        "path": REQUIRED_HANDOFF_PACKET_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": handoff_packet.signoff_packet.rc_gate.handoff.acceptance.promotion.readiness.digest(path)
        if path.exists() and path.is_file()
        else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def evidence_chain_by_issue(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        item["issue"]: item
        for item in doc.get("evidenceChain", [])
        if isinstance(item, dict) and isinstance(item.get("issue"), int)
    }


def archive_boundaries() -> dict[str, Any]:
    return {
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
    }


def expected_artifact_hashes(source_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for path, digest in source_doc.get("artifactHashes", {}).items():
        if isinstance(path, str):
            hashes[path] = digest
    return hashes


def collect_findings(
    source_doc: dict[str, Any],
    binding: dict[str, Any],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "releaseHandoffPacket.exists", "Pinned #353 release handoff packet fixture must exist.")
    require(bool(binding.get("sha256")), "releaseHandoffPacket.sha256", "Pinned #353 release handoff packet fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "releaseHandoffPacket.sizeBytes", "Pinned #353 release handoff packet fixture must have a byte size.")

    require(source_doc.get("mode") == "adl-v02-local-beta-release-handoff-packet", "releaseHandoffPacket.mode", "Archive packet must consume the #353 release handoff packet.")
    require(source_doc.get("issue") == 353, "releaseHandoffPacket.issue", "Release handoff packet must be issue #353.")
    require(source_doc.get("parentEpic") == PARENT_EPIC, "releaseHandoffPacket.parentEpic", "Release handoff packet must belong to #220.")
    require(source_doc.get("status") == "pass", "releaseHandoffPacket.status", "Archive packet requires passing handoff evidence.")
    require(source_doc.get("decision") == "handoff-ready", "releaseHandoffPacket.decision", "Archive packet requires #353 decision=handoff-ready.")
    require(source_doc.get("releaseHandoffPacketId") == REQUIRED_HANDOFF_PACKET_ID, "releaseHandoffPacket.releaseHandoffPacketId", "handoff packet ID must stay stable.")
    require(source_doc.get("follows") == [337, 339, 341, 343, 345, 347, 349, 351], "releaseHandoffPacket.follows", "handoff packet must preserve the #337/#339/#341/#343/#345/#347/#349/#351 chain.")

    signoff = source_doc.get("releaseSignoffPacket", {})
    require(signoff.get("issue") == 351, "releaseHandoffPacket.releaseSignoffPacket.issue", "Release signoff packet must be issue #351.")
    require(signoff.get("status") == "pass", "releaseHandoffPacket.releaseSignoffPacket.status", "Release signoff packet must pass.")
    require(signoff.get("decision") == "release-ready", "releaseHandoffPacket.releaseSignoffPacket.decision", "Release signoff packet must decide release-ready.")
    require(bool(signoff.get("sha256")), "releaseHandoffPacket.releaseSignoffPacket.sha256", "Release signoff packet must be pinned by sha256.")
    require(bool(signoff.get("sizeBytes")), "releaseHandoffPacket.releaseSignoffPacket.sizeBytes", "Release signoff packet must have a byte size.")

    accepted_handoff = source_doc.get("acceptedBaselineHandoff", {})
    require(accepted_handoff.get("issue") == 347, "releaseHandoffPacket.acceptedBaselineHandoff.issue", "Accepted-baseline handoff must be issue #347.")
    require(accepted_handoff.get("status") == "pass", "releaseHandoffPacket.acceptedBaselineHandoff.status", "Accepted-baseline handoff must pass.")
    require(accepted_handoff.get("decision") == "continue", "releaseHandoffPacket.acceptedBaselineHandoff.decision", "Accepted-baseline handoff must decide continue.")

    acceptance_smoke = source_doc.get("baselineAcceptanceSmoke", {})
    require(acceptance_smoke.get("issue") == 345, "releaseHandoffPacket.baselineAcceptanceSmoke.issue", "Upstream acceptance smoke must be issue #345.")
    require(acceptance_smoke.get("status") == "pass", "releaseHandoffPacket.baselineAcceptanceSmoke.status", "Upstream acceptance smoke must pass.")
    require(acceptance_smoke.get("decision") == "accept", "releaseHandoffPacket.baselineAcceptanceSmoke.decision", "Upstream acceptance smoke must decide accept.")

    promotion_packet = source_doc.get("upstreamPromotionPacket", {})
    require(promotion_packet.get("issue") == 343, "releaseHandoffPacket.upstreamPromotionPacket.issue", "Upstream promotion packet must be issue #343.")
    require(promotion_packet.get("status") == "pass", "releaseHandoffPacket.upstreamPromotionPacket.status", "Upstream promotion packet must pass.")
    require(promotion_packet.get("decision") == "promote", "releaseHandoffPacket.upstreamPromotionPacket.decision", "Upstream promotion packet must decide promote.")

    chain = evidence_chain_by_issue(source_doc)
    for issue, path_text in {
        337: "tests/fixtures/beta-release-handoff.json",
        339: "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        341: "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        343: "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
        345: "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json",
        347: "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json",
        349: "tests/fixtures/beta-adl-v02-release-candidate-gate.json",
        351: "tests/fixtures/beta-adl-v02-release-signoff-packet.json",
    }.items():
        item = chain.get(issue, {})
        require(item.get("path") == path_text, f"releaseHandoffPacket.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"releaseHandoffPacket.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"releaseHandoffPacket.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"releaseHandoffPacket.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

    artifact_hashes = source_doc.get("artifactHashes", {})
    for path_text in (
        REQUIRED_VALID_ADL,
        REQUIRED_INVALID_ADL,
        "tests/fixtures/beta-release-handoff.json",
        "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
        "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json",
        "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json",
        "tests/fixtures/beta-adl-v02-release-candidate-gate.json",
        "tests/fixtures/beta-adl-v02-release-signoff-packet.json",
    ):
        require(bool(artifact_hashes.get(path_text)), f"releaseHandoffPacket.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = source_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "releaseHandoffPacket.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "releaseHandoffPacket.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "releaseHandoffPacket.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "releaseHandoffPacket.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"releaseHandoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = source_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalReleaseHandoffPacket") is True, "releaseHandoffPacket.boundaries.deterministicLocalReleaseHandoffPacket", "Source handoff packet must remain deterministic.")
    require(source_boundaries.get("consumesReleaseSignoffPacketOnly") is True, "releaseHandoffPacket.boundaries.consumesReleaseSignoffPacketOnly", "Source handoff packet must consume #351 only.")
    require(source_boundaries.get("releaseHandoffDecisionOnly") is True, "releaseHandoffPacket.boundaries.releaseHandoffDecisionOnly", "Source handoff packet must remain decision-only evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"releaseHandoffPacket.boundaries.{key}", f"Source handoff packet boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalReleaseArchivePacket") is True, "boundaries.deterministicLocalReleaseArchivePacket", "Archive packet must be deterministic local evidence.")
    require(boundaries.get("consumesReleaseHandoffPacketOnly") is True, "boundaries.consumesReleaseHandoffPacketOnly", "Archive packet must consume #353 without replaying historical evidence.")
    require(boundaries.get("releaseArchiveDecisionOnly") is True, "boundaries.releaseArchiveDecisionOnly", "Archive packet must emit only release archive decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Archive packet boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "archive-ready"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = handoff_packet_binding()
    source_doc = load_json(ROOT / REQUIRED_HANDOFF_PACKET_PATH) if binding["exists"] else {}
    boundaries = archive_boundaries()
    findings = collect_findings(source_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-release-archive-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "releaseArchivePacketId": REQUIRED_ARCHIVE_ID,
        "releaseId": source_doc.get(
            "releaseId",
            handoff_packet.signoff_packet.rc_gate.handoff.acceptance.promotion.readiness.REQUIRED_RELEASE_ID,
        ),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-release-archive-packet",
        "findings": findings,
        "decisionCriteria": {
            "archive-ready": [
                "#353 release handoff packet fixture is present, passing, pinned by sha256, and decision=handoff-ready.",
                "#351 release signoff packet remains status=pass and decision=release-ready.",
                "#347 accepted-baseline handoff remains status=pass and decision=continue.",
                "Upstream #345 acceptance smoke remains status=pass and decision=accept.",
                "Upstream #343 baseline promotion packet remains status=pass and decision=promote.",
                "#337/#339/#341/#343/#345/#347/#349/#351/#353 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required handoff, signoff, RC, acceptance, promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-handoff-ready, non-release-ready, non-continue, non-accept, non-promote, or failing.",
                "Do not treat the ADL v0.2 local beta release as archive-ready until a replacement archive packet returns status=pass and decision=archive-ready.",
            ],
            "rollback-required": [
                "Use only if this local beta release was already treated as archive-ready and a later archive or release-packaging gate fails.",
                "Rollback target is the last handoff-ready local beta release handoff packet; this packet does not execute rollback.",
            ],
        },
        "operatorActions": {
            "archive-ready": "Treat the pinned ADL v0.2 local beta release handoff as the current deterministic archive-ready input for offline reviewer handoff or later release/archive packaging.",
            "hold": "Keep the release out of archive packaging flow and resolve listed findings before continuing.",
            "rollback-required": "Revert archive-ready selection to the last handoff-ready local beta release handoff; this packet does not execute rollback.",
        },
        "releaseHandoffPacket": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": source_doc.get("mode"),
            "issue": source_doc.get("issue"),
            "status": source_doc.get("status"),
            "decision": source_doc.get("decision"),
            "releaseHandoffPacketId": source_doc.get("releaseHandoffPacketId"),
        },
        "releaseSignoffPacket": source_doc.get("releaseSignoffPacket", {}),
        "acceptedBaselineHandoff": source_doc.get("acceptedBaselineHandoff", {}),
        "baselineAcceptanceSmoke": source_doc.get("baselineAcceptanceSmoke", {}),
        "upstreamPromotionPacket": source_doc.get("upstreamPromotionPacket", {}),
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **evidence_chain_by_issue(source_doc).get(337, {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **evidence_chain_by_issue(source_doc).get(339, {})},
            {"issue": 341, "name": "readinessGate", **evidence_chain_by_issue(source_doc).get(341, {})},
            {"issue": 343, "name": "baselinePromotionPacket", **evidence_chain_by_issue(source_doc).get(343, {})},
            {"issue": 345, "name": "baselineAcceptanceSmoke", **evidence_chain_by_issue(source_doc).get(345, {})},
            {"issue": 347, "name": "acceptedBaselineHandoffPacket", **evidence_chain_by_issue(source_doc).get(347, {})},
            {"issue": 349, "name": "releaseCandidateGate", **evidence_chain_by_issue(source_doc).get(349, {})},
            {"issue": 351, "name": "releaseSignoffPacket", **evidence_chain_by_issue(source_doc).get(351, {})},
            {"issue": 353, "name": "releaseHandoffPacket", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(source_doc, binding),
        "adlV02RuntimeBaseline": source_doc.get("adlV02RuntimeBaseline", {}),
        "archiveSummary": {
            "readyForOfflineInspection": decision == "archive-ready" and not findings,
            "inputPacket": REQUIRED_HANDOFF_PACKET_PATH,
            "outputUse": "reviewer/operator handoff evidence for later local release archive packaging; no archive is published by this packet.",
            "requiredExamples": [REQUIRED_VALID_ADL, REQUIRED_INVALID_ADL],
            "stableDiagnosticFields": list(STABLE_DIAGNOSTIC_FIELDS),
        },
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
        "mainnetStatement": "This release archive packet is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated release archive packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("archive-ready", "hold", "rollback-required"),
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
