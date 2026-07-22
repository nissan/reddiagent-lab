#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta release handoff evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_signoff_packet as signoff_packet  # noqa: E402


REQUIRED_HANDOFF_ID = "reddiagent-beta-0-adl-v02-local-release-handoff-packet"
REQUIRED_SIGNOFF_PACKET_PATH = "tests/fixtures/beta-adl-v02-release-signoff-packet.json"
REQUIRED_SIGNOFF_PACKET_ID = signoff_packet.REQUIRED_SIGNOFF_ID
REQUIRED_VALID_ADL = signoff_packet.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = signoff_packet.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = signoff_packet.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343, 345, 347, 349, 351]
CURRENT_ISSUE = 353
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = signoff_packet.REQUIRED_BOUNDARY_FALSE + (
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


def signoff_packet_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_SIGNOFF_PACKET_PATH
    return {
        "key": "releaseSignoffPacket",
        "path": REQUIRED_SIGNOFF_PACKET_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": signoff_packet.rc_gate.handoff.acceptance.promotion.readiness.digest(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def evidence_chain_by_issue(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        item["issue"]: item
        for item in doc.get("evidenceChain", [])
        if isinstance(item, dict) and isinstance(item.get("issue"), int)
    }


def handoff_boundaries() -> dict[str, Any]:
    return {
        "deterministicLocalReleaseHandoffPacket": True,
        "consumesReleaseSignoffPacketOnly": True,
        "releaseHandoffDecisionOnly": True,
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


def expected_artifact_hashes(rc_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for path, digest in rc_doc.get("artifactHashes", {}).items():
        if isinstance(path, str):
            hashes[path] = digest
    return hashes


def collect_findings(
    rc_doc: dict[str, Any],
    binding: dict[str, Any],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "releaseSignoffPacket.exists", "Pinned #351 release-signoff packet fixture must exist.")
    require(bool(binding.get("sha256")), "releaseSignoffPacket.sha256", "Pinned #351 release-signoff packet fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "releaseSignoffPacket.sizeBytes", "Pinned #351 release-signoff packet fixture must have a byte size.")

    require(rc_doc.get("mode") == "adl-v02-local-beta-release-signoff-packet", "releaseSignoffPacket.mode", "Handoff packet must consume the #351 release-signoff packet.")
    require(rc_doc.get("issue") == 351, "releaseSignoffPacket.issue", "Release-signoff packet must be issue #351.")
    require(rc_doc.get("parentEpic") == PARENT_EPIC, "releaseSignoffPacket.parentEpic", "Release-signoff packet must belong to #220.")
    require(rc_doc.get("status") == "pass", "releaseSignoffPacket.status", "Handoff packet requires passing signoff evidence.")
    require(rc_doc.get("decision") == "release-ready", "releaseSignoffPacket.decision", "Handoff packet requires #351 decision=release-ready.")
    require(rc_doc.get("releaseSignoffPacketId") == REQUIRED_SIGNOFF_PACKET_ID, "releaseSignoffPacket.releaseSignoffPacketId", "signoff packet ID must stay stable.")
    require(rc_doc.get("follows") == [337, 339, 341, 343, 345, 347, 349], "releaseSignoffPacket.follows", "signoff packet must preserve the #337/#339/#341/#343/#345/#347/#349 chain.")

    accepted_handoff = rc_doc.get("acceptedBaselineHandoff", {})
    require(accepted_handoff.get("issue") == 347, "releaseSignoffPacket.acceptedBaselineHandoff.issue", "Accepted-baseline handoff must be issue #347.")
    require(accepted_handoff.get("status") == "pass", "releaseSignoffPacket.acceptedBaselineHandoff.status", "Accepted-baseline handoff must pass.")
    require(accepted_handoff.get("decision") == "continue", "releaseSignoffPacket.acceptedBaselineHandoff.decision", "Accepted-baseline handoff must decide continue.")
    require(bool(accepted_handoff.get("sha256")), "releaseSignoffPacket.acceptedBaselineHandoff.sha256", "Accepted-baseline handoff must be pinned by sha256.")
    require(bool(accepted_handoff.get("sizeBytes")), "releaseSignoffPacket.acceptedBaselineHandoff.sizeBytes", "Accepted-baseline handoff must have a byte size.")

    acceptance_smoke = rc_doc.get("baselineAcceptanceSmoke", {})
    require(acceptance_smoke.get("issue") == 345, "releaseSignoffPacket.baselineAcceptanceSmoke.issue", "Upstream acceptance smoke must be issue #345.")
    require(acceptance_smoke.get("status") == "pass", "releaseSignoffPacket.baselineAcceptanceSmoke.status", "Upstream acceptance smoke must pass.")
    require(acceptance_smoke.get("decision") == "accept", "releaseSignoffPacket.baselineAcceptanceSmoke.decision", "Upstream acceptance smoke must decide accept.")

    promotion_packet = rc_doc.get("upstreamPromotionPacket", {})
    require(promotion_packet.get("issue") == 343, "releaseSignoffPacket.upstreamPromotionPacket.issue", "Upstream promotion packet must be issue #343.")
    require(promotion_packet.get("status") == "pass", "releaseSignoffPacket.upstreamPromotionPacket.status", "Upstream promotion packet must pass.")
    require(promotion_packet.get("decision") == "promote", "releaseSignoffPacket.upstreamPromotionPacket.decision", "Upstream promotion packet must decide promote.")

    chain = evidence_chain_by_issue(rc_doc)
    for issue, path_text in {
        337: "tests/fixtures/beta-release-handoff.json",
        339: "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        341: "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        343: "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
        345: "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json",
        347: "tests/fixtures/beta-adl-v02-accepted-baseline-handoff-packet.json",
    }.items():
        item = chain.get(issue, {})
        require(item.get("path") == path_text, f"releaseSignoffPacket.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"releaseSignoffPacket.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"releaseSignoffPacket.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"releaseSignoffPacket.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

    artifact_hashes = rc_doc.get("artifactHashes", {})
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
    ):
        require(bool(artifact_hashes.get(path_text)), f"releaseSignoffPacket.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = rc_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "releaseSignoffPacket.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "releaseSignoffPacket.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "releaseSignoffPacket.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "releaseSignoffPacket.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "releaseSignoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "releaseSignoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "releaseSignoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "releaseSignoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"releaseSignoffPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = rc_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalReleaseSignoffPacket") is True, "releaseSignoffPacket.boundaries.deterministicLocalReleaseSignoffPacket", "Source signoff packet must remain deterministic.")
    require(source_boundaries.get("consumesReleaseCandidateGateOnly") is True, "releaseSignoffPacket.boundaries.consumesReleaseCandidateGateOnly", "Source signoff packet must consume #349 only.")
    require(source_boundaries.get("releaseSignoffDecisionOnly") is True, "releaseSignoffPacket.boundaries.releaseSignoffDecisionOnly", "Source signoff packet must remain decision-only evidence.")
    for key in signoff_packet.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"releaseSignoffPacket.boundaries.{key}", f"Source signoff packet boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalReleaseHandoffPacket") is True, "boundaries.deterministicLocalReleaseHandoffPacket", "Handoff packet must be deterministic local evidence.")
    require(boundaries.get("consumesReleaseSignoffPacketOnly") is True, "boundaries.consumesReleaseSignoffPacketOnly", "Handoff packet must consume #351 without replaying historical evidence.")
    require(boundaries.get("releaseHandoffDecisionOnly") is True, "boundaries.releaseHandoffDecisionOnly", "Handoff packet must emit only release handoff decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Handoff packet boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "handoff-ready"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = signoff_packet_binding()
    rc_doc = load_json(ROOT / REQUIRED_SIGNOFF_PACKET_PATH) if binding["exists"] else {}
    boundaries = handoff_boundaries()
    findings = collect_findings(rc_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-release-handoff-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "releaseHandoffPacketId": REQUIRED_HANDOFF_ID,
        "releaseId": rc_doc.get("releaseId", signoff_packet.rc_gate.handoff.acceptance.promotion.readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-release-handoff-packet",
        "findings": findings,
        "decisionCriteria": {
            "handoff-ready": [
                "#351 release-signoff packet fixture is present, passing, pinned by sha256, and decision=release-ready.",
                "#347 accepted-baseline handoff remains status=pass and decision=continue.",
                "Upstream #345 acceptance smoke remains status=pass and decision=accept.",
                "Upstream #343 baseline promotion packet remains status=pass and decision=promote.",
                "#337/#339/#341/#343/#345/#347/#349/#351 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required RC, handoff, acceptance, promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-release-ready, non-continue, non-accept, non-promote, or failing.",
                "Do not treat the ADL v0.2 local beta release signoff as handoff-ready until a replacement handoff packet returns status=pass and decision=handoff-ready.",
            ],
            "rollback-required": [
                "Use only if this local beta release signoff was already treated as handoff-ready and a later handoff gate fails.",
                "Rollback target is the last RC-ready local beta release-signoff packet; this packet does not execute rollback.",
            ],
        },
        "operatorActions": {
            "handoff-ready": "Treat the pinned ADL v0.2 local beta release signoff as the current deterministic handoff-ready input for the next beta release handoff step.",
            "hold": "Keep the release signoff out of release handoff flow and resolve listed findings before continuing.",
            "rollback-required": "Revert handoff-ready selection to the last release-ready local beta signoff; this packet does not execute rollback.",
        },
        "releaseSignoffPacket": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": rc_doc.get("mode"),
            "issue": rc_doc.get("issue"),
            "status": rc_doc.get("status"),
            "decision": rc_doc.get("decision"),
            "releaseSignoffPacketId": rc_doc.get("releaseSignoffPacketId"),
        },
        "acceptedBaselineHandoff": rc_doc.get("acceptedBaselineHandoff", {}),
        "baselineAcceptanceSmoke": rc_doc.get("baselineAcceptanceSmoke", {}),
        "upstreamPromotionPacket": rc_doc.get("upstreamPromotionPacket", {}),
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **evidence_chain_by_issue(rc_doc).get(337, {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **evidence_chain_by_issue(rc_doc).get(339, {})},
            {"issue": 341, "name": "readinessGate", **evidence_chain_by_issue(rc_doc).get(341, {})},
            {"issue": 343, "name": "baselinePromotionPacket", **evidence_chain_by_issue(rc_doc).get(343, {})},
            {"issue": 345, "name": "baselineAcceptanceSmoke", **evidence_chain_by_issue(rc_doc).get(345, {})},
            {"issue": 347, "name": "acceptedBaselineHandoffPacket", **evidence_chain_by_issue(rc_doc).get(347, {})},
            {"issue": 349, "name": "releaseCandidateGate", **evidence_chain_by_issue(rc_doc).get(349, {})},
            {"issue": 351, "name": "releaseSignoffPacket", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(rc_doc, binding),
        "adlV02RuntimeBaseline": rc_doc.get("adlV02RuntimeBaseline", {}),
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
        "mainnetStatement": "This release handoff packet is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated release handoff packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("handoff-ready", "hold", "rollback-required"),
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
