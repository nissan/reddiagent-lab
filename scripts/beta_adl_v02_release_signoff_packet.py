#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta release signoff evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_release_candidate_gate as rc_gate  # noqa: E402


REQUIRED_SIGNOFF_ID = "reddiagent-beta-0-adl-v02-local-release-signoff-packet"
REQUIRED_RC_GATE_PATH = "tests/fixtures/beta-adl-v02-release-candidate-gate.json"
REQUIRED_RC_GATE_ID = rc_gate.REQUIRED_RC_GATE_ID
REQUIRED_VALID_ADL = rc_gate.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = rc_gate.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = rc_gate.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341, 343, 345, 347, 349]
CURRENT_ISSUE = 351
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = rc_gate.REQUIRED_BOUNDARY_FALSE + (
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


def rc_gate_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_RC_GATE_PATH
    return {
        "key": "releaseCandidateGate",
        "path": REQUIRED_RC_GATE_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": rc_gate.handoff.acceptance.promotion.readiness.digest(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def evidence_chain_by_issue(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        item["issue"]: item
        for item in doc.get("evidenceChain", [])
        if isinstance(item, dict) and isinstance(item.get("issue"), int)
    }


def signoff_boundaries() -> dict[str, Any]:
    return {
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

    require(binding.get("exists") is True, "releaseCandidateGate.exists", "Pinned #349 release-candidate gate fixture must exist.")
    require(bool(binding.get("sha256")), "releaseCandidateGate.sha256", "Pinned #349 release-candidate gate fixture must have a sha256.")
    require(bool(binding.get("sizeBytes")), "releaseCandidateGate.sizeBytes", "Pinned #349 release-candidate gate fixture must have a byte size.")

    require(rc_doc.get("mode") == "adl-v02-local-beta-release-candidate-gate", "releaseCandidateGate.mode", "Signoff packet must consume the #349 release-candidate gate.")
    require(rc_doc.get("issue") == 349, "releaseCandidateGate.issue", "Release-candidate gate must be issue #349.")
    require(rc_doc.get("parentEpic") == PARENT_EPIC, "releaseCandidateGate.parentEpic", "Release-candidate gate must belong to #220.")
    require(rc_doc.get("status") == "pass", "releaseCandidateGate.status", "Signoff packet requires passing RC evidence.")
    require(rc_doc.get("decision") == "rc-ready", "releaseCandidateGate.decision", "Signoff packet requires #349 decision=rc-ready.")
    require(rc_doc.get("releaseCandidateGateId") == REQUIRED_RC_GATE_ID, "releaseCandidateGate.releaseCandidateGateId", "RC gate ID must stay stable.")
    require(rc_doc.get("follows") == [337, 339, 341, 343, 345, 347], "releaseCandidateGate.follows", "RC gate must preserve the #337/#339/#341/#343/#345/#347 chain.")

    accepted_handoff = rc_doc.get("acceptedBaselineHandoff", {})
    require(accepted_handoff.get("issue") == 347, "releaseCandidateGate.acceptedBaselineHandoff.issue", "Accepted-baseline handoff must be issue #347.")
    require(accepted_handoff.get("status") == "pass", "releaseCandidateGate.acceptedBaselineHandoff.status", "Accepted-baseline handoff must pass.")
    require(accepted_handoff.get("decision") == "continue", "releaseCandidateGate.acceptedBaselineHandoff.decision", "Accepted-baseline handoff must decide continue.")
    require(bool(accepted_handoff.get("sha256")), "releaseCandidateGate.acceptedBaselineHandoff.sha256", "Accepted-baseline handoff must be pinned by sha256.")
    require(bool(accepted_handoff.get("sizeBytes")), "releaseCandidateGate.acceptedBaselineHandoff.sizeBytes", "Accepted-baseline handoff must have a byte size.")

    acceptance_smoke = rc_doc.get("baselineAcceptanceSmoke", {})
    require(acceptance_smoke.get("issue") == 345, "releaseCandidateGate.baselineAcceptanceSmoke.issue", "Upstream acceptance smoke must be issue #345.")
    require(acceptance_smoke.get("status") == "pass", "releaseCandidateGate.baselineAcceptanceSmoke.status", "Upstream acceptance smoke must pass.")
    require(acceptance_smoke.get("decision") == "accept", "releaseCandidateGate.baselineAcceptanceSmoke.decision", "Upstream acceptance smoke must decide accept.")

    promotion_packet = rc_doc.get("upstreamPromotionPacket", {})
    require(promotion_packet.get("issue") == 343, "releaseCandidateGate.upstreamPromotionPacket.issue", "Upstream promotion packet must be issue #343.")
    require(promotion_packet.get("status") == "pass", "releaseCandidateGate.upstreamPromotionPacket.status", "Upstream promotion packet must pass.")
    require(promotion_packet.get("decision") == "promote", "releaseCandidateGate.upstreamPromotionPacket.decision", "Upstream promotion packet must decide promote.")

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
        require(item.get("path") == path_text, f"releaseCandidateGate.evidenceChain.{issue}.path", f"#{issue} evidence path must remain `{path_text}`.")
        require(item.get("exists") is True, f"releaseCandidateGate.evidenceChain.{issue}.exists", f"#{issue} evidence must exist.")
        require(bool(item.get("sha256")), f"releaseCandidateGate.evidenceChain.{issue}.sha256", f"#{issue} evidence must have a sha256.")
        require(bool(item.get("sizeBytes")), f"releaseCandidateGate.evidenceChain.{issue}.sizeBytes", f"#{issue} evidence must have a byte size.")

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
    ):
        require(bool(artifact_hashes.get(path_text)), f"releaseCandidateGate.artifactHashes.{path_text}", f"`{path_text}` must keep a sha256 pin.")

    baseline = rc_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "releaseCandidateGate.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain accepted.")
    require(valid.get("status") == "pass", "releaseCandidateGate.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "releaseCandidateGate.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "releaseCandidateGate.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain accepted.")
    require(invalid.get("exitCode") == 1, "releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"releaseCandidateGate.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = rc_doc.get("boundaries", {})
    require(source_boundaries.get("deterministicLocalReleaseCandidateGate") is True, "releaseCandidateGate.boundaries.deterministicLocalReleaseCandidateGate", "Source RC gate must remain deterministic.")
    require(source_boundaries.get("consumesAcceptedBaselineHandoffOnly") is True, "releaseCandidateGate.boundaries.consumesAcceptedBaselineHandoffOnly", "Source RC gate must consume #347 only.")
    require(source_boundaries.get("releaseCandidateDecisionOnly") is True, "releaseCandidateGate.boundaries.releaseCandidateDecisionOnly", "Source RC gate must remain decision-only evidence.")
    for key in rc_gate.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"releaseCandidateGate.boundaries.{key}", f"Source RC gate boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalReleaseSignoffPacket") is True, "boundaries.deterministicLocalReleaseSignoffPacket", "Signoff packet must be deterministic local evidence.")
    require(boundaries.get("consumesReleaseCandidateGateOnly") is True, "boundaries.consumesReleaseCandidateGateOnly", "Signoff packet must consume #349 without replaying historical evidence.")
    require(boundaries.get("releaseSignoffDecisionOnly") is True, "boundaries.releaseSignoffDecisionOnly", "Signoff packet must emit only release signoff decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Signoff packet boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "release-ready"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = rc_gate_binding()
    rc_doc = load_json(ROOT / REQUIRED_RC_GATE_PATH) if binding["exists"] else {}
    boundaries = signoff_boundaries()
    findings = collect_findings(rc_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-release-signoff-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "releaseSignoffPacketId": REQUIRED_SIGNOFF_ID,
        "releaseId": rc_doc.get("releaseId", rc_gate.handoff.acceptance.promotion.readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-release-signoff-packet",
        "findings": findings,
        "decisionCriteria": {
            "release-ready": [
                "#349 release-candidate gate fixture is present, passing, pinned by sha256, and decision=rc-ready.",
                "#347 accepted-baseline handoff remains status=pass and decision=continue.",
                "Upstream #345 acceptance smoke remains status=pass and decision=accept.",
                "Upstream #343 baseline promotion packet remains status=pass and decision=promote.",
                "#337/#339/#341/#343/#345/#347/#349 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required RC, handoff, acceptance, promotion, artifact, diagnostic, or guardrail evidence is missing, stale, non-rc-ready, non-continue, non-accept, non-promote, or failing.",
                "Do not treat the ADL v0.2 local beta RC as release-ready until a replacement signoff packet returns status=pass and decision=release-ready.",
            ],
            "rollback-required": [
                "Use only if this local beta RC was already treated as release-ready and a later signoff gate fails.",
                "Rollback target is the last RC-ready local beta release-candidate gate; this packet does not execute rollback.",
            ],
        },
        "operatorActions": {
            "release-ready": "Treat the pinned ADL v0.2 local beta RC as the current deterministic release-ready input for the next beta release handoff step.",
            "hold": "Keep the RC out of release handoff flow and resolve listed findings before continuing.",
            "rollback-required": "Revert release-ready selection to the last RC-ready local beta gate; this packet does not execute rollback.",
        },
        "releaseCandidateGate": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": rc_doc.get("mode"),
            "issue": rc_doc.get("issue"),
            "status": rc_doc.get("status"),
            "decision": rc_doc.get("decision"),
            "releaseCandidateGateId": rc_doc.get("releaseCandidateGateId"),
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
            {"issue": 349, "name": "releaseCandidateGate", **binding},
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
        "mainnetStatement": "This release signoff packet is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated release signoff packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("release-ready", "hold", "rollback-required"),
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
