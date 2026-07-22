#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta baseline acceptance smoke evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_baseline_promotion_packet as promotion  # noqa: E402


REQUIRED_ACCEPTANCE_ID = "reddiagent-beta-0-adl-v02-local-baseline-acceptance-smoke"
REQUIRED_PROMOTION_PATH = "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json"
REQUIRED_PROMOTION_ID = promotion.REQUIRED_PACKET_ID
REQUIRED_VALID_ADL = promotion.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = promotion.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = promotion.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343]
CURRENT_ISSUE = 345
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = promotion.REQUIRED_BOUNDARY_FALSE + (
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


def promotion_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_PROMOTION_PATH
    return {
        "key": "baselinePromotionPacket",
        "path": REQUIRED_PROMOTION_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": promotion.readiness.digest(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def evidence_chain_by_issue(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        item["issue"]: item
        for item in doc.get("evidenceChain", [])
        if isinstance(item, dict) and isinstance(item.get("issue"), int)
    }


def acceptance_boundaries() -> dict[str, Any]:
    return {
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
    }


def expected_artifact_hashes(promotion_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for path, digest in promotion_doc.get("artifactHashes", {}).items():
        if isinstance(path, str):
            hashes[path] = digest
    return hashes


def collect_findings(
    promotion_doc: dict[str, Any],
    binding: dict[str, Any],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "baselinePromotionPacket.exists", "Pinned #343 promotion packet fixture must exist.")
    require(bool(binding.get("sha256")), "baselinePromotionPacket.sha256", "Pinned #343 promotion packet fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "baselinePromotionPacket.sizeBytes", "Pinned #343 promotion packet fixture must have a byte size.")

    require(promotion_doc.get("mode") == "adl-v02-local-beta-baseline-promotion-packet", "baselinePromotionPacket.mode", "Acceptance smoke must consume the #343 promotion packet.")
    require(promotion_doc.get("issue") == 343, "baselinePromotionPacket.issue", "Promotion packet must be issue #343.")
    require(promotion_doc.get("parentEpic") == PARENT_EPIC, "baselinePromotionPacket.parentEpic", "Promotion packet must belong to #220.")
    require(promotion_doc.get("status") == "pass", "baselinePromotionPacket.status", "Acceptance smoke requires a passing promotion packet.")
    require(promotion_doc.get("decision") == "promote", "baselinePromotionPacket.decision", "Acceptance smoke requires #343 packet decision=promote.")
    require(promotion_doc.get("promotionPacketId") == REQUIRED_PROMOTION_ID, "baselinePromotionPacket.promotionPacketId", "Promotion packet ID must stay stable.")
    require(promotion_doc.get("follows") == [337, 339, 341], "baselinePromotionPacket.follows", "Promotion packet must preserve the #337/#339/#341 chain.")

    chain = evidence_chain_by_issue(promotion_doc)
    for issue, path_text in {
        337: "tests/fixtures/beta-release-handoff.json",
        339: "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        341: "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
    }.items():
        item = chain.get(issue, {})
        require(item.get("path") == path_text, f"baselinePromotionPacket.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"baselinePromotionPacket.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"baselinePromotionPacket.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"baselinePromotionPacket.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

    artifact_hashes = promotion_doc.get("artifactHashes", {})
    for path_text in (
        REQUIRED_VALID_ADL,
        REQUIRED_INVALID_ADL,
        "tests/fixtures/beta-release-handoff.json",
        "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
    ):
        require(bool(artifact_hashes.get(path_text)), f"baselinePromotionPacket.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = promotion_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "baselinePromotionPacket.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "baselinePromotionPacket.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "baselinePromotionPacket.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "baselinePromotionPacket.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"baselinePromotionPacket.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = promotion_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalPacket") is True, "baselinePromotionPacket.boundaries.deterministicLocalPacket", "Source promotion packet must remain deterministic.")
    require(source_boundaries.get("consumesReadinessGateOnly") is True, "baselinePromotionPacket.boundaries.consumesReadinessGateOnly", "Source promotion packet must consume #341 only.")
    require(source_boundaries.get("promoteHoldRollbackDecisionOnly") is True, "baselinePromotionPacket.boundaries.promoteHoldRollbackDecisionOnly", "Source promotion packet must emit only decision evidence.")
    for key in promotion.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"baselinePromotionPacket.boundaries.{key}", f"Source promotion boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalSmoke") is True, "boundaries.deterministicLocalSmoke", "Acceptance smoke must be deterministic local evidence.")
    require(boundaries.get("consumesPromotionPacketOnly") is True, "boundaries.consumesPromotionPacketOnly", "Acceptance smoke must consume #343 without replaying historical evidence.")
    require(boundaries.get("acceptHoldRollbackDecisionOnly") is True, "boundaries.acceptHoldRollbackDecisionOnly", "Acceptance smoke must emit only decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Acceptance boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "accept"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = promotion_binding()
    promotion_doc = load_json(ROOT / REQUIRED_PROMOTION_PATH) if binding["exists"] else {}
    boundaries = acceptance_boundaries()
    findings = collect_findings(promotion_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-baseline-acceptance-smoke",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "acceptanceSmokeId": REQUIRED_ACCEPTANCE_ID,
        "releaseId": promotion_doc.get("releaseId", promotion.readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-baseline-acceptance-smoke",
        "findings": findings,
        "decisionCriteria": {
            "accept": [
                "#343 promotion packet fixture is present, passing, pinned by sha256, and decision=promote.",
                "#337/#339/#341/#343 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-promote, or failing.",
                "Do not accept the ADL v0.2 local beta baseline until a replacement acceptance smoke returns status=pass and decision=accept.",
            ],
            "rollback-required": [
                "Use only if this ADL v0.2 local beta baseline was already accepted and a later acceptance smoke fails.",
                "Rollback target is the last accepted local beta baseline evidence bundle; this smoke does not execute rollback.",
            ],
        },
        "operatorActions": {
            "accept": "Accept the pinned ADL v0.2 local beta evidence as the current local beta baseline for the next offline lane.",
            "hold": "Keep the previous accepted baseline and resolve listed findings before accepting #343 as baseline.",
            "rollback-required": "Revert baseline selection to the last accepted local beta packet; this smoke does not execute rollback.",
        },
        "baselinePromotionPacket": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": promotion_doc.get("mode"),
            "issue": promotion_doc.get("issue"),
            "status": promotion_doc.get("status"),
            "decision": promotion_doc.get("decision"),
            "promotionPacketId": promotion_doc.get("promotionPacketId"),
        },
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **evidence_chain_by_issue(promotion_doc).get(337, {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **evidence_chain_by_issue(promotion_doc).get(339, {})},
            {"issue": 341, "name": "readinessGate", **evidence_chain_by_issue(promotion_doc).get(341, {})},
            {"issue": 343, "name": "baselinePromotionPacket", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(promotion_doc, binding),
        "adlV02RuntimeBaseline": promotion_doc.get("adlV02RuntimeBaseline", {}),
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
        "mainnetStatement": "This acceptance smoke is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated acceptance smoke JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("accept", "hold", "rollback-required"),
        help="Optional operator-requested decision override for hold/rollback smoke dry-runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(requested_decision=args.requested_decision)
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
