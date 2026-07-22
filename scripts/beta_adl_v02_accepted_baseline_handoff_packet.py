#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta accepted-baseline handoff evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_baseline_acceptance_smoke as acceptance  # noqa: E402


REQUIRED_HANDOFF_ID = "reddiagent-beta-0-adl-v02-local-accepted-baseline-handoff-packet"
REQUIRED_ACCEPTANCE_PATH = "tests/fixtures/beta-adl-v02-baseline-acceptance-smoke.json"
REQUIRED_ACCEPTANCE_ID = acceptance.REQUIRED_ACCEPTANCE_ID
REQUIRED_VALID_ADL = acceptance.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = acceptance.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = acceptance.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343, 345]
CURRENT_ISSUE = 347
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = acceptance.REQUIRED_BOUNDARY_FALSE + (
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


def acceptance_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_ACCEPTANCE_PATH
    return {
        "key": "baselineAcceptanceSmoke",
        "path": REQUIRED_ACCEPTANCE_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": acceptance.promotion.readiness.digest(path) if path.exists() and path.is_file() else None,
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
        "deterministicLocalHandoff": True,
        "consumesAcceptanceSmokeOnly": True,
        "acceptedBaselineInspectionOnly": True,
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


def expected_artifact_hashes(acceptance_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for path, digest in acceptance_doc.get("artifactHashes", {}).items():
        if isinstance(path, str):
            hashes[path] = digest
    return hashes


def collect_findings(
    acceptance_doc: dict[str, Any],
    binding: dict[str, Any],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "baselineAcceptanceSmoke.exists", "Pinned #345 acceptance smoke fixture must exist.")
    require(bool(binding.get("sha256")), "baselineAcceptanceSmoke.sha256", "Pinned #345 acceptance smoke fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "baselineAcceptanceSmoke.sizeBytes", "Pinned #345 acceptance smoke fixture must have a byte size.")

    require(acceptance_doc.get("mode") == "adl-v02-local-beta-baseline-acceptance-smoke", "baselineAcceptanceSmoke.mode", "Handoff must consume the #345 acceptance smoke.")
    require(acceptance_doc.get("issue") == 345, "baselineAcceptanceSmoke.issue", "Acceptance smoke must be issue #345.")
    require(acceptance_doc.get("parentEpic") == PARENT_EPIC, "baselineAcceptanceSmoke.parentEpic", "Acceptance smoke must belong to #220.")
    require(acceptance_doc.get("status") == "pass", "baselineAcceptanceSmoke.status", "Handoff requires passing acceptance smoke.")
    require(acceptance_doc.get("decision") == "accept", "baselineAcceptanceSmoke.decision", "Handoff requires #345 decision=accept.")
    require(acceptance_doc.get("acceptanceSmokeId") == REQUIRED_ACCEPTANCE_ID, "baselineAcceptanceSmoke.acceptanceSmokeId", "Acceptance smoke ID must stay stable.")
    require(acceptance_doc.get("follows") == [337, 339, 341, 343], "baselineAcceptanceSmoke.follows", "Acceptance smoke must preserve the #337/#339/#341/#343 chain.")

    promotion_packet = acceptance_doc.get("baselinePromotionPacket", {})
    require(promotion_packet.get("issue") == 343, "baselineAcceptanceSmoke.baselinePromotionPacket.issue", "Upstream promotion packet must be issue #343.")
    require(promotion_packet.get("status") == "pass", "baselineAcceptanceSmoke.baselinePromotionPacket.status", "Upstream promotion packet must pass.")
    require(promotion_packet.get("decision") == "promote", "baselineAcceptanceSmoke.baselinePromotionPacket.decision", "Upstream promotion packet must decide promote.")
    require(bool(promotion_packet.get("sha256")), "baselineAcceptanceSmoke.baselinePromotionPacket.sha256", "Upstream promotion packet must be pinned by sha256.")
    require(bool(promotion_packet.get("sizeBytes")), "baselineAcceptanceSmoke.baselinePromotionPacket.sizeBytes", "Upstream promotion packet must have a byte size.")

    chain = evidence_chain_by_issue(acceptance_doc)
    for issue, path_text in {
        337: "tests/fixtures/beta-release-handoff.json",
        339: "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        341: "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        343: "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
    }.items():
        item = chain.get(issue, {})
        require(item.get("path") == path_text, f"baselineAcceptanceSmoke.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"baselineAcceptanceSmoke.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"baselineAcceptanceSmoke.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"baselineAcceptanceSmoke.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

    artifact_hashes = acceptance_doc.get("artifactHashes", {})
    for path_text in (
        REQUIRED_VALID_ADL,
        REQUIRED_INVALID_ADL,
        "tests/fixtures/beta-release-handoff.json",
        "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
        "tests/fixtures/beta-adl-v02-local-readiness-gate.json",
        "tests/fixtures/beta-adl-v02-baseline-promotion-packet.json",
    ):
        require(bool(artifact_hashes.get(path_text)), f"baselineAcceptanceSmoke.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = acceptance_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "baselineAcceptanceSmoke.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "baselineAcceptanceSmoke.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "baselineAcceptanceSmoke.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "baselineAcceptanceSmoke.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "baselineAcceptanceSmoke.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "baselineAcceptanceSmoke.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "baselineAcceptanceSmoke.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "baselineAcceptanceSmoke.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"baselineAcceptanceSmoke.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = acceptance_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalSmoke") is True, "baselineAcceptanceSmoke.boundaries.deterministicLocalSmoke", "Source acceptance smoke must remain deterministic.")
    require(source_boundaries.get("consumesPromotionPacketOnly") is True, "baselineAcceptanceSmoke.boundaries.consumesPromotionPacketOnly", "Source acceptance smoke must consume #343 only.")
    require(source_boundaries.get("acceptHoldRollbackDecisionOnly") is True, "baselineAcceptanceSmoke.boundaries.acceptHoldRollbackDecisionOnly", "Source acceptance smoke must emit only decision evidence.")
    for key in acceptance.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"baselineAcceptanceSmoke.boundaries.{key}", f"Source acceptance boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalHandoff") is True, "boundaries.deterministicLocalHandoff", "Handoff packet must be deterministic local evidence.")
    require(boundaries.get("consumesAcceptanceSmokeOnly") is True, "boundaries.consumesAcceptanceSmokeOnly", "Handoff packet must consume #345 without replaying historical evidence.")
    require(boundaries.get("acceptedBaselineInspectionOnly") is True, "boundaries.acceptedBaselineInspectionOnly", "Handoff packet must only support offline inspection.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Handoff boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "continue"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = acceptance_binding()
    acceptance_doc = load_json(ROOT / REQUIRED_ACCEPTANCE_PATH) if binding["exists"] else {}
    boundaries = handoff_boundaries()
    findings = collect_findings(acceptance_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-accepted-baseline-handoff-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "handoffPacketId": REQUIRED_HANDOFF_ID,
        "releaseId": acceptance_doc.get("releaseId", acceptance.promotion.readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-accepted-baseline-handoff-packet",
        "findings": findings,
        "decisionCriteria": {
            "continue": [
                "#345 acceptance smoke fixture is present, passing, pinned by sha256, and decision=accept.",
                "Upstream #343 baseline promotion packet is present in #345 evidence and decision=promote.",
                "#337/#339/#341/#343/#345 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required acceptance, promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-accept, non-promote, or failing.",
                "Do not continue from this accepted baseline until a replacement handoff packet returns status=pass and decision=continue.",
            ],
            "rollback-required": [
                "Use only if this accepted local beta baseline was already handed off and a later handoff packet fails.",
                "Rollback target is the last accepted local beta handoff packet; this packet does not execute rollback.",
            ],
        },
        "operatorActions": {
            "continue": "Use this compact packet as the offline accepted-baseline handoff for the next ADL v0.2 local beta lane.",
            "hold": "Keep the previous accepted baseline and resolve listed findings before continuing.",
            "rollback-required": "Revert baseline selection to the last accepted local beta handoff packet; this packet does not execute rollback.",
        },
        "baselineAcceptanceSmoke": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": acceptance_doc.get("mode"),
            "issue": acceptance_doc.get("issue"),
            "status": acceptance_doc.get("status"),
            "decision": acceptance_doc.get("decision"),
            "acceptanceSmokeId": acceptance_doc.get("acceptanceSmokeId"),
        },
        "upstreamPromotionPacket": acceptance_doc.get("baselinePromotionPacket", {}),
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **evidence_chain_by_issue(acceptance_doc).get(337, {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **evidence_chain_by_issue(acceptance_doc).get(339, {})},
            {"issue": 341, "name": "readinessGate", **evidence_chain_by_issue(acceptance_doc).get(341, {})},
            {"issue": 343, "name": "baselinePromotionPacket", **evidence_chain_by_issue(acceptance_doc).get(343, {})},
            {"issue": 345, "name": "baselineAcceptanceSmoke", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(acceptance_doc, binding),
        "adlV02RuntimeBaseline": acceptance_doc.get("adlV02RuntimeBaseline", {}),
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
        "mainnetStatement": "This accepted-baseline handoff packet is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated accepted-baseline handoff packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("continue", "hold", "rollback-required"),
        help="Optional operator-requested decision override for hold/rollback packet dry-runs.",
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
