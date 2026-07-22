#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta baseline promotion packet evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_local_readiness_gate as readiness  # noqa: E402


REQUIRED_PACKET_ID = "reddiagent-beta-0-adl-v02-local-baseline-promotion-packet"
REQUIRED_READINESS_PATH = "tests/fixtures/beta-adl-v02-local-readiness-gate.json"
REQUIRED_READINESS_ID = readiness.REQUIRED_READINESS_ID
REQUIRED_VALID_ADL = readiness.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = readiness.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = readiness.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_FOLLOWS = [337, 339, 341]
CURRENT_ISSUE = 343
PARENT_EPIC = 220
REQUIRED_BOUNDARY_FALSE = readiness.REQUIRED_BOUNDARY_FALSE + (
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


def readiness_binding() -> dict[str, Any]:
    path = ROOT / REQUIRED_READINESS_PATH
    return {
        "key": "readinessGate",
        "path": REQUIRED_READINESS_PATH,
        "exists": path.exists() and path.is_file(),
        "sha256": readiness.digest(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def inventory_by_key(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("key"): item
        for item in doc.get("artifactInventory", [])
        if isinstance(item, dict) and item.get("key")
    }


def expected_artifact_hashes(readiness_doc: dict[str, Any], binding: dict[str, Any]) -> dict[str, str | None]:
    hashes = {binding["path"]: binding.get("sha256")}
    for item in readiness_doc.get("artifactInventory", []):
        if isinstance(item, dict) and item.get("path"):
            hashes[item["path"]] = item.get("sha256")
    return hashes


def packet_boundaries() -> dict[str, Any]:
    boundaries = {
        "deterministicLocalPacket": True,
        "consumesReadinessGateOnly": True,
        "promoteHoldRollbackDecisionOnly": True,
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
    return boundaries


def collect_findings(readiness_doc: dict[str, Any], binding: dict[str, Any], boundaries: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    require(binding.get("exists") is True, "readinessGate.exists", "Pinned #341 readiness fixture must exist.")
    require(bool(binding.get("sha256")), "readinessGate.sha256", "Pinned #341 readiness fixture must have a sha256.")
    require(readiness_doc.get("mode") == "adl-v02-local-beta-readiness-gate", "readinessGate.mode", "Packet must consume the #341 readiness gate artifact.")
    require(readiness_doc.get("issue") == 341, "readinessGate.issue", "Readiness gate must be issue #341.")
    require(readiness_doc.get("parentEpic") == PARENT_EPIC, "readinessGate.parentEpic", "Readiness gate must belong to #220.")
    require(readiness_doc.get("status") == "pass", "readinessGate.status", "Promotion packet requires a passing readiness gate.")
    require(readiness_doc.get("baselineDecision") == "ready", "readinessGate.baselineDecision", "Promotion packet requires readiness baselineDecision=ready.")
    require(readiness_doc.get("readinessId") == REQUIRED_READINESS_ID, "readinessGate.readinessId", "Readiness gate ID must stay stable.")
    require(readiness_doc.get("follows") == [337, 339], "readinessGate.follows", "Readiness gate must preserve the #337/#339 chain.")

    inventory = inventory_by_key(readiness_doc)
    for key, path_text in readiness.REQUIRED_ARTIFACTS.items():
        item = inventory.get(key, {})
        require(item.get("path") == path_text, f"readinessGate.artifactInventory.{key}.path", f"{key} path must remain `{path_text}`.")
        require(item.get("exists") is True, f"readinessGate.artifactInventory.{key}.exists", f"{key} must exist.")
        require(bool(item.get("sha256")), f"readinessGate.artifactInventory.{key}.sha256", f"{key} must have a sha256.")
        require(bool(item.get("sizeBytes")), f"readinessGate.artifactInventory.{key}.sizeBytes", f"{key} must have a byte size.")

    baseline = readiness_doc.get("adlV02RuntimeBaseline", {})
    valid = baseline.get("validRuntimeExample", {}) if isinstance(baseline, dict) else {}
    invalid = baseline.get("invalidDiagnosticSample", {}) if isinstance(baseline, dict) else {}
    diagnostics = invalid.get("diagnostics", []) if isinstance(invalid, dict) else []
    require(valid.get("adl") == REQUIRED_VALID_ADL, "readinessGate.adlV02RuntimeBaseline.validRuntimeExample.adl", "Valid runtime ADL path must remain in the beta baseline.")
    require(valid.get("status") == "pass", "readinessGate.adlV02RuntimeBaseline.validRuntimeExample.status", "Valid runtime example must pass.")
    require(valid.get("exitCode") == 0, "readinessGate.adlV02RuntimeBaseline.validRuntimeExample.exitCode", "Valid runtime example must exit zero.")
    require(valid.get("completionStatus") == "pass", "readinessGate.adlV02RuntimeBaseline.validRuntimeExample.completionStatus", "Valid runtime completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "readinessGate.adlV02RuntimeBaseline.invalidDiagnosticSample.adl", "Invalid diagnostic ADL path must remain in the beta baseline.")
    require(invalid.get("exitCode") == 1, "readinessGate.adlV02RuntimeBaseline.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail closed.")
    require(invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "readinessGate.adlV02RuntimeBaseline.invalidDiagnosticSample.stableFields", "Stable diagnostic fields must remain pinned.")
    require(bool(diagnostics), "readinessGate.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"readinessGate.adlV02RuntimeBaseline.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    source_boundaries = readiness_doc.get("boundaries", {})
    require(source_boundaries.get("offlinePassFailGate") is True, "readinessGate.boundaries.offlinePassFailGate", "Source readiness gate must remain offline.")
    require(source_boundaries.get("consumesHandoffAndWalkthroughOnly") is True, "readinessGate.boundaries.consumesHandoffAndWalkthroughOnly", "Source readiness gate must not replay the full chain.")
    require(source_boundaries.get("deterministicLocalFixturesOnly") is True, "readinessGate.boundaries.deterministicLocalFixturesOnly", "Source readiness gate must remain deterministic.")
    for key in readiness.REQUIRED_BOUNDARY_FALSE:
        require(source_boundaries.get(key) is False, f"readinessGate.boundaries.{key}", f"Source readiness boundary `{key}` must remain false.")

    require(boundaries.get("deterministicLocalPacket") is True, "boundaries.deterministicLocalPacket", "Packet must be deterministic local evidence.")
    require(boundaries.get("consumesReadinessGateOnly") is True, "boundaries.consumesReadinessGateOnly", "Packet must consume the #341 gate without replaying the historical chain.")
    require(boundaries.get("promoteHoldRollbackDecisionOnly") is True, "boundaries.promoteHoldRollbackDecisionOnly", "Packet must emit only decision evidence.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"Packet boundary `{key}` must remain false.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "promote"


def build_report(commit: str | None = None, requested_decision: str | None = None) -> dict[str, Any]:
    binding = readiness_binding()
    readiness_doc = load_json(ROOT / REQUIRED_READINESS_PATH) if binding["exists"] else {}
    boundaries = packet_boundaries()
    findings = collect_findings(readiness_doc, binding, boundaries)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "adl-v02-local-beta-baseline-promotion-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": REQUIRED_FOLLOWS,
        "promotionPacketId": REQUIRED_PACKET_ID,
        "releaseId": readiness_doc.get("releaseId", readiness.REQUIRED_RELEASE_ID),
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "sourceCommit": commit or "fixture://adl-v02-local-beta-baseline-promotion-packet",
        "findings": findings,
        "decisionCriteria": {
            "promote": [
                "#341 readiness gate fixture is present, passing, and pinned by sha256.",
                "#337/#339/#341 evidence chain is preserved by issue IDs, paths, sizes, and sha256 hashes.",
                "Valid ADL v0.2 runtime example remains present and passing.",
                "Invalid ADL v0.2 diagnostic sample remains fail-closed with stable diagnostic fields.",
                "All local/free/deterministic guardrails remain false for live, hosted, provider, payment, devnet, mainnet, publishing, and gateway mutation actions.",
            ],
            "hold": [
                "Use when any required readiness, artifact, diagnostic, or guardrail evidence is missing, stale, or failing.",
                "Do not promote the ADL v0.2 local beta baseline until a replacement packet returns status=pass and decision=promote.",
            ],
            "rollback-required": [
                "Use only if the current promoted local beta baseline has already been advertised or selected and this packet later fails.",
                "Rollback target is the prior accepted local beta baseline evidence bundle; do not perform runtime, deployment, provider, payment, devnet, mainnet, publishing, or gateway actions from this packet.",
            ],
        },
        "operatorActions": {
            "promote": "Treat the pinned ADL v0.2 local beta evidence as the active local beta baseline for the next offline reviewer/operator lane.",
            "hold": "Keep the previous baseline and resolve listed findings before promotion.",
            "rollback-required": "Revert reviewer/operator baseline selection to the last accepted local beta packet; this packet does not execute rollback.",
        },
        "readinessGate": {
            "path": binding["path"],
            "sha256": binding.get("sha256"),
            "sizeBytes": binding.get("sizeBytes"),
            "mode": readiness_doc.get("mode"),
            "issue": readiness_doc.get("issue"),
            "status": readiness_doc.get("status"),
            "baselineDecision": readiness_doc.get("baselineDecision"),
            "readinessId": readiness_doc.get("readinessId"),
        },
        "evidenceChain": [
            {"issue": 337, "name": "releaseHandoff", **inventory_by_key(readiness_doc).get("releaseHandoff", {})},
            {"issue": 339, "name": "reviewerWalkthroughSmoke", **inventory_by_key(readiness_doc).get("reviewerWalkthroughSmoke", {})},
            {"issue": 341, "name": "readinessGate", **binding},
        ],
        "artifactHashes": expected_artifact_hashes(readiness_doc, binding),
        "adlV02RuntimeBaseline": readiness_doc.get("adlV02RuntimeBaseline", {}),
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
        "mainnetStatement": "This promotion packet is local/free/deterministic evidence only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated promotion packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("promote", "hold", "rollback-required"),
        help="Optional operator-requested decision override for hold/rollback packet dry-runs.",
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
