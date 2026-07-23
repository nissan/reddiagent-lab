#!/usr/bin/env python3
"""Build deterministic Solana devnet external tester gate design evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCALNET_REHEARSAL_PATH = "tests/fixtures/beta-surfpool-localnet-rehearsal-packet.json"
ROADMAP_PACKET_PATH = "research/2026-07-23-agentic-payments-roadmap-recalibration.md"
CURRENT_ISSUE = 360
PARENT_EPIC = 220
REQUIRED_LOCALNET_REHEARSAL_ISSUE = 359
REQUIRED_ROADMAP_ISSUE = 356
REQUIRED_TERMS = (
    "Solana devnet external tester gate",
    "devnet-only labels",
    "test wallet separation",
    "allowlisted mints/programs",
    "confirmation/settlement proof",
    "payment-settled/service-failed",
    "no mainnet",
)
REQUIRED_BOUNDARY_FALSE = (
    "devnetExecution",
    "mainnetAccess",
    "productionCredentialAccess",
    "realValueWalletAccess",
    "facilitatorAction",
    "settlementAction",
    "hostedDeployment",
    "packagePublished",
    "productionGatewayMutation",
    "runtimeActivation",
    "providerApiAccess",
    "mcpInvocation",
    "externalSpend",
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


def gate_boundaries() -> dict[str, Any]:
    return {
        "deterministicDevnetGateDesign": True,
        "consumesLocalnetAndRoadmapOnly": True,
        "externalTesterGateDesignOnly": True,
        "devnetExecution": False,
        "mainnetAccess": False,
        "productionCredentialAccess": False,
        "realValueWalletAccess": False,
        "facilitatorAction": False,
        "settlementAction": False,
        "hostedDeployment": False,
        "packagePublished": False,
        "productionGatewayMutation": False,
        "runtimeActivation": False,
        "providerApiAccess": False,
        "mcpInvocation": False,
        "externalSpend": False,
    }


def tester_gate() -> dict[str, Any]:
    return {
        "cohort": {
            "name": "devnet-external-feedback-cohort-0",
            "size": {"minimum": 3, "maximum": 5},
            "roles": ["builder", "protocol-reviewer", "operator"],
            "eligibility": [
                "Can run a local receipt/authority walkthrough first.",
                "Understands devnet has no monetary value.",
                "Agrees to file issue-template feedback with transaction and receipt evidence.",
            ],
            "expansionRequires": "successful cohort-0 closeout plus fresh implementation issue approval",
        },
        "onboardingChecklist": [
            "Read the devnet-only warning and confirm no mainnet wallet/address is used.",
            "Create or select a dedicated devnet wallet/keypair for this test only.",
            "Fund only the devnet wallet from a devnet faucet; never import production keys.",
            "Use only the allowlisted devnet mint and program labels in this packet.",
            "Run localnet rehearsal evidence review before any future devnet implementation run.",
            "Acknowledge tiny per-tester and per-attempt caps before signing anything.",
        ],
        "feedbackLoop": {
            "channel": "GitHub issue template or private tester form",
            "requiredFields": [
                "tester role",
                "devnet wallet public key",
                "scenario id",
                "transaction signature or expected fail-closed code",
                "receipt id",
                "authority state",
                "support needed",
            ],
            "triageSla": "one business day for cohort-0 blockers",
            "closeout": "summarize confusion, failed confirmations, receipt gaps, and rollback evidence before expansion",
        },
        "supportPath": {
            "firstLine": "tester coordinator",
            "engineeringEscalation": "RAP maintainer",
            "killSwitchOwner": "operator",
            "rollbackOwner": "operator",
            "incidentRule": "pause the cohort on any mainnet ambiguity, production key use, cap bypass, or receipt/proof mismatch",
        },
    }


def controls() -> dict[str, Any]:
    return {
        "labels": {
            "environment": "solana-devnet-only",
            "wallet": "dedicated-devnet-wallet-only",
            "value": "no-real-value",
            "mainnet": "mainnet-blocked-until-audit",
        },
        "walletSeparation": {
            "devnetWalletRequired": True,
            "productionKeyImportAllowed": False,
            "mainnetAddressAllowed": False,
            "perTesterWalletReuseAcrossCohort": False,
            "keyStorage": "tester-managed devnet key only; repo stores no secrets",
        },
        "caps": {
            "perAttemptMinorUnits": 100_000,
            "perTesterDailyMinorUnits": 300_000,
            "globalCohortMinorUnits": 1_500_000,
            "maxRetriesPerScenario": 1,
            "capEnforcedBeforeSigning": True,
            "capRecheckedBeforeReceipt": True,
        },
        "allowlists": {
            "cluster": "devnet",
            "mints": [{"symbol": "rUSD-D", "mint": "DevnetMint111111111111111111111111111111111", "decimals": 6}],
            "programs": [{"name": "reddiagent-devnet-gate", "programId": "DevnetProgram111111111111111111111111111111"}],
            "payees": [{"name": "merchant-service-devnet", "address": "DevnetMerchant111111111111111111111111111111"}],
        },
        "proofRequirements": {
            "transactionLanding": ["signature", "slot", "blockTime", "err"],
            "confirmation": {"minimumCommitment": "confirmed", "finalizedRequiredForCloseout": True},
            "receipt": [
                "receiptId",
                "requestHash",
                "responseHash",
                "mandateId",
                "devnetSignature",
                "confirmationStatus",
                "serviceOutcome",
                "evalStatus",
            ],
            "authorityState": ["principal", "spender", "payee", "mint", "programId", "cap", "expirySlot", "nonce", "revoked"],
            "rollbackEvidence": ["killSwitchState", "mandateRevocation", "cohortPause", "receiptMarkedForReview"],
        },
    }


def default_scenarios() -> list[dict[str, Any]]:
    base_authority = {
        "mandateId": "mandate-devnet-cohort0-001",
        "principal": "tester-devnet-wallet-001",
        "spender": "agent-devnet-spender-001",
        "payee": "DevnetMerchant111111111111111111111111111111",
        "mint": "DevnetMint111111111111111111111111111111111",
        "programId": "DevnetProgram111111111111111111111111111111",
        "capMinorUnits": 100_000,
        "expiresSlot": 50_000,
        "nonce": "devnet-nonce-001",
        "revoked": False,
    }
    base_boundary = {
        "cluster": "devnet",
        "devnetOnly": True,
        "mainnetUsed": False,
        "productionKeyUsed": False,
        "realValueTransfer": False,
        "facilitatorUsed": False,
        "settlementActionPerformed": False,
    }
    return [
        {
            "id": "devnet-onboarding-ready",
            "kind": "onboarding",
            "expectedStatus": "pass",
            "tester": {"role": "builder", "cohort": "devnet-external-feedback-cohort-0", "wallet": "tester-devnet-wallet-001"},
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": base_authority,
            "transaction": {"signature": "devnet-sig-onboarding-ready", "slot": 49_000, "err": None, "confirmationStatus": "confirmed"},
            "receipt": {"receiptId": "receipt-devnet-onboarding-ready", "settlementProof": "devnet-signature-only", "serviceOutcome": "pass", "evalStatus": "pass"},
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "devnet-confirmation-and-receipt-pass",
            "kind": "confirmation",
            "expectedStatus": "pass",
            "tester": {"role": "protocol-reviewer", "cohort": "devnet-external-feedback-cohort-0", "wallet": "tester-devnet-wallet-002"},
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "principal": "tester-devnet-wallet-002", "nonce": "devnet-nonce-002"},
            "attempt": {"amountMinorUnits": 75_000, "slot": 49_100, "purpose": "paid-data-receipt-review"},
            "transaction": {"signature": "devnet-sig-confirmation-pass", "slot": 49_101, "err": None, "confirmationStatus": "confirmed"},
            "receipt": {"receiptId": "receipt-devnet-confirmation-pass", "settlementProof": "devnet-signature-only", "serviceOutcome": "pass", "evalStatus": "pass"},
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "expired-mandate-denied",
            "kind": "authority",
            "expectedStatus": "fail",
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "nonce": "devnet-nonce-expired-001", "expiresSlot": 49_999},
            "attempt": {"amountMinorUnits": 50_000, "slot": 50_001, "purpose": "paid-data-receipt-review"},
            "transaction": None,
            "receipt": None,
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "replayed-request-denied",
            "kind": "replay",
            "expectedStatus": "fail",
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "nonce": "devnet-nonce-002"},
            "attempt": {"amountMinorUnits": 75_000, "slot": 49_200, "purpose": "paid-data-receipt-review"},
            "replay": {"previousNonceSeen": True, "previousReceiptId": "receipt-devnet-confirmation-pass"},
            "transaction": None,
            "receipt": None,
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "over-budget-denied",
            "kind": "budget",
            "expectedStatus": "fail",
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "nonce": "devnet-nonce-over-budget-001"},
            "attempt": {"amountMinorUnits": 150_000, "slot": 49_250, "purpose": "paid-data-receipt-review"},
            "transaction": None,
            "receipt": None,
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "wrong-mint-program-denied",
            "kind": "allowlist",
            "expectedStatus": "fail",
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "mint": "WrongMint111111111111111111111111111111111", "programId": "WrongProgram111111111111111111111111111111", "nonce": "devnet-nonce-wrong-001"},
            "attempt": {"amountMinorUnits": 50_000, "slot": 49_300, "purpose": "paid-data-receipt-review"},
            "transaction": None,
            "receipt": None,
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True},
            "boundaries": base_boundary,
        },
        {
            "id": "payment-settled-service-failed-denied",
            "kind": "atomicity",
            "expectedStatus": "fail",
            "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
            "authority": {**base_authority, "nonce": "devnet-nonce-atomicity-001"},
            "attempt": {"amountMinorUnits": 60_000, "slot": 49_400, "purpose": "a2a-service-outcome-bundle"},
            "transaction": {"signature": "devnet-sig-payment-settled-service-failed", "slot": 49_401, "err": None, "confirmationStatus": "confirmed"},
            "receipt": {"receiptId": "receipt-devnet-atomicity-denied", "settlementProof": "devnet-signature-only", "serviceOutcome": "fail", "evalStatus": "fail"},
            "rollback": {"killSwitchState": "armed", "mandateRevocationTested": True, "cohortPauseAvailable": True, "receiptMarkedForReview": True},
            "boundaries": base_boundary,
        },
    ]


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    scenario_id = scenario.get("id")
    authority = scenario.get("authority", {})
    attempt = scenario.get("attempt", {})
    receipt = scenario.get("receipt")
    transaction = scenario.get("transaction")
    rollback = scenario.get("rollback", {})
    boundaries = scenario.get("boundaries", {})
    labels = set(scenario.get("labels", []))
    allowlists = controls()["allowlists"]
    caps = controls()["caps"]

    for required_label in ("solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"):
        require(required_label in labels, f"scenarios.{scenario_id}.labels.{required_label}", "Required devnet-only tester label is missing.")
    require(boundaries.get("cluster") == "devnet", f"scenarios.{scenario_id}.boundaries.cluster", "Scenario must be labelled devnet.")
    require(boundaries.get("devnetOnly") is True, f"scenarios.{scenario_id}.boundaries.devnetOnly", "Scenario must be devnet-only.")
    for key in ("mainnetUsed", "productionKeyUsed", "realValueTransfer", "facilitatorUsed", "settlementActionPerformed"):
        require(boundaries.get(key) is False, f"scenarios.{scenario_id}.boundaries.{key}", f"{key} must be false.")
    require(rollback.get("killSwitchState") == "armed", f"scenarios.{scenario_id}.rollback.killSwitchState", "Kill switch must be armed.")
    require(rollback.get("mandateRevocationTested") is True, f"scenarios.{scenario_id}.rollback.mandateRevocationTested", "Rollback must include mandate revocation evidence.")
    require(rollback.get("cohortPauseAvailable") is True, f"scenarios.{scenario_id}.rollback.cohortPauseAvailable", "Rollback must include cohort pause evidence.")

    require(authority.get("mandateId") == "mandate-devnet-cohort0-001", f"scenarios.{scenario_id}.authority.mandateId", "Authority must bind to the cohort-0 mandate.")
    require(authority.get("payee") in {payee["address"] for payee in allowlists["payees"]}, f"scenarios.{scenario_id}.authority.payee", "Payee must be allowlisted.")
    require(authority.get("mint") in {mint["mint"] for mint in allowlists["mints"]}, f"scenarios.{scenario_id}.authority.mint", "Mint must be allowlisted.")
    require(authority.get("programId") in {program["programId"] for program in allowlists["programs"]}, f"scenarios.{scenario_id}.authority.programId", "Program must be allowlisted.")

    if attempt:
        require(attempt.get("amountMinorUnits", 0) <= caps["perAttemptMinorUnits"], f"scenarios.{scenario_id}.attempt.amountMinorUnits", "Attempt exceeds tiny devnet cap.")
        require(attempt.get("slot", 0) < authority.get("expiresSlot", -1), f"scenarios.{scenario_id}.attempt.slot", "Attempt is after authority expiry.")

    replay = scenario.get("replay", {})
    require(replay.get("previousNonceSeen") is not True, f"scenarios.{scenario_id}.replay.previousNonceSeen", "Replayed request must fail closed.")

    if scenario.get("expectedStatus") == "pass":
        require(isinstance(transaction, dict), f"scenarios.{scenario_id}.transaction", "Passing scenario requires transaction landing evidence.")
        require(isinstance(receipt, dict), f"scenarios.{scenario_id}.receipt", "Passing scenario requires receipt evidence.")
    if isinstance(transaction, dict):
        require(transaction.get("err") is None, f"scenarios.{scenario_id}.transaction.err", "Landing evidence must have no transaction error.")
        require(transaction.get("confirmationStatus") in {"confirmed", "finalized"}, f"scenarios.{scenario_id}.transaction.confirmationStatus", "Confirmation must be confirmed or finalized.")
    if isinstance(receipt, dict):
        require(receipt.get("settlementProof") == "devnet-signature-only", f"scenarios.{scenario_id}.receipt.settlementProof", "Receipt settlement proof must be devnet-labelled.")
        require(receipt.get("serviceOutcome") == "pass", f"scenarios.{scenario_id}.receipt.serviceOutcome", "Receipt cannot claim success when service failed.")
        require(receipt.get("evalStatus") == "pass", f"scenarios.{scenario_id}.receipt.evalStatus", "Receipt cannot claim success when eval failed.")

    return findings


def build_scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    status = "pass" if not findings else "fail"
    trace_id = stable_id("issue-360", scenario.get("id", ""), scenario.get("kind", ""))
    return {
        "id": scenario.get("id"),
        "kind": scenario.get("kind"),
        "expectedStatus": scenario.get("expectedStatus"),
        "status": status,
        "traceId": trace_id,
        "authorityRef": scenario.get("authority", {}).get("mandateId"),
        "receiptRef": scenario.get("receipt", {}).get("receiptId") if isinstance(scenario.get("receipt"), dict) else None,
        "inputs": {
            "tester": scenario.get("tester"),
            "labels": scenario.get("labels", []),
            "authority": scenario.get("authority"),
            "attempt": scenario.get("attempt"),
            "replay": scenario.get("replay"),
            "transaction": scenario.get("transaction"),
            "receipt": scenario.get("receipt"),
            "rollback": scenario.get("rollback"),
            "boundaries": scenario.get("boundaries"),
        },
        "findings": findings,
    }


def collect_packet_findings(
    rehearsal_doc: dict[str, Any],
    rehearsal_binding: dict[str, Any],
    roadmap_text: str,
    roadmap_binding: dict[str, Any],
    boundaries: dict[str, Any],
    scenario_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    for name, binding in {"localnetRehearsalPacket": rehearsal_binding, "roadmapPacket": roadmap_binding}.items():
        require(binding.get("exists") is True, f"{name}.exists", "Required input artifact must exist.")
        require(bool(binding.get("sha256")), f"{name}.sha256", "Required input artifact must be pinned by sha256.")
        require(bool(binding.get("sizeBytes")), f"{name}.sizeBytes", "Required input artifact must have a byte size.")

    require(rehearsal_doc.get("issue") == REQUIRED_LOCALNET_REHEARSAL_ISSUE, "localnetRehearsalPacket.issue", "Must consume #359 localnet rehearsal packet.")
    require(rehearsal_doc.get("status") == "pass", "localnetRehearsalPacket.status", "#359 localnet rehearsal packet must pass.")
    require(rehearsal_doc.get("decision") == "localnet-rehearsal-ready", "localnetRehearsalPacket.decision", "#359 localnet rehearsal must be ready.")
    require(rehearsal_doc.get("acceptanceEvidence", {}).get("readyForDevnetGate") is True, "localnetRehearsalPacket.acceptanceEvidence.readyForDevnetGate", "#359 must explicitly allow #360 gate design.")
    require(rehearsal_doc.get("boundaries", {}).get("devnetAccess") is False, "localnetRehearsalPacket.boundaries.devnetAccess", "#359 must not have touched devnet.")
    require(rehearsal_doc.get("boundaries", {}).get("mainnetAccess") is False, "localnetRehearsalPacket.boundaries.mainnetAccess", "#359 must not have touched mainnet.")

    for term in REQUIRED_TERMS:
        require(term.lower() in roadmap_text.lower(), f"roadmapPacket.term.{term}", f"#356 roadmap must mention {term}.")
    require("## Practical Release Ladder" in roadmap_text, "roadmapPacket.Practical Release Ladder", "#356 roadmap ladder is required.")
    require("## Audit Prep Deltas" in roadmap_text, "roadmapPacket.Audit Prep Deltas", "#356 audit-prep deltas are required.")

    for key in ("deterministicDevnetGateDesign", "consumesLocalnetAndRoadmapOnly", "externalTesterGateDesignOnly"):
        require(boundaries.get(key) is True, f"boundaries.{key}", f"{key} must be true.")
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"{key} must be false.")

    positive = [scenario for scenario in scenario_results if scenario["expectedStatus"] == "pass"]
    negative = [scenario for scenario in scenario_results if scenario["expectedStatus"] == "fail"]
    require(len(positive) >= 2, "scenarios.positive", "Onboarding and confirmation positive scenarios are required.")
    require(len(negative) >= 5, "scenarios.negative", "Expired, replay, over-budget, wrong mint/program, and atomicity failure scenarios are required.")
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
    return "devnet-tester-gate-ready"


def build_report(requested_decision: str | None = None) -> dict[str, Any]:
    rehearsal_binding = artifact_binding(LOCALNET_REHEARSAL_PATH)
    roadmap_binding = artifact_binding(ROADMAP_PACKET_PATH)
    rehearsal_doc = load_json(ROOT / LOCALNET_REHEARSAL_PATH) if rehearsal_binding["exists"] else {}
    roadmap_text = (ROOT / ROADMAP_PACKET_PATH).read_text(encoding="utf-8") if roadmap_binding["exists"] else ""
    boundaries = gate_boundaries()
    scenario_results = [build_scenario_result(scenario) for scenario in default_scenarios()]
    findings = collect_packet_findings(rehearsal_doc, rehearsal_binding, roadmap_text, roadmap_binding, boundaries, scenario_results)
    decision = decision_for(findings, requested_decision)
    return {
        "mode": "solana-devnet-external-tester-gate-design",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": [REQUIRED_LOCALNET_REHEARSAL_ISSUE, REQUIRED_ROADMAP_ISSUE],
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "gateId": "reddiagent-beta-0-solana-devnet-external-tester-gate",
        "sourceCommit": "fixture://solana-devnet-external-tester-gate",
        "inputs": {
            "localnetRehearsalPacket": {
                **rehearsal_binding,
                "issue": rehearsal_doc.get("issue"),
                "status": rehearsal_doc.get("status"),
                "decision": rehearsal_doc.get("decision"),
            },
            "agenticPaymentsRoadmap": {
                **roadmap_binding,
                "issue": REQUIRED_ROADMAP_ISSUE,
                "requiredTerms": list(REQUIRED_TERMS),
            },
        },
        "testerGate": tester_gate(),
        "controls": controls(),
        "scenarioSummary": {
            "positiveScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "pass"),
            "negativeScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail"),
            "failClosedScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail" and scenario["status"] == "fail"),
            "rollbackScenarios": sum(1 for scenario in scenario_results if scenario["inputs"]["rollback"]["killSwitchState"] == "armed"),
            "receiptProofScenarios": sum(1 for scenario in scenario_results if isinstance(scenario["inputs"]["receipt"], dict)),
        },
        "scenarios": scenario_results,
        "decisionCriteria": {
            "devnet-tester-gate-ready": [
                "#359 localnet rehearsal is passing and explicitly ready for #360.",
                "#356 roadmap supports devnet external tester gate requirements and no-mainnet guardrails.",
                "Cohort scope, onboarding, feedback loop, and support path are explicit.",
                "Devnet-only labels, wallet/key separation, tiny caps, allowlisted mints/programs, confirmation proof, receipt proof, authority state, and rollback evidence are defined.",
                "Expired mandate, replay, over-budget, wrong mint/program, and payment-settled/service-failed scenarios fail closed.",
                "This gate remains design-only; no devnet execution or live settlement occurs in #360.",
            ],
            "hold": [
                "Use when any localnet input, roadmap input, tester workflow, control, proof, rollback, or fail-closed scenario is missing.",
                "Do not create implementation/devnet-run work until the design gate is ready and separately scoped.",
            ],
            "rollback-required": [
                "Use only if a later implementation gate invalidates the devnet tester design.",
                "Rollback target is #359 localnet rehearsal plus #356 roadmap; this script mutates no runtime state.",
            ],
        },
        "operatorActions": {
            "devnet-tester-gate-ready": "Use this packet as the design handoff for a later explicitly scoped devnet tester implementation issue.",
            "hold": "Keep the lane at #360 design; resolve findings before any implementation/devnet execution scope.",
            "rollback-required": "Return to #359 localnet rehearsal evidence and revise the devnet design before implementation.",
        },
        "boundaries": boundaries,
        "findings": findings,
        "mainnetStatement": "This packet designs a bounded devnet external tester gate only. It does not approve or run devnet/mainnet; mainnet remains blocked until official audit and go-live readiness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated devnet tester gate JSON.")
    parser.add_argument("--requested-decision", choices=("hold", "rollback-required"), help="Force an operator decision for rehearsal.")
    args = parser.parse_args()
    payload = dump_json(build_report(args.requested_decision))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
