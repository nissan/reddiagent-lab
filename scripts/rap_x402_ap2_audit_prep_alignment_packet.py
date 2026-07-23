#!/usr/bin/env python3
"""Build deterministic RAP x402/AP2 audit-prep alignment evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = 361
PARENT_EPIC = 220
REQUIRED_ISSUES = (356, 359, 360)
ROADMAP_PACKET_PATH = "research/2026-07-23-agentic-payments-roadmap-recalibration.md"
LOCALNET_PACKET_PATH = "tests/fixtures/beta-surfpool-localnet-rehearsal-packet.json"
DEVNET_GATE_PATH = "tests/fixtures/beta-solana-devnet-external-tester-gate.json"
RAP_BRIDGE_READY_PATH = "tests/fixtures/rap-bridge-x402-paid-mcp-ready.json"
AP2_X402_READY_PATH = "tests/fixtures/ap2-x402-mandate-ready.json"
MCP_HANDOFF_READY_PATH = "tests/fixtures/mcp-runtime-handoff-ready.json"
REQUIRED_ROADMAP_TERMS = (
    "x402 is payment evidence",
    "AP2/FIDO/Verifiable Intent is authority",
    "MCP auth is resource access",
    "RAP binds the receipt/accounting/reputation envelope",
    "Replay resistance",
    "Atomicity",
    "Privacy/PII",
    "Settlement proof",
    "Kill switch",
)
REQUIRED_AUDIT_AREAS = (
    "invariants",
    "replayResistance",
    "atomicity",
    "delegatedAuthority",
    "spendLimits",
    "privacyPii",
    "receiptSettlementProof",
    "rollbackKillSwitch",
)
REQUIRED_BOUNDARY_FALSE = (
    "liveRuntimeActivation",
    "hostedDeployment",
    "dockerSurfpoolCoolifyMutation",
    "credentialAccess",
    "liveMcpInvocation",
    "devnetRun",
    "mainnetRun",
    "walletAccess",
    "paymentFacilitatorSettlementAction",
    "packagePublishing",
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


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def artifact_binding(path_text: str, *, issue: int | None = None) -> dict[str, Any]:
    path = ROOT / path_text
    binding = {
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
        "deterministicAuditPrepPacket": True,
        "researchSpecAuditPrepOnly": True,
        "liveRuntimeActivation": False,
        "hostedDeployment": False,
        "dockerSurfpoolCoolifyMutation": False,
        "credentialAccess": False,
        "liveMcpInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "walletAccess": False,
        "paymentFacilitatorSettlementAction": False,
        "packagePublishing": False,
        "productionGatewayMutation": False,
    }


def layer_contract() -> list[dict[str, Any]]:
    return [
        {
            "layer": "delegatedAuthority",
            "source": "AP2/FIDO/Verifiable Intent",
            "responsibility": "prove who authorized what, for whom, within which cap and expiry",
            "adlRapFields": [
                "authority.mandateId",
                "authority.principal",
                "authority.spender",
                "authority.payee",
                "authority.scope",
                "authority.maxAmount",
                "authority.expiresAt",
                "authority.revocationRef",
                "authority.auditRef",
            ],
            "auditQuestion": "Can any spend-capable path execute without a bounded mandate?",
            "failClosedRule": "missing, stale, over-broad, revoked, or mismatched mandates fail before execution",
        },
        {
            "layer": "resourceAccess",
            "source": "MCP authorization",
            "responsibility": "separate protected tool/resource access from payment permission",
            "adlRapFields": [
                "service.mcp.serverRef",
                "service.mcp.toolName",
                "service.mcp.authorizationRef",
                "policy.resourceAccess",
            ],
            "auditQuestion": "Can MCP auth be mistaken for payment authority?",
            "failClosedRule": "resource access success cannot emit payment receipts or reputation by itself",
        },
        {
            "layer": "paymentEvidence",
            "source": "x402",
            "responsibility": "carry HTTP payment challenge, selected rail, signature, and response proof",
            "adlRapFields": [
                "x402.PaymentRequired",
                "x402.PaymentSignature.authorizationRef",
                "x402.PaymentSignature.selectedRail",
                "x402.PaymentResponse.transactionRef",
            ],
            "auditQuestion": "Can payment success be interpreted as service success?",
            "failClosedRule": "payment evidence must be joined to service outcome and eval status",
        },
        {
            "layer": "settlementProof",
            "source": "Solana",
            "responsibility": "prove environment, mint/program allowlist, signature, confirmation, payer, payee, and amount",
            "adlRapFields": [
                "settlement.cluster",
                "settlement.signature",
                "settlement.confirmationStatus",
                "settlement.mint",
                "settlement.programId",
                "settlement.amount",
            ],
            "auditQuestion": "Can devnet evidence be confused with mainnet evidence?",
            "failClosedRule": "environment labels, mints, program ids, and confirmation policy must match the intended rail",
        },
        {
            "layer": "receiptAccountingReputation",
            "source": "RAP",
            "responsibility": "bind request, response, authority, payment, settlement, service result, eval, and dispute state",
            "adlRapFields": [
                "receipts.requestHash",
                "receipts.responseHash",
                "receipts.paymentRef",
                "receipts.serviceResultStatus",
                "receipts.requiredEvalGateStatus",
                "reputation.signals",
                "dispute.status",
            ],
            "auditQuestion": "Can reputation emit before the full receipt bundle is valid?",
            "failClosedRule": "reputation emits only after receipt verification, service pass, eval pass, and dispute clearance",
        },
    ]


def source_field_mapping() -> list[dict[str, Any]]:
    return [
        {
            "standard": "x402",
            "standardFields": [
                "HTTP 402 Payment Required",
                "PAYMENT-REQUIRED / PaymentRequired.accepts",
                "PAYMENT-SIGNATURE / PaymentPayload",
                "PAYMENT-RESPONSE / SettlementResponse",
                "payment-identifier",
                "facilitator verify/settle response",
            ],
            "adlRapFields": [
                "extensions.x402.intents[].rails",
                "extensions.x402.intents[].maxAmount",
                "extensions.x402.intents[].currency",
                "receipts.paymentRef",
                "receipts.paymentRequiredHash",
                "receipts.paymentResponseHash",
                "receipts.idempotencyKey",
            ],
            "auditExpectation": "x402 fields prove payment challenge/payload/settlement evidence only; they do not prove authority, service success, or reputation eligibility.",
        },
        {
            "standard": "AP2/FIDO/Verifiable Intent",
            "standardFields": [
                "IntentMandate",
                "CheckoutMandate",
                "PaymentMandate",
                "verifiable credential issuer/subject",
                "user-signed intent",
                "non-repudiable audit trail",
                "revocation/audit reference",
            ],
            "adlRapFields": [
                "extensions.authority.principal",
                "extensions.authority.spender",
                "extensions.authority.payee",
                "extensions.authority.scope",
                "extensions.authority.maxAmount",
                "extensions.authority.expiresAt",
                "extensions.authority.revocationRef",
                "extensions.authority.auditRef",
            ],
            "auditExpectation": "authority must be bounded, current, purpose-bound, rail-bound, and independently verifiable before any payment-capable path can proceed.",
        },
        {
            "standard": "MCP authorization",
            "standardFields": [
                "OAuth protected resource metadata",
                "authorization_servers",
                "resource_metadata WWW-Authenticate",
                "scope",
                "OAuth 2.1 authorization server metadata",
                "enterprise-managed authorization policy",
            ],
            "adlRapFields": [
                "harness.tools[].id",
                "harness.tools[].policyRefs",
                "service.mcp.serverRef",
                "service.mcp.authorizationRef",
                "policy.resourceAccess",
                "receipts.serviceResultStatus",
            ],
            "auditExpectation": "MCP authorization proves protected resource access only; it must not be accepted as delegated payment authority or settlement proof.",
        },
        {
            "standard": "Solana payment proof",
            "standardFields": [
                "cluster",
                "signature",
                "slot",
                "blockTime",
                "err",
                "confirmationStatus",
                "mint",
                "programId",
                "source token account",
                "destination token account",
                "amount",
            ],
            "adlRapFields": [
                "settlement.cluster",
                "settlement.signature",
                "settlement.slot",
                "settlement.confirmationStatus",
                "settlement.mint",
                "settlement.programId",
                "settlement.payer",
                "settlement.payee",
                "settlement.amount",
            ],
            "auditExpectation": "Solana proof must be environment-explicit and allowlist-bound so devnet/mainnet, mint/program, payer/payee, and confirmation state cannot be confused.",
        },
        {
            "standard": "RAP receipt/accounting/reputation",
            "standardFields": [
                "request hash",
                "response hash",
                "authority reference",
                "payment reference",
                "settlement reference",
                "service result",
                "eval gate status",
                "dispute state",
                "reputation signal source",
            ],
            "adlRapFields": [
                "receipts.requestHash",
                "receipts.responseHash",
                "receipts.authorityRef",
                "receipts.paymentRef",
                "receipts.serviceResultStatus",
                "receipts.requiredEvalGateStatus",
                "dispute.status",
                "reputation.signals",
            ],
            "auditExpectation": "RAP is the join layer: success/reputation can emit only when authority, resource access, payment evidence, settlement proof, service result, eval, and dispute state all agree.",
        },
    ]


def audit_deltas() -> dict[str, dict[str, Any]]:
    return {
        "invariants": {
            "mustProve": [
                "receipt ids are unique",
                "authority scope matches payee, purpose, rail, mint, amount, and expiry",
                "reputation is derived from verified receipt state",
            ],
            "evidence": ["unit tests", "scenario packet", "auditor checklist"],
            "readyWhen": "all spend-capable paths name the invariant they enforce",
        },
        "replayResistance": {
            "mustProve": ["nonce uniqueness", "mandate id binding", "request hash binding", "expiry enforcement"],
            "evidence": ["stale mandate fixture", "replayed request fixture"],
            "readyWhen": "stale or reused nonce/request pairs cannot spend or emit receipts",
        },
        "atomicity": {
            "mustProve": [
                "payment-settled/service-failed cannot report success",
                "service-returned/payment-missing cannot report success",
                "partial multi-step workflows surface rollback-required",
            ],
            "evidence": ["decoupling scenarios", "receipt status assertions"],
            "readyWhen": "success requires payment, service result, and eval status to agree",
        },
        "delegatedAuthority": {
            "mustProve": ["principal", "spender", "payee", "purpose", "scope", "cap", "rail", "mint", "revocation"],
            "evidence": ["AP2/FIDO/VI field mapping", "valid-authorization misuse scenario"],
            "readyWhen": "valid signatures cannot be reused for wrong purpose, merchant, or rail",
        },
        "spendLimits": {
            "mustProve": ["per-intent cap", "per-tester cap", "daily cap", "global cohort cap"],
            "evidence": ["over-budget fail-closed fixture", "cap pre-sign and pre-receipt checks"],
            "readyWhen": "limits are enforced before signing and before receipt completion",
        },
        "privacyPii": {
            "mustProve": ["raw intent minimization", "payload hashing", "wallet/user identifier minimization"],
            "evidence": ["redaction policy", "receipt payload shape"],
            "readyWhen": "receipts are dispute-useful without storing raw PII or secrets",
        },
        "receiptSettlementProof": {
            "mustProve": ["cluster label", "signature", "confirmation", "mint/program allowlist", "payer/payee/amount"],
            "evidence": ["Solana proof mapping", "devnet/mainnet confusion scenario"],
            "readyWhen": "devnet and mainnet receipts are impossible to confuse",
        },
        "rollbackKillSwitch": {
            "mustProve": ["operator pause", "mandate revocation", "per-agent suspension", "receipt review marking"],
            "evidence": ["rollback scenario", "kill-switch owner and state"],
            "readyWhen": "future spend can be stopped without mutating historical evidence",
        },
    }


def default_scenarios() -> list[dict[str, Any]]:
    base_bundle = {
        "authority": {
            "mandateId": "mandate-audit-001",
            "principal": "tester-principal",
            "spender": "reddiagent-spender",
            "payee": "merchant-service-devnet",
            "purpose": "paid-data-receipt-review",
            "scope": "single paid data review",
            "maxAmountMinorUnits": 100_000,
            "expiresAt": "2026-08-01T00:00:00Z",
            "revoked": False,
        },
        "x402": {
            "paymentRequired": True,
            "selectedRail": "solana-devnet-usdc",
            "authorizationRef": "mandate-audit-001",
            "paymentResponseSuccess": True,
        },
        "mcp": {"resourceAccessAuthorized": True, "toolName": "forecast_report"},
        "settlement": {
            "cluster": "devnet",
            "signature": "devnet-sig-audit-001",
            "confirmationStatus": "confirmed",
            "mintAllowlisted": True,
            "programAllowlisted": True,
        },
        "receipt": {
            "requestHash": "reqhash-audit-001",
            "responseHash": "resphash-audit-001",
            "paymentRef": "devnet-sig-audit-001",
            "serviceResultStatus": "pass",
            "requiredEvalGateStatus": "pass",
            "reputationSignals": ["receipt_verified", "service_result_pass", "required_eval_gate_pass"],
        },
        "privacy": {"rawPiiStored": False, "payloadsHashed": True},
        "rollback": {"killSwitchArmed": True, "receiptMarkedForReview": False},
        "boundaries": {"mainnetUsed": False, "realValueTransfer": False, "liveFacilitatorUsed": False},
    }
    return [
        {
            "id": "complete-authorized-paid-service-bundle",
            "kind": "positive",
            "expectedStatus": "pass",
            "inputs": base_bundle,
        },
        {
            "id": "payment-settled-service-failed",
            "kind": "atomicity",
            "expectedStatus": "fail",
            "inputs": {
                **base_bundle,
                "receipt": {**base_bundle["receipt"], "serviceResultStatus": "fail"},
                "rollback": {**base_bundle["rollback"], "receiptMarkedForReview": True},
            },
        },
        {
            "id": "valid-authorization-wrong-purpose",
            "kind": "delegatedAuthority",
            "expectedStatus": "fail",
            "inputs": {
                **base_bundle,
                "authority": {**base_bundle["authority"], "purpose": "different-purpose"},
            },
        },
        {
            "id": "stale-replayed-mandate",
            "kind": "replayResistance",
            "expectedStatus": "fail",
            "inputs": {
                **base_bundle,
                "replay": {"nonceSeen": True, "previousReceiptId": "receipt-audit-prior"},
            },
        },
        {
            "id": "devnet-mainnet-confusion",
            "kind": "receiptSettlementProof",
            "expectedStatus": "fail",
            "inputs": {
                **base_bundle,
                "settlement": {**base_bundle["settlement"], "cluster": "mainnet-beta"},
                "boundaries": {**base_bundle["boundaries"], "mainnetUsed": True},
            },
        },
        {
            "id": "raw-pii-in-receipt",
            "kind": "privacyPii",
            "expectedStatus": "fail",
            "inputs": {
                **base_bundle,
                "privacy": {"rawPiiStored": True, "payloadsHashed": False},
            },
        },
    ]


def scenario_findings(scenario: dict[str, Any]) -> list[dict[str, str]]:
    inputs = scenario["inputs"]
    findings: list[dict[str, str]] = []
    authority = inputs["authority"]
    receipt = inputs["receipt"]
    settlement = inputs["settlement"]
    privacy = inputs["privacy"]
    boundaries_doc = inputs["boundaries"]

    if receipt["serviceResultStatus"] != "pass":
        findings.append(finding(f"scenarios.{scenario['id']}.receipt.serviceResultStatus", "Payment success cannot prove service success."))
    if receipt["requiredEvalGateStatus"] != "pass":
        findings.append(finding(f"scenarios.{scenario['id']}.receipt.requiredEvalGateStatus", "Eval pass is required before receipt success."))
    if authority["purpose"] != "paid-data-receipt-review":
        findings.append(finding(f"scenarios.{scenario['id']}.authority.purpose", "Mandate purpose does not match requested service."))
    if scenario["inputs"].get("replay", {}).get("nonceSeen") is True:
        findings.append(finding(f"scenarios.{scenario['id']}.replay.nonceSeen", "Replayed nonce must fail closed."))
    if settlement["cluster"] != "devnet" or boundaries_doc["mainnetUsed"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.settlement.cluster", "Devnet evidence cannot use or resemble mainnet settlement."))
    if privacy["rawPiiStored"] is True or privacy["payloadsHashed"] is not True:
        findings.append(finding(f"scenarios.{scenario['id']}.privacy.rawPiiStored", "Receipt evidence must avoid raw PII and use payload hashes."))
    if boundaries_doc["realValueTransfer"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.boundaries.realValueTransfer", "Audit-prep scenarios cannot perform real-value transfer."))
    if boundaries_doc["liveFacilitatorUsed"] is True:
        findings.append(finding(f"scenarios.{scenario['id']}.boundaries.liveFacilitatorUsed", "Audit-prep scenarios cannot call a live facilitator."))
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
    roadmap_text: str,
    artifacts: dict[str, dict[str, Any]],
    localnet_doc: dict[str, Any],
    devnet_doc: dict[str, Any],
    rap_ready_doc: dict[str, Any],
    ap2_ready_doc: dict[str, Any],
    boundaries_doc: dict[str, Any],
    layers: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    deltas: dict[str, Any],
    scenario_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for name, artifact in artifacts.items():
        if not artifact["exists"] or not artifact["sha256"] or not artifact["sizeBytes"]:
            findings.append(finding(f"artifacts.{name}", "Required upstream artifact binding is missing."))

    normalized_roadmap = normalized_text(roadmap_text)
    for term in REQUIRED_ROADMAP_TERMS:
        if normalized_text(term) not in normalized_roadmap:
            findings.append(finding("roadmap.requiredTerms", f"Missing required #356 term: {term}."))

    if localnet_doc.get("decision") != "localnet-rehearsal-ready":
        findings.append(finding("localnet.decision", "Localnet rehearsal must be ready before audit prep."))
    if devnet_doc.get("decision") != "devnet-tester-gate-ready":
        findings.append(finding("devnet.decision", "Devnet tester gate must be ready before audit prep."))
    if rap_ready_doc.get("conformance", {}).get("liveBridgeAllowed") is not False:
        findings.append(finding("rapBridge.conformance.liveBridgeAllowed", "RAP bridge evidence must remain non-live."))
    payment_mandate = ap2_ready_doc.get("ap2", {}).get("mandates", {}).get("PaymentMandate", {})
    payment_response = ap2_ready_doc.get("x402", {}).get("PaymentResponse", {})
    receipt_policy = ap2_ready_doc.get("rap", {}).get("facilitatorProfile", {}).get("receiptPolicy")
    if not payment_mandate.get("id") or not payment_mandate.get("revocationRef"):
        findings.append(finding("ap2X402.ap2.mandates.PaymentMandate", "AP2/x402 fixture must include a bounded payment mandate with revocation."))
    if payment_response.get("success") is not True or not payment_response.get("transactionRef"):
        findings.append(finding("ap2X402.x402.PaymentResponse", "AP2/x402 fixture must include payment response evidence."))
    if receipt_policy != "emit-after-payment-and-service-pass":
        findings.append(finding("ap2X402.rap.facilitatorProfile.receiptPolicy", "AP2/x402 fixture must bind receipts to payment and service pass."))

    for flag in REQUIRED_BOUNDARY_FALSE:
        if boundaries_doc.get(flag) is not False:
            findings.append(finding(f"boundaries.{flag}", "Audit-prep packet must preserve no-live-action boundary."))

    layer_names = {entry["layer"] for entry in layers}
    for layer in ("delegatedAuthority", "resourceAccess", "paymentEvidence", "settlementProof", "receiptAccountingReputation"):
        if layer not in layer_names:
            findings.append(finding("layerContract", f"Missing layer contract: {layer}."))

    mapped_standards = {entry["standard"] for entry in mappings}
    for standard in (
        "x402",
        "AP2/FIDO/Verifiable Intent",
        "MCP authorization",
        "Solana payment proof",
        "RAP receipt/accounting/reputation",
    ):
        if standard not in mapped_standards:
            findings.append(finding("sourceFieldMapping", f"Missing standard mapping: {standard}."))

    for area in REQUIRED_AUDIT_AREAS:
        if area not in deltas:
            findings.append(finding("auditDeltas", f"Missing audit delta area: {area}."))

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
    roadmap_text = (ROOT / ROADMAP_PACKET_PATH).read_text(encoding="utf-8")
    localnet_doc = load_json(ROOT / LOCALNET_PACKET_PATH)
    devnet_doc = load_json(ROOT / DEVNET_GATE_PATH)
    rap_ready_doc = load_json(ROOT / RAP_BRIDGE_READY_PATH)
    ap2_ready_doc = load_json(ROOT / AP2_X402_READY_PATH)
    artifacts = {
        "roadmap": artifact_binding(ROADMAP_PACKET_PATH, issue=356),
        "localnetRehearsal": artifact_binding(LOCALNET_PACKET_PATH, issue=359),
        "devnetTesterGate": artifact_binding(DEVNET_GATE_PATH, issue=360),
        "rapBridgeReady": artifact_binding(RAP_BRIDGE_READY_PATH),
        "ap2X402MandateReady": artifact_binding(AP2_X402_READY_PATH),
        "mcpRuntimeHandoffReady": artifact_binding(MCP_HANDOFF_READY_PATH),
    }
    boundary_doc = boundaries()
    layers = layer_contract()
    mappings = source_field_mapping()
    deltas = audit_deltas()
    scenario_results = [build_scenario_result(scenario) for scenario in default_scenarios()]
    findings = collect_packet_findings(
        roadmap_text,
        artifacts,
        localnet_doc,
        devnet_doc,
        rap_ready_doc,
        ap2_ready_doc,
        boundary_doc,
        layers,
        mappings,
        deltas,
        scenario_results,
    )
    return {
        "mode": "rap-x402-ap2-audit-prep-alignment-packet",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": list(REQUIRED_ISSUES),
        "status": "pass" if not findings else "fail",
        "decision": decision_for(findings, requested_decision),
        "packetId": "reddiagent-rap-x402-ap2-audit-prep-alignment",
        "mainnetStatement": "Mainnet remains blocked until official audit completion and explicit go-live readiness.",
        "artifacts": artifacts,
        "layerContract": layers,
        "sourceFieldMapping": mappings,
        "auditDeltas": deltas,
        "scenarioSummary": {
            "positiveScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "pass"),
            "negativeScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail"),
            "failClosedScenarios": sum(1 for scenario in scenario_results if scenario["expectedStatus"] == "fail" and scenario["status"] == "fail"),
            "privacyScenarios": sum(1 for scenario in scenario_results if scenario["kind"] == "privacyPii"),
            "atomicityScenarios": sum(1 for scenario in scenario_results if scenario["kind"] == "atomicity"),
        },
        "scenarios": scenario_results,
        "boundaries": boundary_doc,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requested-decision",
        choices=("audit-prep-ready", "hold", "rollback-required"),
        default="audit-prep-ready",
    )
    args = parser.parse_args()
    packet = build_packet(args.requested_decision)
    print(dump_json(packet), end="")
    return 0 if packet["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
