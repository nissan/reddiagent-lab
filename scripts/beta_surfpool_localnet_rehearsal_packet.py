#!/usr/bin/env python3
"""Build deterministic Surfpool/localnet external beta rehearsal evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PACKET_PATH = "tests/fixtures/beta-adl-v02-release-archive-packet.json"
ROADMAP_PACKET_PATH = "research/2026-07-23-agentic-payments-roadmap-recalibration.md"
SURFPOOL_LANE_PATH = "tests/fixtures/surfpool-validator-lane.json"
CURRENT_ISSUE = 359
PARENT_EPIC = 220
REQUIRED_RELEASE_ARCHIVE_ISSUE = 355
REQUIRED_ROADMAP_ISSUE = 356
REQUIRED_SURFPOOL_LANE_ISSUE = 248
REQUIRED_LOCALNET_TERMS = (
    "Surfpool/localnet",
    "fixture accounts/mints",
    "delegated authority",
    "replay",
    "receipt",
    "rollback",
    "no mainnet",
)
REQUIRED_BOUNDARY_FALSE = (
    "liveRuntimeActivation",
    "hostedDeployment",
    "dockerMutation",
    "surfpoolMutation",
    "coolifyMutation",
    "networkAccess",
    "credentialAccess",
    "providerApiAccess",
    "mcpInvocation",
    "paymentAccess",
    "walletAccess",
    "facilitatorAccess",
    "settlementAccess",
    "devnetAccess",
    "mainnetAccess",
    "deploymentPublished",
    "packagePublished",
    "archivePublished",
    "publicPublished",
    "externalSpend",
    "productionGatewayMutation",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_id(*parts: str) -> str:
    return digest_text("|".join(parts))[:16]


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def artifact_binding(path_text: str) -> dict[str, Any]:
    path = ROOT / path_text
    return {
        "path": path_text,
        "exists": path.exists() and path.is_file(),
        "sha256": digest_file(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def rehearsal_boundaries() -> dict[str, Any]:
    return {
        "deterministicLocalnetRehearsalPacket": True,
        "consumesReleaseArchiveAndRoadmapOnly": True,
        "usesSurfpoolLaneAsStaticInput": True,
        "externalBetaRehearsalEvidenceOnly": True,
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


def default_scenarios() -> list[dict[str, Any]]:
    common_boundary = {
        "network": "localnet",
        "devnetUsed": False,
        "mainnetUsed": False,
        "walletAccessUsed": False,
        "facilitatorUsed": False,
        "settlementClaimed": False,
        "realValueTransfer": False,
    }
    return [
        {
            "id": "localnet-setup-pass",
            "kind": "setup",
            "expectedStatus": "pass",
            "cluster": {
                "validatorPreference": "surfpool-local",
                "endpoint": "127.0.0.1",
                "resetRequired": True,
                "ledgerPath": ".tmp/reddiagent-localnet-rehearsal",
            },
            "fixtureAccounts": [
                {"id": "tester-principal", "role": "principal", "lamports": 5_000_000_000},
                {"id": "agent-spender", "role": "spender", "lamports": 1_000_000_000},
                {"id": "merchant-service", "role": "payee", "lamports": 0},
            ],
            "fixtureMints": [
                {"symbol": "rUSD-L", "mint": "fixture:mint:localnet-rusd", "decimals": 6, "supply": 1_000_000_000},
            ],
            "authority": {
                "mandateId": "mandate-localnet-beta-001",
                "principal": "tester-principal",
                "spender": "agent-spender",
                "payee": "merchant-service",
                "assetMint": "fixture:mint:localnet-rusd",
                "maxAmount": 250_000,
                "expiresSlot": 9000,
                "nonce": "nonce-localnet-001",
                "revocable": True,
            },
            "receipt": {
                "receiptId": "receipt-localnet-setup",
                "status": "dry-run-recorded",
                "bindsRequestHash": True,
                "bindsResponseHash": True,
                "bindsMandateId": True,
                "bindsEvalStatus": True,
            },
            "rollback": {"drill": "reset-local-ledger", "verified": True, "killSwitch": "operator-hold"},
            "boundaries": common_boundary,
        },
        {
            "id": "delegated-authority-pass",
            "kind": "authority",
            "expectedStatus": "pass",
            "attempt": {"amount": 125_000, "slot": 5120, "purpose": "paid-data-receipt-review"},
            "authority": {
                "mandateId": "mandate-localnet-beta-001",
                "principal": "tester-principal",
                "spender": "agent-spender",
                "payee": "merchant-service",
                "assetMint": "fixture:mint:localnet-rusd",
                "maxAmount": 250_000,
                "expiresSlot": 9000,
                "nonce": "nonce-authority-001",
                "revocable": True,
            },
            "receipt": {
                "receiptId": "receipt-authority-pass",
                "status": "dry-run-recorded",
                "bindsRequestHash": True,
                "bindsResponseHash": True,
                "bindsMandateId": True,
                "bindsEvalStatus": True,
            },
            "rollback": {"drill": "revoke-mandate-and-reset-ledger", "verified": True, "killSwitch": "operator-disable"},
            "boundaries": common_boundary,
        },
        {
            "id": "replay-denied",
            "kind": "replay",
            "expectedStatus": "fail",
            "attempt": {"amount": 125_000, "slot": 5122, "purpose": "paid-data-receipt-review"},
            "authority": {
                "mandateId": "mandate-localnet-beta-001",
                "principal": "tester-principal",
                "spender": "agent-spender",
                "payee": "merchant-service",
                "assetMint": "fixture:mint:localnet-rusd",
                "maxAmount": 250_000,
                "expiresSlot": 9000,
                "nonce": "nonce-authority-001",
                "revocable": True,
            },
            "replay": {"previousNonceSeen": True, "previousReceiptId": "receipt-authority-pass"},
            "receipt": None,
            "rollback": {"drill": "discard-replayed-run", "verified": True, "killSwitch": "operator-hold"},
            "boundaries": common_boundary,
        },
        {
            "id": "over-cap-denied",
            "kind": "authority",
            "expectedStatus": "fail",
            "attempt": {"amount": 300_000, "slot": 5124, "purpose": "paid-data-receipt-review"},
            "authority": {
                "mandateId": "mandate-localnet-beta-001",
                "principal": "tester-principal",
                "spender": "agent-spender",
                "payee": "merchant-service",
                "assetMint": "fixture:mint:localnet-rusd",
                "maxAmount": 250_000,
                "expiresSlot": 9000,
                "nonce": "nonce-over-cap-001",
                "revocable": True,
            },
            "receipt": None,
            "rollback": {"drill": "operator-hold-no-receipt", "verified": True, "killSwitch": "operator-disable"},
            "boundaries": common_boundary,
        },
        {
            "id": "receipt-mismatch-denied",
            "kind": "receipt",
            "expectedStatus": "fail",
            "attempt": {"amount": 125_000, "slot": 5126, "purpose": "paid-data-receipt-review"},
            "authority": {
                "mandateId": "mandate-localnet-beta-001",
                "principal": "tester-principal",
                "spender": "agent-spender",
                "payee": "merchant-service",
                "assetMint": "fixture:mint:localnet-rusd",
                "maxAmount": 250_000,
                "expiresSlot": 9000,
                "nonce": "nonce-receipt-mismatch-001",
                "revocable": True,
            },
            "receipt": {
                "receiptId": "receipt-mismatch-denied",
                "status": "dry-run-recorded",
                "bindsRequestHash": True,
                "bindsResponseHash": False,
                "bindsMandateId": True,
                "bindsEvalStatus": True,
            },
            "rollback": {"drill": "mark-receipt-invalid-and-reset-ledger", "verified": True, "killSwitch": "operator-hold"},
            "boundaries": common_boundary,
        },
    ]


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    authority = scenario.get("authority", {})
    attempt = scenario.get("attempt", {})
    receipt = scenario.get("receipt")
    rollback = scenario.get("rollback", {})
    boundaries = scenario.get("boundaries", {})
    cluster = scenario.get("cluster", {})
    fixture_accounts = scenario.get("fixtureAccounts", [])
    fixture_mints = scenario.get("fixtureMints", [])

    require(boundaries.get("network") == "localnet", f"scenarios.{scenario.get('id')}.boundaries.network", "Rehearsal scenarios must stay localnet-only.")
    for key in ("devnetUsed", "mainnetUsed", "walletAccessUsed", "facilitatorUsed", "settlementClaimed", "realValueTransfer"):
        require(boundaries.get(key) is False, f"scenarios.{scenario.get('id')}.boundaries.{key}", f"{key} must be false.")
    require(rollback.get("verified") is True, f"scenarios.{scenario.get('id')}.rollback.verified", "Rollback drill must be verified.")
    require(bool(rollback.get("killSwitch")), f"scenarios.{scenario.get('id')}.rollback.killSwitch", "Operator kill-switch/hold path is required.")

    if scenario.get("kind") == "setup":
        require(cluster.get("validatorPreference") == "surfpool-local", f"scenarios.{scenario.get('id')}.cluster.validatorPreference", "Setup must prefer Surfpool localnet.")
        require(cluster.get("endpoint") in {"127.0.0.1", "localhost"}, f"scenarios.{scenario.get('id')}.cluster.endpoint", "Setup endpoint must be loopback only.")
        require(bool(fixture_accounts), f"scenarios.{scenario.get('id')}.fixtureAccounts", "Fixture accounts are required.")
        require(bool(fixture_mints), f"scenarios.{scenario.get('id')}.fixtureMints", "Fixture mints are required.")

    require(authority.get("mandateId") == "mandate-localnet-beta-001", f"scenarios.{scenario.get('id')}.authority.mandateId", "Authority must bind to the localnet beta mandate.")
    require(authority.get("principal") == "tester-principal", f"scenarios.{scenario.get('id')}.authority.principal", "Principal fixture must be pinned.")
    require(authority.get("spender") == "agent-spender", f"scenarios.{scenario.get('id')}.authority.spender", "Spender fixture must be pinned.")
    require(authority.get("payee") == "merchant-service", f"scenarios.{scenario.get('id')}.authority.payee", "Payee fixture must be pinned.")
    require(authority.get("assetMint") == "fixture:mint:localnet-rusd", f"scenarios.{scenario.get('id')}.authority.assetMint", "Fixture mint must be pinned.")
    require(authority.get("revocable") is True, f"scenarios.{scenario.get('id')}.authority.revocable", "Mandate must be revocable.")

    if attempt:
        require(attempt.get("amount", 0) <= authority.get("maxAmount", -1), f"scenarios.{scenario.get('id')}.attempt.amount", "Attempt amount must not exceed mandate cap.")
        require(attempt.get("slot", 0) < authority.get("expiresSlot", -1), f"scenarios.{scenario.get('id')}.attempt.slot", "Attempt slot must be before mandate expiry.")

    replay = scenario.get("replay", {})
    require(replay.get("previousNonceSeen") is not True, f"scenarios.{scenario.get('id')}.replay.previousNonceSeen", "Replay attempts must fail closed before receipt emission.")

    if scenario.get("expectedStatus") == "pass":
        require(isinstance(receipt, dict), f"scenarios.{scenario.get('id')}.receipt", "Passing rehearsal scenarios must emit a dry-run receipt.")
    if isinstance(receipt, dict):
        for key in ("bindsRequestHash", "bindsResponseHash", "bindsMandateId", "bindsEvalStatus"):
            require(receipt.get(key) is True, f"scenarios.{scenario.get('id')}.receipt.{key}", f"Receipt must bind {key}.")
        require(receipt.get("status") == "dry-run-recorded", f"scenarios.{scenario.get('id')}.receipt.status", "Receipt must be dry-run evidence only.")

    return findings


def build_scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    status = "pass" if not findings else "fail"
    trace_id = stable_id("issue-359", scenario.get("id", ""), scenario.get("kind", ""))
    return {
        "id": scenario.get("id"),
        "kind": scenario.get("kind"),
        "expectedStatus": scenario.get("expectedStatus"),
        "status": status,
        "traceId": trace_id,
        "authorityRef": scenario.get("authority", {}).get("mandateId"),
        "receiptRef": scenario.get("receipt", {}).get("receiptId") if isinstance(scenario.get("receipt"), dict) else None,
        "rollbackDrill": scenario.get("rollback", {}).get("drill"),
        "inputs": {
            "cluster": scenario.get("cluster"),
            "fixtureAccounts": scenario.get("fixtureAccounts", []),
            "fixtureMints": scenario.get("fixtureMints", []),
            "authority": scenario.get("authority"),
            "attempt": scenario.get("attempt"),
            "replay": scenario.get("replay"),
            "receipt": scenario.get("receipt"),
            "rollback": scenario.get("rollback"),
            "boundaries": scenario.get("boundaries"),
        },
        "findings": findings,
    }


def collect_packet_findings(
    archive_doc: dict[str, Any],
    archive_binding: dict[str, Any],
    roadmap_text: str,
    roadmap_binding: dict[str, Any],
    surfpool_doc: dict[str, Any],
    surfpool_binding: dict[str, Any],
    boundaries: dict[str, Any],
    scenario_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    for name, binding in {
        "releaseArchivePacket": archive_binding,
        "roadmapPacket": roadmap_binding,
        "surfpoolValidatorLane": surfpool_binding,
    }.items():
        require(binding.get("exists") is True, f"{name}.exists", "Required input artifact must exist.")
        require(bool(binding.get("sha256")), f"{name}.sha256", "Required input artifact must be pinned by sha256.")
        require(bool(binding.get("sizeBytes")), f"{name}.sizeBytes", "Required input artifact must have a byte size.")

    require(archive_doc.get("issue") == REQUIRED_RELEASE_ARCHIVE_ISSUE, "releaseArchivePacket.issue", "Must consume #355 release archive packet.")
    require(archive_doc.get("status") == "pass", "releaseArchivePacket.status", "#355 release archive packet must pass.")
    require(archive_doc.get("decision") == "archive-ready", "releaseArchivePacket.decision", "#355 release archive packet must be archive-ready.")
    require(archive_doc.get("archiveSummary", {}).get("readyForOfflineInspection") is True, "releaseArchivePacket.archiveSummary.readyForOfflineInspection", "#355 archive must be reviewer-ready.")

    for term in REQUIRED_LOCALNET_TERMS:
        require(term.lower() in roadmap_text.lower(), f"roadmapPacket.term.{term}", f"#356 roadmap must mention {term}.")
    require("## Practical Release Ladder" in roadmap_text, "roadmapPacket.Practical Release Ladder", "#356 roadmap ladder is required.")
    require("## Audit Prep Deltas" in roadmap_text, "roadmapPacket.Audit Prep Deltas", "#356 audit-prep deltas are required.")

    require(surfpool_doc.get("issue") == REQUIRED_SURFPOOL_LANE_ISSUE, "surfpoolValidatorLane.issue", "Must consume #248 Surfpool validator lane evidence.")
    require(surfpool_doc.get("status") == "pass", "surfpoolValidatorLane.status", "#248 Surfpool validator lane must pass.")
    require(surfpool_doc.get("validatorPreference", {}).get("preferred") == "surfpool-local", "surfpoolValidatorLane.validatorPreference.preferred", "Surfpool must remain preferred.")
    require(surfpool_doc.get("boundaries", {}).get("validatorStartedByThisScript") is False, "surfpoolValidatorLane.boundaries.validatorStartedByThisScript", "#359 must not start a validator.")
    require(surfpool_doc.get("boundaries", {}).get("devnetAccessUsed") is False, "surfpoolValidatorLane.boundaries.devnetAccessUsed", "Surfpool input must not use devnet.")
    require(surfpool_doc.get("boundaries", {}).get("mainnetAccessUsed") is False, "surfpoolValidatorLane.boundaries.mainnetAccessUsed", "Surfpool input must not use mainnet.")

    for key in ("deterministicLocalnetRehearsalPacket", "consumesReleaseArchiveAndRoadmapOnly", "usesSurfpoolLaneAsStaticInput", "externalBetaRehearsalEvidenceOnly"):
        require(boundaries.get(key) is True, f"boundaries.{key}", f"{key} must be true.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"{key} must be false.")

    positive = [scenario for scenario in scenario_results if scenario["expectedStatus"] == "pass"]
    negative = [scenario for scenario in scenario_results if scenario["expectedStatus"] == "fail"]
    require(len(positive) >= 2, "scenarios.positive", "At least setup and authority pass scenarios are required.")
    require(len(negative) >= 3, "scenarios.negative", "Replay, cap, and receipt mismatch fail-closed scenarios are required.")
    for scenario in positive:
        require(scenario["status"] == "pass", f"scenarios.{scenario['id']}.status", "Positive scenario must pass.")
    for scenario in negative:
        require(scenario["status"] == "fail", f"scenarios.{scenario['id']}.status", "Negative scenario must fail closed.")

    return findings


def decision_for(findings: list[dict[str, str]], requested: str | None = None) -> str:
    if requested in {"hold", "rollback-required"}:
        return requested
    if findings:
        return "hold"
    return "localnet-rehearsal-ready"


def build_report(requested_decision: str | None = None) -> dict[str, Any]:
    archive_binding = artifact_binding(ARCHIVE_PACKET_PATH)
    roadmap_binding = artifact_binding(ROADMAP_PACKET_PATH)
    surfpool_binding = artifact_binding(SURFPOOL_LANE_PATH)
    archive_doc = load_json(ROOT / ARCHIVE_PACKET_PATH) if archive_binding["exists"] else {}
    roadmap_text = (ROOT / ROADMAP_PACKET_PATH).read_text(encoding="utf-8") if roadmap_binding["exists"] else ""
    surfpool_doc = load_json(ROOT / SURFPOOL_LANE_PATH) if surfpool_binding["exists"] else {}
    boundaries = rehearsal_boundaries()
    scenarios = default_scenarios()
    scenario_results = [build_scenario_result(scenario) for scenario in scenarios]
    findings = collect_packet_findings(
        archive_doc,
        archive_binding,
        roadmap_text,
        roadmap_binding,
        surfpool_doc,
        surfpool_binding,
        boundaries,
        scenario_results,
    )
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "surfpool-localnet-external-beta-rehearsal-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": [REQUIRED_RELEASE_ARCHIVE_ISSUE, REQUIRED_ROADMAP_ISSUE],
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "rehearsalPacketId": "reddiagent-beta-0-surfpool-localnet-external-rehearsal",
        "sourceCommit": "fixture://surfpool-localnet-external-beta-rehearsal-packet",
        "inputs": {
            "releaseArchivePacket": {
                **archive_binding,
                "issue": archive_doc.get("issue"),
                "status": archive_doc.get("status"),
                "decision": archive_doc.get("decision"),
            },
            "agenticPaymentsRoadmap": {
                **roadmap_binding,
                "issue": REQUIRED_ROADMAP_ISSUE,
                "requiredTerms": list(REQUIRED_LOCALNET_TERMS),
            },
            "surfpoolValidatorLane": {
                **surfpool_binding,
                "issue": surfpool_doc.get("issue"),
                "status": surfpool_doc.get("status"),
                "preferred": surfpool_doc.get("validatorPreference", {}).get("preferred"),
                "fallback": surfpool_doc.get("validatorPreference", {}).get("fallback"),
            },
        },
        "setupAssumptions": {
            "environment": "Surfpool/localnet first, solana-test-validator fallback only if Surfpool is unavailable.",
            "endpoint": "loopback only: 127.0.0.1 or localhost.",
            "ledger": "resettable local ledger under .tmp; no reusable validator state.",
            "accounts": "fixture-funded tester principal, agent spender, and merchant service accounts only.",
            "mints": "fixture localnet mint rUSD-L only; no devnet/mainnet mint IDs.",
            "commandsAreIllustrative": True,
        },
        "acceptanceEvidence": {
            "localReviewerCanRun": [
                "python scripts/beta_surfpool_localnet_rehearsal_packet.py",
                "python tests/test_beta_surfpool_localnet_rehearsal_packet.py",
            ],
            "operatorAcceptance": decision == "localnet-rehearsal-ready" and not findings,
            "readyForDevnetGate": decision == "localnet-rehearsal-ready" and not findings,
            "devnetRequiresSeparateIssue": 360,
            "mainnetBlockedUntilAudit": True,
        },
        "scenarioSummary": {
            "positiveScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "pass"),
            "negativeScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail"),
            "failClosedScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail" and scenario["status"] == "fail"),
            "receiptScenarios": sum(1 for scenario in scenario_results if scenario["kind"] == "receipt"),
            "replayScenarios": sum(1 for scenario in scenario_results if scenario["kind"] == "replay"),
        },
        "scenarios": scenario_results,
        "decisionCriteria": {
            "localnet-rehearsal-ready": [
                "#355 archive packet is present, passing, archive-ready, and reviewer-ready.",
                "#356 roadmap packet is present and contains the localnet, authority, replay, receipt, rollback, and no-mainnet requirements.",
                "#248 Surfpool validator lane remains passing and static; #359 does not start Surfpool or a validator.",
                "Setup and delegated authority positive scenarios pass using localnet fixtures.",
                "Replay, over-cap, and receipt mismatch scenarios fail closed without receipt/settlement success.",
                "Rollback and kill-switch evidence is present for every scenario.",
                "All devnet/mainnet/wallet/payment/facilitator/settlement/live/provider/deployment/publishing boundaries remain false.",
            ],
            "hold": [
                "Use when any input, localnet fixture, authority, replay, receipt, rollback, or guardrail evidence is missing or stale.",
                "Do not move to #360 devnet tester gate until a replacement #359 packet is localnet-rehearsal-ready.",
            ],
            "rollback-required": [
                "Use only if localnet rehearsal was already accepted and a later devnet/audit gate invalidates it.",
                "Rollback target is the #355 archive-ready packet plus #356 roadmap before #359 acceptance; this script does not mutate runtime state.",
            ],
        },
        "operatorActions": {
            "localnet-rehearsal-ready": "Use this packet as deterministic local reviewer/operator evidence before opening the #360 devnet external tester gate.",
            "hold": "Keep the external beta lane on localnet; resolve findings before any devnet tester expansion.",
            "rollback-required": "Return to the #355 archive-ready release baseline and rerun the localnet rehearsal after fixing findings.",
        },
        "findings": findings,
        "boundaries": boundaries,
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
        "mainnetStatement": "This #359 rehearsal packet is localnet/local deterministic evidence only. It does not approve or run devnet/mainnet; mainnet remains blocked until official audit and go-live readiness.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for generated rehearsal packet JSON.")
    parser.add_argument(
        "--requested-decision",
        choices=("localnet-rehearsal-ready", "hold", "rollback-required"),
        help="Optional operator-requested decision override for hold/rollback dry-runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(requested_decision=args.requested_decision)
    rendered = dump_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
