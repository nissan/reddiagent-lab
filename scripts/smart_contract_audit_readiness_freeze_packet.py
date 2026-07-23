#!/usr/bin/env python3
"""Build deterministic smart-contract audit-readiness freeze evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = 366
PARENT_EPIC = 220
REQUIRED_ISSUES = (361, 365)
AUDIT_PREP_PATH = "tests/fixtures/rap-x402-ap2-audit-prep-alignment-packet.json"
TESTER_MVP_PATH = "tests/fixtures/beta-external-tester-mvp-packet.json"
ROADMAP_PATH = "docs/ROADMAP.md"
README_PATH = "README.md"
REQUIRED_BOUNDARY_FALSE = (
    "smartContractDeployment",
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
    "externalTesterExecution",
    "externalSpend",
)
FREEZE_AREAS = (
    "paymentCapableInvariants",
    "solanaProgramMintAllowlists",
    "authorityMandateBinding",
    "replayIdempotency",
    "receiptSettlementProof",
    "privacyPii",
    "rollbackKillSwitch",
    "disputeReputation",
)
REQUIRED_EVIDENCE = (
    "deterministic tests",
    "localnet gate artifact",
    "devnet gate artifact",
    "threat model",
    "invariant checklist",
    "known limitations",
    "no-mainnet boundary proof",
)
REQUIRED_BLOCKERS = (
    "unaudited contracts/programs",
    "unclear authority",
    "stale/replayed mandates",
    "devnet/mainnet ambiguity",
    "unbounded spend",
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


def normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def boundaries() -> dict[str, Any]:
    return {
        "deterministicPacketOnly": True,
        "consumesPriorEvidenceOnly": True,
        "officialAuditRequiredBeforePaymentCapablePublicBeta": True,
        "explicitGoLiveReadinessRequired": True,
        "smartContractDeployment": False,
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
        "externalTesterExecution": False,
        "externalSpend": False,
    }


def freeze_checklist() -> dict[str, dict[str, Any]]:
    return {
        "paymentCapableInvariants": {
            "criteria": [
                "ADL/RAP success requires authority, resource access, payment evidence, settlement proof, service result, eval result, and dispute state to agree.",
                "Payment-settled/service-failed and payment-settled/eval-failed paths never emit success or positive reputation.",
            ],
            "evidence": ["RAP x402/AP2 alignment scenarios", "external tester MVP receipt/eval/dispute expectations", "focused fail-closed tests"],
            "blockers": ["atomicity gap", "receipt/eval mismatch", "reputation emitted before dispute state is clear"],
        },
        "solanaProgramMintAllowlists": {
            "criteria": [
                "Every payment-capable Solana path is cluster-explicit and allowlist-bound by program, mint, and payee.",
                "Devnet allowlists cannot be promoted or interpreted as mainnet allowlists.",
            ],
            "evidence": ["#360 devnet gate artifact", "#365 tester controls", "allowlist mutation tests"],
            "blockers": ["unaudited contracts/programs", "wrong mint/program/payee accepted", "devnet/mainnet ambiguity"],
        },
        "authorityMandateBinding": {
            "criteria": [
                "AP2/FIDO/Verifiable Intent mandate identity, scope, max amount, expiry, revocation, and audit reference bind to each payment request.",
                "MCP resource authorization is never accepted as delegated payment authority.",
            ],
            "evidence": ["#361 layer contract", "mandate field mapping", "valid-authorization misuse scenario"],
            "blockers": ["unclear authority", "missing revocation reference", "authorization and payment refs disagree"],
        },
        "replayIdempotency": {
            "criteria": [
                "Mandate nonce, request hash, response hash, payment reference, and receipt id prevent stale or repeated settlement from being accepted.",
                "Idempotent retry evidence cannot double-count spend, service success, or reputation.",
            ],
            "evidence": ["stale/replayed mandate scenario", "receipt idempotency checklist", "negative replay tests"],
            "blockers": ["stale/replayed mandates", "duplicate receipt accepted", "nonce state unavailable"],
        },
        "receiptSettlementProof": {
            "criteria": [
                "Receipt records bind authority, resource access, payment evidence, settlement proof, service result, eval result, and dispute state.",
                "Settlement proof is environment-explicit and confirmation-state explicit.",
            ],
            "evidence": ["#361 Solana proof mapping", "#365 feedback required fields", "receipt fixture hashes"],
            "blockers": ["settlement proof missing", "payment proof detached from receipt", "confirmation state unclear"],
        },
        "privacyPii": {
            "criteria": [
                "Evidence captures public devnet identifiers and hashes only.",
                "Secrets, private keys, raw PII, production wallet material, and unredacted support notes are blocked from audit packets.",
            ],
            "evidence": ["privacy/PII scenario", "#365 feedback privacy rule", "fixture scan expectations"],
            "blockers": ["raw PII captured", "secret or private key captured", "production wallet material captured"],
        },
        "rollbackKillSwitch": {
            "criteria": [
                "Kill switch remains armed before any later bounded live/devnet cohort run.",
                "Rollback evidence is mandatory for failed, disputed, replayed, over-cap, or wrong-allowlist scenarios.",
            ],
            "evidence": ["#361 rollback delta", "#365 rollback evidence bundle", "rollback-required criteria"],
            "blockers": ["kill switch disabled", "rollback evidence missing", "unsafe path cannot be paused"],
        },
        "disputeReputation": {
            "criteria": [
                "Dispute state is explicit before reputation output.",
                "Negative, disputed, or incomplete receipts cannot improve reputation.",
            ],
            "evidence": ["RAP join-layer expectations", "#365 acceptance matrix", "dispute/reputation checklist"],
            "blockers": ["dispute state missing", "reputation emits on failed payment/service/eval", "reputation cannot be rolled back"],
        },
    }


def evidence_requirements() -> list[dict[str, Any]]:
    return [
        {"name": "deterministic tests", "required": True, "source": "focused fixture/test/smoke coverage for #366"},
        {"name": "localnet gate artifact", "required": True, "source": "consumed through #361/#365 chain from #359"},
        {"name": "devnet gate artifact", "required": True, "source": "consumed through #361/#365 chain from #360"},
        {"name": "threat model", "required": True, "source": "freeze threat model in this packet"},
        {"name": "invariant checklist", "required": True, "source": "freeze checklist in this packet"},
        {"name": "known limitations", "required": True, "source": "known limitation list in this packet"},
        {"name": "no-mainnet boundary proof", "required": True, "source": "boundary flags and mainnet blocker scenarios"},
    ]


def threat_model() -> list[dict[str, Any]]:
    return [
        {"id": "authority-confusion", "risk": "resource auth or payment proof is mistaken for delegated spend authority", "requiredControl": "authorityMandateBinding"},
        {"id": "replay-or-double-spend", "risk": "stale mandate or duplicate receipt is accepted", "requiredControl": "replayIdempotency"},
        {"id": "wrong-rail", "risk": "devnet proof, mint, program, or payee is confused with mainnet", "requiredControl": "solanaProgramMintAllowlists"},
        {"id": "atomicity-gap", "risk": "payment success is treated as full service success", "requiredControl": "paymentCapableInvariants"},
        {"id": "privacy-leak", "risk": "audit evidence captures secrets, private keys, PII, or production wallet material", "requiredControl": "privacyPii"},
        {"id": "irreversible-unsafe-state", "risk": "failed or disputed path lacks rollback/kill-switch evidence", "requiredControl": "rollbackKillSwitch"},
    ]


def known_limitations() -> list[str]:
    return [
        "This packet is audit-readiness planning evidence only, not an official audit.",
        "No smart contract, Solana program, wallet, facilitator, settlement path, or devnet/mainnet transaction was executed.",
        "Devnet tester evidence is still a gate packet and MVP packet, not a completed live cohort.",
        "Mainnet remains blocked until official audit completion and explicit go-live readiness.",
    ]


def blocker_catalog() -> dict[str, str]:
    return {
        "unaudited contracts/programs": "No payment-capable public beta or mainnet readiness work until an official audit covers the relevant contracts/programs.",
        "unclear authority": "Hold if mandate scope, signer, revocation, amount cap, expiry, or audit reference is missing or ambiguous.",
        "stale/replayed mandates": "Hold or rollback if nonce, request hash, response hash, receipt id, or mandate freshness cannot be proven.",
        "devnet/mainnet ambiguity": "Rollback-required if any evidence can be interpreted as mainnet-ready or mainnet-executed.",
        "unbounded spend": "Hold if per-attempt, per-tester, global, or mandate caps are absent or unenforced.",
    }


def default_scenarios() -> list[dict[str, Any]]:
    common = {
        "freezeAreas": list(FREEZE_AREAS),
        "evidence": list(REQUIRED_EVIDENCE),
        "blockers": list(REQUIRED_BLOCKERS),
        "authority": {"boundedMandate": True, "scopeClear": True, "revocationRef": True, "auditRef": True},
        "replay": {"nonceFresh": True, "idempotencyKeyPresent": True, "duplicateReceiptAccepted": False},
        "allowlist": {"cluster": "devnet", "mintAllowed": True, "programAllowed": True, "payeeAllowed": True},
        "caps": {"boundedSpend": True, "perAttemptCap": True, "globalCap": True},
        "proof": {"receiptPresent": True, "settlementProofPresent": True, "paymentServiceEvalAgree": True, "disputeStateClear": True},
        "privacy": {"secretsCaptured": False, "rawPiiCaptured": False, "productionWalletMaterialCaptured": False},
        "rollback": {"killSwitchArmed": True, "rollbackEvidencePresent": True},
        "boundaries": {"mainnetRun": False, "devnetRun": False, "smartContractDeployment": False},
    }
    return [
        {"id": "freeze-ready-baseline", "kind": "positive", "expectedStatus": "pass", "inputs": common},
        {
            "id": "unclear-authority-blocked",
            "kind": "authority",
            "expectedStatus": "fail",
            "inputs": {**common, "authority": {**common["authority"], "scopeClear": False}},
        },
        {
            "id": "replayed-mandate-blocked",
            "kind": "replay",
            "expectedStatus": "fail",
            "inputs": {**common, "replay": {**common["replay"], "nonceFresh": False, "duplicateReceiptAccepted": True}},
        },
        {
            "id": "devnet-mainnet-ambiguity-blocked",
            "kind": "mainnet",
            "expectedStatus": "fail",
            "inputs": {**common, "allowlist": {**common["allowlist"], "cluster": "mainnet-beta"}, "boundaries": {**common["boundaries"], "mainnetRun": True}},
        },
        {
            "id": "unbounded-spend-blocked",
            "kind": "spend",
            "expectedStatus": "fail",
            "inputs": {**common, "caps": {**common["caps"], "boundedSpend": False, "globalCap": False}},
        },
        {
            "id": "rollback-evidence-missing-blocked",
            "kind": "rollback",
            "expectedStatus": "fail",
            "inputs": {**common, "rollback": {**common["rollback"], "rollbackEvidencePresent": False}},
        },
        {
            "id": "privacy-leak-blocked",
            "kind": "privacy",
            "expectedStatus": "fail",
            "inputs": {**common, "privacy": {**common["privacy"], "rawPiiCaptured": True}},
        },
    ]


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    inputs = scenario["inputs"]
    findings: list[dict[str, str]] = []
    scenario_path = f"scenarios.{scenario['id']}"

    for area in FREEZE_AREAS:
        if area not in inputs["freezeAreas"]:
            findings.append(finding(f"{scenario_path}.freezeAreas.{area}", "All freeze areas must be covered."))
    for evidence in REQUIRED_EVIDENCE:
        if evidence not in inputs["evidence"]:
            findings.append(finding(f"{scenario_path}.evidence.{evidence}", "Required audit evidence is missing."))
    for blocker in REQUIRED_BLOCKERS:
        if blocker not in inputs["blockers"]:
            findings.append(finding(f"{scenario_path}.blockers.{blocker}", "Required audit blocker is missing."))

    for key in ("boundedMandate", "scopeClear", "revocationRef", "auditRef"):
        if inputs["authority"][key] is not True:
            findings.append(finding(f"{scenario_path}.authority.{key}", "Authority/mandate binding must be clear and auditable."))
    if inputs["replay"]["nonceFresh"] is not True or inputs["replay"]["duplicateReceiptAccepted"] is True:
        findings.append(finding(f"{scenario_path}.replay.idempotency", "Stale mandates and duplicate receipts must fail closed."))
    if inputs["allowlist"]["cluster"] != "devnet":
        findings.append(finding(f"{scenario_path}.allowlist.cluster", "Only devnet-scoped evidence may feed this planning packet."))
    for key in ("mintAllowed", "programAllowed", "payeeAllowed"):
        if inputs["allowlist"][key] is not True:
            findings.append(finding(f"{scenario_path}.allowlist.{key}", "Mint, program, and payee allowlists must hold."))
    for key in ("boundedSpend", "perAttemptCap", "globalCap"):
        if inputs["caps"][key] is not True:
            findings.append(finding(f"{scenario_path}.caps.{key}", "Spend must remain bounded before any later payment-capable run."))
    for key in ("receiptPresent", "settlementProofPresent", "paymentServiceEvalAgree", "disputeStateClear"):
        if inputs["proof"][key] is not True:
            findings.append(finding(f"{scenario_path}.proof.{key}", "Receipt, settlement, eval, and dispute proof must agree."))
    for key in ("secretsCaptured", "rawPiiCaptured", "productionWalletMaterialCaptured"):
        if inputs["privacy"][key] is True:
            findings.append(finding(f"{scenario_path}.privacy.{key}", "Audit evidence must not capture secrets, PII, or production wallet material."))
    if inputs["rollback"]["killSwitchArmed"] is not True:
        findings.append(finding(f"{scenario_path}.rollback.killSwitchArmed", "Kill switch must remain armed."))
    if inputs["rollback"]["rollbackEvidencePresent"] is not True:
        findings.append(finding(f"{scenario_path}.rollback.rollbackEvidencePresent", "Rollback evidence is required."))
    for key in ("mainnetRun", "devnetRun", "smartContractDeployment"):
        if inputs["boundaries"][key] is True:
            findings.append(finding(f"{scenario_path}.boundaries.{key}", "This freeze packet cannot record live chain or deployment action."))

    return findings


def build_scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    findings = scenario_findings(scenario)
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "expectedStatus": scenario["expectedStatus"],
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "inputs": scenario["inputs"],
    }


def collect_packet_findings(
    artifacts: dict[str, dict[str, Any]],
    roadmap_text: str,
    audit_doc: dict[str, Any],
    tester_doc: dict[str, Any],
    boundary_doc: dict[str, Any],
    checklist: dict[str, dict[str, Any]],
    evidence: list[dict[str, Any]],
    threats: list[dict[str, Any]],
    limitations: list[str],
    blockers: dict[str, str],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for name, artifact in artifacts.items():
        if not artifact["exists"] or not artifact["sha256"] or not artifact["sizeBytes"]:
            findings.append(finding(f"artifacts.{name}", "Required upstream artifact binding is missing."))

    roadmap = normalized_text(roadmap_text)
    for term in ("audit-readiness freeze/evidence", "official audit", "Mainnet remains blocked"):
        if normalized_text(term) not in roadmap:
            findings.append(finding("roadmap.requiredTerms", f"Missing roadmap term: {term}."))

    if audit_doc.get("decision") != "audit-prep-ready":
        findings.append(finding("auditPrep.decision", "RAP x402/AP2 audit-prep evidence must be ready."))
    if tester_doc.get("decision") != "mvp-packet-ready":
        findings.append(finding("testerMvp.decision", "External tester MVP packet evidence must be ready."))
    if "rollbackKillSwitch" not in audit_doc.get("auditDeltas", {}):
        findings.append(finding("auditPrep.auditDeltas.rollbackKillSwitch", "Audit prep must include rollback/kill-switch deltas."))
    if tester_doc.get("controls", {}).get("allowlists", {}).get("cluster") != "devnet":
        findings.append(finding("testerMvp.controls.allowlists.cluster", "Tester MVP packet must preserve devnet allowlists."))

    for area in FREEZE_AREAS:
        item = checklist.get(area)
        if not item or not item.get("criteria") or not item.get("evidence") or not item.get("blockers"):
            findings.append(finding(f"freezeChecklist.{area}", "Every freeze area needs criteria, evidence, and blockers."))
    evidence_names = {item.get("name") for item in evidence}
    for item in REQUIRED_EVIDENCE:
        if item not in evidence_names:
            findings.append(finding(f"evidenceRequirements.{item}", "Required audit evidence entry is missing."))
    control_names = {item.get("requiredControl") for item in threats}
    for area in ("authorityMandateBinding", "replayIdempotency", "solanaProgramMintAllowlists", "rollbackKillSwitch"):
        if area not in control_names:
            findings.append(finding(f"threatModel.{area}", "Threat model must map risk to freeze controls."))
    for blocker in REQUIRED_BLOCKERS:
        if blocker not in blockers:
            findings.append(finding(f"blockers.{blocker}", "Required blocker is missing."))
    if not any("not an official audit" in item for item in limitations):
        findings.append(finding("knownLimitations.officialAudit", "Known limitations must state this is not an official audit."))

    for flag in REQUIRED_BOUNDARY_FALSE:
        if boundary_doc.get(flag) is not False:
            findings.append(finding(f"boundaries.{flag}", "Freeze packet must preserve no-live-action boundary."))
    for flag in ("officialAuditRequiredBeforePaymentCapablePublicBeta", "explicitGoLiveReadinessRequired"):
        if boundary_doc.get(flag) is not True:
            findings.append(finding(f"boundaries.{flag}", "Official audit and go-live readiness gates are required."))

    for scenario in scenarios:
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
        "rapX402Ap2AuditPrep": artifact_binding(AUDIT_PREP_PATH, issue=361),
        "externalTesterMvp": artifact_binding(TESTER_MVP_PATH, issue=365),
        "roadmap": artifact_binding(ROADMAP_PATH),
        "readme": artifact_binding(README_PATH),
    }
    roadmap_text = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in (ROADMAP_PATH, README_PATH))
    audit_doc = load_json(ROOT / AUDIT_PREP_PATH)
    tester_doc = load_json(ROOT / TESTER_MVP_PATH)
    boundary_doc = boundaries()
    checklist = freeze_checklist()
    evidence = evidence_requirements()
    threats = threat_model()
    limitations = known_limitations()
    blockers = blocker_catalog()
    scenarios = [build_scenario_result(scenario) for scenario in default_scenarios()]
    findings = collect_packet_findings(
        artifacts,
        roadmap_text,
        audit_doc,
        tester_doc,
        boundary_doc,
        checklist,
        evidence,
        threats,
        limitations,
        blockers,
        scenarios,
    )
    return {
        "mode": "smart-contract-audit-readiness-freeze-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": list(REQUIRED_ISSUES),
        "status": "pass" if not findings else "fail",
        "decision": decision_for(findings, requested_decision),
        "packetId": "reddiagent-smart-contract-audit-readiness-freeze",
        "mainnetStatement": "Mainnet remains blocked until official audit completion and explicit go-live readiness.",
        "executionStatement": "This packet is audit-readiness planning evidence only; it does not authorize smart-contract deployment, devnet execution, public beta execution, or mainnet readiness work.",
        "artifacts": artifacts,
        "freezeChecklist": checklist,
        "evidenceRequirements": evidence,
        "threatModel": threats,
        "knownLimitations": limitations,
        "blockers": blockers,
        "scenarioSummary": {
            "positiveScenarios": sum(1 for scenario in scenarios if scenario["expectedStatus"] == "pass"),
            "negativeScenarios": sum(1 for scenario in scenarios if scenario["expectedStatus"] == "fail"),
            "failClosedScenarios": sum(1 for scenario in scenarios if scenario["expectedStatus"] == "fail" and scenario["status"] == "fail"),
            "mainnetAmbiguityScenarios": sum(1 for scenario in scenarios if scenario["kind"] == "mainnet"),
            "privacyScenarios": sum(1 for scenario in scenarios if scenario["kind"] == "privacy"),
        },
        "scenarios": scenarios,
        "boundaries": boundary_doc,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requested-decision",
        choices=("audit-freeze-ready", "hold", "rollback-required"),
        default="audit-freeze-ready",
    )
    parser.add_argument("--output", type=Path, help="Optional path for the generated audit freeze packet JSON.")
    args = parser.parse_args()
    packet = build_packet(args.requested_decision)
    output = dump_json(packet)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if packet["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
