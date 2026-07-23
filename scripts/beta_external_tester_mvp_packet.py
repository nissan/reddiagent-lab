#!/usr/bin/env python3
"""Build deterministic external tester MVP packet evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = 365
PARENT_EPIC = 220
REQUIRED_ISSUES = (359, 360, 361, 367)
LOCALNET_PACKET_PATH = "tests/fixtures/beta-surfpool-localnet-rehearsal-packet.json"
DEVNET_GATE_PATH = "tests/fixtures/beta-solana-devnet-external-tester-gate.json"
AUDIT_PREP_PATH = "tests/fixtures/rap-x402-ap2-audit-prep-alignment-packet.json"
ROADMAP_PATH = "docs/ROADMAP.md"
VISION_ROADMAP_PATH = "docs/REDDIAGENT-VISION-ROADMAP.md"
INDEX_PATH = "docs/INDEX.md"
README_PATH = "README.md"
REQUIRED_ROADMAP_TERMS = (
    "external tester MVP packet",
    "audit-readiness freeze/evidence",
    "official audit/go-live readiness",
    "Mainnet remains blocked",
)
REQUIRED_BOUNDARY_FALSE = (
    "externalTesterExecution",
    "liveRuntimeActivation",
    "hostedDeployment",
    "dockerSurfpoolCoolifyMutation",
    "credentialAccess",
    "liveMcpInvocation",
    "devnetRun",
    "mainnetRun",
    "walletPaymentFacilitatorSettlementAction",
    "packageArchivePublishing",
    "productionGatewayMutation",
    "providerApiAccess",
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


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def artifact_binding(path_text: str, *, issue: int | None = None) -> dict[str, Any]:
    path = ROOT / path_text
    binding: dict[str, Any] = {
        "path": path_text,
        "exists": path.exists() and path.is_file(),
        "sha256": digest_file(path) if path.exists() and path.is_file() else None,
        "sizeBytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }
    if issue is not None:
        binding["issue"] = issue
    return binding


def boundaries() -> dict[str, Any]:
    return {
        "deterministicPacketOnly": True,
        "consumesPriorEvidenceOnly": True,
        "laterBoundedExecutionDecisionRequired": True,
        "externalTesterExecution": False,
        "liveRuntimeActivation": False,
        "hostedDeployment": False,
        "dockerSurfpoolCoolifyMutation": False,
        "credentialAccess": False,
        "liveMcpInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "walletPaymentFacilitatorSettlementAction": False,
        "packageArchivePublishing": False,
        "productionGatewayMutation": False,
        "providerApiAccess": False,
        "externalSpend": False,
    }


def tester_mvp() -> dict[str, Any]:
    return {
        "cohort": {
            "name": "external-tester-mvp-cohort-0",
            "size": {"minimum": 3, "maximum": 5},
            "roles": ["builder", "operator", "protocol-reviewer"],
            "selectionCriteria": [
                "Has reviewed the localnet rehearsal packet.",
                "Can keep devnet and mainnet wallets separate.",
                "Can report receipt, authority, and rollback evidence without sharing secrets.",
            ],
            "expansionRequires": "fresh issue approval after successful cohort-0 closeout and audit-readiness freeze review",
        },
        "onboardingPacket": [
            "Start from the ADL v0.2 beta baseline and #359 Surfpool/localnet rehearsal.",
            "Read the #360 devnet gate before any later devnet execution is authorized.",
            "Acknowledge devnet-only labels and no-real-value expectations.",
            "Use a dedicated devnet wallet/key only if a later issue authorizes execution.",
            "Never import production keys, production wallets, or mainnet addresses.",
            "Use only allowlisted devnet mints/programs/payees from the gate packet.",
            "Accept tiny per-attempt, per-tester, and global cohort caps.",
            "Stop on any mainnet ambiguity, receipt mismatch, replay finding, or rollback evidence gap.",
        ],
        "support": {
            "coordinator": "tester coordinator",
            "engineeringEscalation": "RAP maintainer",
            "safetyOwner": "operator",
            "triageSla": "one business day for cohort-0 blockers",
            "pauseRule": "pause immediately on production key use, cap bypass, mainnet ambiguity, or payment/service/eval disagreement",
        },
        "feedbackCapture": {
            "channel": "GitHub issue template or private tester form",
            "requiredFields": [
                "tester role",
                "scenario id",
                "devnet-only acknowledgement",
                "wallet separation acknowledgement",
                "transaction signature or expected fail-closed code",
                "receipt id",
                "authority state",
                "service outcome",
                "eval outcome",
                "rollback evidence",
                "support request",
            ],
            "privacyRule": "capture public devnet identifiers and hashes only; never capture secrets, private keys, raw PII, or production wallet material",
        },
    }


def controls() -> dict[str, Any]:
    return {
        "labels": {
            "environment": "solana-devnet-only",
            "value": "no-real-value",
            "wallet": "dedicated-devnet-wallet-only",
            "mainnet": "mainnet-blocked-until-official-audit-and-go-live-readiness",
        },
        "walletKeySeparation": {
            "dedicatedDevnetWalletRequiredForFutureExecution": True,
            "productionKeyImportAllowed": False,
            "mainnetAddressAllowed": False,
            "repoStoresKeys": False,
            "cohortWalletReuseAllowed": False,
        },
        "caps": {
            "perAttemptMinorUnits": 100_000,
            "perTesterDailyMinorUnits": 300_000,
            "globalCohortMinorUnits": 1_500_000,
            "maxRetriesPerScenario": 1,
            "preSignCapCheckRequired": True,
            "preReceiptCapCheckRequired": True,
        },
        "allowlists": {
            "cluster": "devnet",
            "mints": ["DevnetMint111111111111111111111111111111111"],
            "programs": ["DevnetProgram111111111111111111111111111111"],
            "payees": ["DevnetMerchant111111111111111111111111111111"],
        },
        "evidenceBundle": [
            "tester roster and acknowledgements",
            "scenario run sheet",
            "devnet-only wallet/public-key attestations",
            "transaction or fail-closed diagnostic records",
            "authority state snapshots",
            "receipt/eval/dispute records",
            "rollback/kill-switch evidence",
            "coordinator closeout summary",
        ],
    }


def acceptance_matrix() -> dict[str, Any]:
    return {
        "accept": [
            "all cohort members acknowledge devnet-only/no-real-value boundaries",
            "all completed scenarios use only allowlisted mint/program/payee labels",
            "payment, service, eval, receipt, and dispute state agree for every positive case",
            "negative scenarios fail closed with rollback evidence",
            "no mainnet ambiguity appears in labels, wallet material, receipts, or support notes",
        ],
        "hold": [
            "tester cannot confirm wallet/key separation",
            "support queue contains unresolved coordinator blockers",
            "receipt or eval evidence is incomplete but no unsafe execution occurred",
            "cohort closeout finds unclear instructions that can be fixed before expansion",
        ],
        "rollbackRequired": [
            "mainnet wallet/address/key material appears anywhere in the packet or feedback",
            "cap bypass, replay acceptance, or wrong allowlist acceptance is observed",
            "payment-settled/service-failed is reported as success",
            "rollback/kill-switch evidence is missing after a failed or disputed case",
        ],
    }


def default_scenarios() -> list[dict[str, Any]]:
    common = {
        "labels": ["solana-devnet-only", "dedicated-devnet-wallet-only", "no-real-value"],
        "walletSeparation": {"dedicatedDevnetWallet": True, "productionKeyUsed": False, "mainnetAddressUsed": False},
        "allowlist": {"mintAllowed": True, "programAllowed": True, "payeeAllowed": True},
        "caps": {"amountMinorUnits": 75_000, "withinPerAttemptCap": True, "withinDailyCap": True, "withinGlobalCap": True},
        "receipt": {"present": True, "paymentStatus": "pass", "serviceOutcome": "pass", "evalOutcome": "pass", "disputeStatus": "clear"},
        "rollback": {"killSwitchArmed": True, "rollbackEvidencePresent": True},
        "boundaries": {"externalTesterExecuted": False, "devnetRunPerformed": False, "mainnetUsed": False, "realValueTransfer": False},
    }
    return [
        {
            "id": "cohort-onboarding-ready",
            "kind": "onboarding",
            "expectedStatus": "pass",
            "inputs": common,
        },
        {
            "id": "receipt-eval-dispute-ready",
            "kind": "receipt",
            "expectedStatus": "pass",
            "inputs": {**common, "receipt": {**common["receipt"], "disputeStatus": "clear"}},
        },
        {
            "id": "wallet-separation-missing",
            "kind": "wallet",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "walletSeparation": {"dedicatedDevnetWallet": False, "productionKeyUsed": False, "mainnetAddressUsed": False},
            },
        },
        {
            "id": "mainnet-ambiguity-denied",
            "kind": "mainnet-confusion",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "labels": ["solana-mainnet", "dedicated-devnet-wallet-only", "no-real-value"],
                "walletSeparation": {"dedicatedDevnetWallet": True, "productionKeyUsed": False, "mainnetAddressUsed": True},
                "boundaries": {**common["boundaries"], "mainnetUsed": True},
            },
        },
        {
            "id": "over-cap-denied",
            "kind": "caps",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "caps": {"amountMinorUnits": 150_000, "withinPerAttemptCap": False, "withinDailyCap": True, "withinGlobalCap": True},
            },
        },
        {
            "id": "wrong-allowlist-denied",
            "kind": "allowlist",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "allowlist": {"mintAllowed": False, "programAllowed": True, "payeeAllowed": False},
            },
        },
        {
            "id": "payment-settled-service-failed-denied",
            "kind": "atomicity",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "receipt": {**common["receipt"], "paymentStatus": "pass", "serviceOutcome": "fail", "evalOutcome": "pass"},
                "rollback": {"killSwitchArmed": True, "rollbackEvidencePresent": True},
            },
        },
        {
            "id": "rollback-evidence-missing-denied",
            "kind": "rollback",
            "expectedStatus": "fail",
            "inputs": {
                **common,
                "receipt": {**common["receipt"], "disputeStatus": "needs-review"},
                "rollback": {"killSwitchArmed": True, "rollbackEvidencePresent": False},
            },
        },
    ]


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    inputs = scenario["inputs"]
    findings: list[dict[str, str]] = []
    labels = inputs["labels"]
    wallet = inputs["walletSeparation"]
    allowlist = inputs["allowlist"]
    caps = inputs["caps"]
    receipt = inputs["receipt"]
    rollback = inputs["rollback"]
    boundary_doc = inputs["boundaries"]

    if "solana-devnet-only" not in labels:
        findings.append(finding(f"scenarios.{scenario['id']}.labels.solana-devnet-only", "External tester packet must be devnet-only labeled."))
    if wallet["dedicatedDevnetWallet"] is not True:
        findings.append(finding(f"scenarios.{scenario['id']}.walletSeparation.dedicatedDevnetWallet", "Dedicated devnet wallet/key separation is required."))
    if wallet["productionKeyUsed"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.walletSeparation.productionKeyUsed", "Production keys are never allowed."))
    if wallet["mainnetAddressUsed"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.walletSeparation.mainnetAddressUsed", "Mainnet addresses are never allowed in tester evidence."))
    for key in ("mintAllowed", "programAllowed", "payeeAllowed"):
        if allowlist[key] is not True:
            findings.append(finding(f"scenarios.{scenario['id']}.allowlist.{key}", "Mint, program, and payee must be allowlisted."))
    for key in ("withinPerAttemptCap", "withinDailyCap", "withinGlobalCap"):
        if caps[key] is not True:
            findings.append(finding(f"scenarios.{scenario['id']}.caps.{key}", "Tiny test caps must hold before signing and receipt completion."))
    if receipt["present"] is not True:
        findings.append(finding(f"scenarios.{scenario['id']}.receipt.present", "Receipt evidence is required for completed positive cases."))
    if receipt["paymentStatus"] != "pass" or receipt["serviceOutcome"] != "pass" or receipt["evalOutcome"] != "pass":
        findings.append(finding(f"scenarios.{scenario['id']}.receipt.atomicity", "Payment, service, and eval must all pass before success."))
    if receipt["disputeStatus"] not in ("clear", "needs-review"):
        findings.append(finding(f"scenarios.{scenario['id']}.receipt.disputeStatus", "Dispute state must be explicit."))
    if receipt["disputeStatus"] != "clear" and rollback["rollbackEvidencePresent"] is not True:
        findings.append(finding(f"scenarios.{scenario['id']}.rollback.rollbackEvidencePresent", "Disputed or failed cases require rollback evidence."))
    if rollback["killSwitchArmed"] is not True:
        findings.append(finding(f"scenarios.{scenario['id']}.rollback.killSwitchArmed", "Kill switch must remain armed."))
    if boundary_doc["externalTesterExecuted"] is True or boundary_doc["devnetRunPerformed"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.boundaries.externalTesterExecuted", "This packet cannot authorize or record external tester execution."))
    if boundary_doc["mainnetUsed"] is True or boundary_doc["realValueTransfer"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.boundaries.mainnetUsed", "Mainnet or real-value transfer is blocked."))
    return findings


def build_scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    status = "pass" if not findings else "fail"
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "expectedStatus": scenario["expectedStatus"],
        "status": status,
        "findings": findings,
        "inputs": scenario["inputs"],
    }


def collect_packet_findings(
    artifacts: dict[str, dict[str, Any]],
    roadmap_texts: dict[str, str],
    localnet_doc: dict[str, Any],
    devnet_doc: dict[str, Any],
    audit_doc: dict[str, Any],
    boundary_doc: dict[str, Any],
    mvp_doc: dict[str, Any],
    control_doc: dict[str, Any],
    matrix_doc: dict[str, Any],
    scenario_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for name, artifact in artifacts.items():
        if not artifact["exists"] or not artifact["sha256"] or not artifact["sizeBytes"]:
            findings.append(finding(f"artifacts.{name}", "Required upstream artifact binding is missing."))

    combined_roadmap = normalized_text("\n".join(roadmap_texts.values()))
    for term in REQUIRED_ROADMAP_TERMS:
        if normalized_text(term) not in combined_roadmap:
            findings.append(finding("roadmap.requiredTerms", f"Missing accepted ladder term: {term}."))

    if localnet_doc.get("decision") != "localnet-rehearsal-ready":
        findings.append(finding("localnet.decision", "Localnet rehearsal must be ready before tester MVP packet."))
    if devnet_doc.get("decision") != "devnet-tester-gate-ready":
        findings.append(finding("devnet.decision", "Devnet tester gate must be ready before tester MVP packet."))
    if audit_doc.get("decision") != "audit-prep-ready":
        findings.append(finding("auditPrep.decision", "RAP x402/AP2 audit prep must be ready before tester MVP packet."))
    if devnet_doc.get("controls", {}).get("walletSeparation", {}).get("productionKeyImportAllowed") is not False:
        findings.append(finding("devnet.controls.walletSeparation.productionKeyImportAllowed", "Devnet gate must block production key import."))
    if devnet_doc.get("controls", {}).get("allowlists", {}).get("cluster") != "devnet":
        findings.append(finding("devnet.controls.allowlists.cluster", "Devnet gate must remain cluster-scoped to devnet."))
    if audit_doc.get("auditDeltas", {}).get("rollbackKillSwitch", {}).get("readyWhen") is None:
        findings.append(finding("auditPrep.auditDeltas.rollbackKillSwitch", "Audit prep must preserve rollback/kill-switch readiness."))

    if mvp_doc["cohort"]["size"] != {"minimum": 3, "maximum": 5}:
        findings.append(finding("testerMvp.cohort.size", "Cohort-0 must stay small and bounded."))
    if "successful cohort-0 closeout" not in mvp_doc["cohort"]["expansionRequires"]:
        findings.append(finding("testerMvp.cohort.expansionRequires", "Expansion requires later closeout and approval."))
    if len(mvp_doc["onboardingPacket"]) < 8:
        findings.append(finding("testerMvp.onboardingPacket", "Onboarding packet is incomplete."))
    if "transaction signature or expected fail-closed code" not in mvp_doc["feedbackCapture"]["requiredFields"]:
        findings.append(finding("testerMvp.feedbackCapture.requiredFields", "Feedback capture must include receipt/fail-closed evidence."))

    if control_doc["walletKeySeparation"]["productionKeyImportAllowed"] is not False:
        findings.append(finding("controls.walletKeySeparation.productionKeyImportAllowed", "Production keys must be blocked."))
    if control_doc["allowlists"]["cluster"] != "devnet":
        findings.append(finding("controls.allowlists.cluster", "Allowlists must be devnet-scoped."))
    if control_doc["caps"]["perAttemptMinorUnits"] > 100_000:
        findings.append(finding("controls.caps.perAttemptMinorUnits", "Per-attempt cap must stay tiny."))
    if "rollback/kill-switch evidence" not in control_doc["evidenceBundle"]:
        findings.append(finding("controls.evidenceBundle", "Evidence bundle must include rollback evidence."))

    for key in ("accept", "hold", "rollbackRequired"):
        if not matrix_doc.get(key):
            findings.append(finding(f"acceptanceMatrix.{key}", "Acceptance, hold, and rollback criteria are required."))

    for flag in REQUIRED_BOUNDARY_FALSE:
        if boundary_doc.get(flag) is not False:
            findings.append(finding(f"boundaries.{flag}", "External tester MVP packet must preserve no-live-action boundary."))

    for scenario in scenario_results:
        if scenario["status"] != scenario["expectedStatus"]:
            findings.append(finding(f"scenarios.{scenario['id']}.status", "Scenario did not match expected pass/fail status."))
        if scenario["expectedStatus"] == "fail" and not scenario["findings"]:
            findings.append(finding(f"scenarios.{scenario['id']}.findings", "Negative scenario must include fail-closed findings."))

    return findings


def decision_for(findings: list[dict[str, str]], requested_decision: str) -> str:
    if findings:
        return "hold"
    return requested_decision


def build_packet(requested_decision: str) -> dict[str, Any]:
    artifacts = {
        "localnetRehearsal": artifact_binding(LOCALNET_PACKET_PATH, issue=359),
        "devnetTesterGate": artifact_binding(DEVNET_GATE_PATH, issue=360),
        "rapX402Ap2AuditPrep": artifact_binding(AUDIT_PREP_PATH, issue=361),
        "roadmap": artifact_binding(ROADMAP_PATH, issue=367),
        "visionRoadmap": artifact_binding(VISION_ROADMAP_PATH, issue=367),
        "docsIndex": artifact_binding(INDEX_PATH, issue=367),
        "readme": artifact_binding(README_PATH, issue=367),
    }
    roadmap_texts = {
        "roadmap": (ROOT / ROADMAP_PATH).read_text(encoding="utf-8"),
        "visionRoadmap": (ROOT / VISION_ROADMAP_PATH).read_text(encoding="utf-8"),
        "docsIndex": (ROOT / INDEX_PATH).read_text(encoding="utf-8"),
        "readme": (ROOT / README_PATH).read_text(encoding="utf-8"),
    }
    localnet_doc = load_json(ROOT / LOCALNET_PACKET_PATH)
    devnet_doc = load_json(ROOT / DEVNET_GATE_PATH)
    audit_doc = load_json(ROOT / AUDIT_PREP_PATH)
    boundary_doc = boundaries()
    mvp_doc = tester_mvp()
    control_doc = controls()
    matrix_doc = acceptance_matrix()
    scenario_results = [build_scenario_result(scenario) for scenario in default_scenarios()]
    findings = collect_packet_findings(
        artifacts,
        roadmap_texts,
        localnet_doc,
        devnet_doc,
        audit_doc,
        boundary_doc,
        mvp_doc,
        control_doc,
        matrix_doc,
        scenario_results,
    )
    return {
        "mode": "external-tester-mvp-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": list(REQUIRED_ISSUES),
        "status": "pass" if not findings else "fail",
        "decision": decision_for(findings, requested_decision),
        "packetId": "reddiagent-external-tester-mvp-cohort-0-packet",
        "mainnetStatement": "Mainnet remains blocked until official audit completion and explicit go-live readiness.",
        "executionStatement": "This packet does not authorize external tester execution; a later bounded issue must approve any live/devnet cohort run.",
        "artifacts": artifacts,
        "testerMvp": mvp_doc,
        "controls": control_doc,
        "acceptanceMatrix": matrix_doc,
        "scenarioSummary": {
            "positiveScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "pass"),
            "negativeScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail"),
            "failClosedScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail" and scenario["status"] == "fail"),
            "rollbackScenarios": sum(1 for scenario in scenario_results if scenario["kind"] in ("rollback", "atomicity")),
            "mainnetAmbiguityScenarios": sum(1 for scenario in scenario_results if scenario["kind"] == "mainnet-confusion"),
        },
        "scenarios": scenario_results,
        "boundaries": boundary_doc,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requested-decision",
        choices=("mvp-packet-ready", "hold", "rollback-required"),
        default="mvp-packet-ready",
    )
    args = parser.parse_args()
    packet = build_packet(args.requested_decision)
    print(dump_json(packet), end="")
    return 0 if packet["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
