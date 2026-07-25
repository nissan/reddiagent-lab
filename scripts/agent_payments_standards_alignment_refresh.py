#!/usr/bin/env python3
"""Build deterministic agent-payments standards alignment evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = 374
PARENT_EPIC = 220
DATE_CHECKED = "2026-07-25"
FIXTURE = ROOT / "tests" / "fixtures" / "agent-payments-standards-alignment-refresh.json"


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def source_matrix() -> list[dict[str, Any]]:
    return [
        {
            "protocol": "x402",
            "layer": "paymentEvidence",
            "confidence": "high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://www.linuxfoundation.org/press/linux-foundation-announces-operational-launch-of-x402-foundation-to-standardize-internet-native-payments-for-ai-agents-and-applications",
                "https://www.x402.org/x402-whitepaper.pdf",
                "https://www.coinbase.com/developer-platform/discover/launches/x402",
                "https://x402.org/",
            ],
            "relevance": "HTTP-native payment challenge/payload/settlement evidence for paid APIs, apps, and agent services.",
            "reddiagentAction": "Keep x402 as payment evidence only; feed #375 receipt-integrity benchmarks and #376 static discovery compatibility.",
        },
        {
            "protocol": "Pay.sh",
            "layer": "externalServiceDiscovery",
            "confidence": "medium-high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://learn.backpack.exchange/articles/what-is-pay-sh-solana-and-ai-agent-payments",
            ],
            "relevance": "Solana-oriented x402/API discovery and proxy pattern for agent-paid API access.",
            "reddiagentAction": "Study as static discovery/proxy compatibility only in #376; do not contact, redeem, call, or pay providers.",
        },
        {
            "protocol": "AP2/FIDO/Verifiable Intent",
            "layer": "delegatedAuthority",
            "confidence": "high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol",
                "https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/",
                "https://fidoalliance.org/building-the-trust-layer-for-agentic-payments-with-ap2-and-verifiable-intent/",
                "https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html",
            ],
            "relevance": "Mandates and verifiable intent establish user authorization, consent, accountability, and non-repudiation.",
            "reddiagentAction": "Refresh ADL/RAP mandate mapping in #377; do not let payment proof substitute for authorization.",
        },
        {
            "protocol": "MCP authorization",
            "layer": "protectedResourceAccess",
            "confidence": "high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization",
                "https://modelcontextprotocol.io/docs/tutorials/security/authorization",
            ],
            "relevance": "Protected resource metadata and OAuth-style authorization govern tool/resource access, not payment permission.",
            "reddiagentAction": "Keep MCP authorization separate from x402/AP2; use it as resource-access evidence in later static reports.",
        },
        {
            "protocol": "AIP",
            "layer": "identityGovernance",
            "confidence": "medium",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://github.com/openagentidentityprotocol",
                "https://github.com/openagentidentityprotocol/agentidentityprotocol",
            ],
            "relevance": "Emerging identity, attestation, authorization, governance, and audit-trail layer for MCP/autonomous agents.",
            "reddiagentAction": "Treat as compatibility/report target in #378 until maturity and adoption are clearer.",
        },
        {
            "protocol": "Solana Agent Registry/SATI/ERC-8004",
            "layer": "identityReputationDiscovery",
            "confidence": "medium",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://solana.com/agent-registry/what-is-agent-registry",
                "https://github.com/solana-foundation/SRFCs/discussions/7",
            ],
            "relevance": "On-chain agent identity, registration metadata, capability declarations, and proposed SATI trust infrastructure.",
            "reddiagentAction": "Compare identity/reputation/export surfaces in #378; keep report-only before promoting runtime use.",
        },
        {
            "protocol": "Token-2022",
            "layer": "settlementAssetControls",
            "confidence": "high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://solana.com/docs/tokens/extensions",
                "https://solana.com/solutions/token-extensions",
            ],
            "relevance": "Optional token/mint/account extensions can express transfer, memo, delegate, default-state, fee, and metadata controls.",
            "reddiagentAction": "Evaluate RAP payment asset extension candidates and footguns in #379 before any payment-capable beta.",
        },
        {
            "protocol": "MPP",
            "layer": "machinePaymentAlternative",
            "confidence": "medium-high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://stripe.com/blog/machine-payments-protocol",
                "https://docs.stripe.com/payments/machine",
            ],
            "relevance": "Machine Payments Protocol is a separate programmatic payment interface that overlaps x402 but is vendor/rail distinct.",
            "reddiagentAction": "Classify as non-canonical adapter/export target in #380; do not displace Solana/x402/AP2 core lane.",
        },
        {
            "protocol": "ACP",
            "layer": "commerceCheckoutAlternative",
            "confidence": "medium-high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "https://stripe.com/blog/developing-an-open-standard-for-agentic-commerce",
                "https://docs.stripe.com/agentic-commerce/acp",
            ],
            "relevance": "Agentic Commerce Protocol focuses buyer-agent-to-business checkout and commerce flows.",
            "reddiagentAction": "Classify as non-canonical commerce adapter target in #380; keep out of RAP receipt-critical path for now.",
        },
        {
            "protocol": "RAP",
            "layer": "receiptAccountingDisputeEvalReputation",
            "confidence": "high",
            "dateChecked": DATE_CHECKED,
            "sources": [
                "specs/RAP-BRIDGE-v0.1.md",
                "specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md",
                "tests/fixtures/rap-x402-ap2-audit-prep-alignment-packet.json",
                "tests/fixtures/beta-external-tester-mvp-packet.json",
                "tests/fixtures/smart-contract-audit-readiness-freeze-packet.json",
            ],
            "relevance": "Local ReddiAgent layer binds payment, authority, resource access, settlement, service outcome, eval, dispute, and reputation evidence.",
            "reddiagentAction": "Use #375 as next technical safety gate before standards-specific reports advance.",
        },
    ]


def layer_rules() -> list[dict[str, str]]:
    return [
        {"layer": "paymentEvidence", "rule": "x402 is payment evidence; it does not prove delegated authority, service success, or reputation eligibility."},
        {"layer": "delegatedAuthority", "rule": "AP2/FIDO/Verifiable Intent is delegated authority; mandates must bind actor, payee, purpose, cap, expiry, revocation, and audit refs."},
        {"layer": "protectedResourceAccess", "rule": "MCP auth is protected resource access; it does not authorize spend or settlement."},
        {"layer": "settlementProgramEvidence", "rule": "Solana is settlement/program evidence; cluster, mint, program id, signature, confirmation, and allowlist evidence must be explicit."},
        {"layer": "receiptAccountingDisputeEvalReputation", "rule": "RAP binds receipt/accounting/dispute/eval/reputation evidence across all lower layers."},
    ]


def issue_ladder() -> list[dict[str, Any]]:
    return [
        {
            "issue": 374,
            "title": "Research agent payments standards alignment refresh",
            "priority": 1,
            "swimlane": "Standards Intelligence",
            "status": "active",
            "purpose": "Build dated source matrix, taxonomy, issue ladder, and refresh assumptions.",
        },
        {
            "issue": 375,
            "title": "Build RAP receipt integrity benchmark from agent-payment threat models",
            "priority": 2,
            "swimlane": "RAP Receipt Integrity",
            "status": "next",
            "purpose": "Highest technical safety gate: prove payment success cannot become task success or reputation without full receipt validation.",
        },
        {
            "issue": 376,
            "title": "Add static Pay.sh/x402 discovery compatibility report",
            "priority": 3,
            "swimlane": "External Service Discovery",
            "status": "queued",
            "purpose": "Report-only discovery/proxy compatibility against x402/Pay.sh-style catalogs and paid API metadata.",
        },
        {
            "issue": 377,
            "title": "Refresh ADL/RAP AP2-FIDO mandate mapping",
            "priority": 4,
            "swimlane": "Audit and Compliance Readiness",
            "status": "queued",
            "purpose": "Update delegated authority mapping after AP2/FIDO/Verifiable Intent movement.",
        },
        {
            "issue": 378,
            "title": "Add AIP and Solana Agent Registry/SATI identity-reputation compatibility reports",
            "priority": 5,
            "swimlane": "Solana Agent Payments",
            "status": "queued",
            "purpose": "Report-only identity, attestation, capability, and reputation compatibility.",
        },
        {
            "issue": 379,
            "title": "Evaluate Solana Token-2022 extensions for RAP payment assets",
            "priority": 6,
            "swimlane": "Solana Agent Payments",
            "status": "queued",
            "purpose": "Decide which Token-2022 controls are candidates, blockers, or footguns for RAP payment assets.",
        },
        {
            "issue": 380,
            "title": "Classify MPP and ACP as non-canonical RAP adapter targets",
            "priority": 7,
            "swimlane": "Adapter Targets",
            "status": "lower-priority",
            "purpose": "Prevent Stripe/commerce alternatives from displacing Solana/x402/AP2 receipt-critical work.",
        },
    ]


def refresh_assumptions() -> list[dict[str, str]]:
    return [
        {
            "sourceIssue": "#361",
            "assumption": "x402/AP2/MCP/Solana/RAP layer split remains correct.",
            "refresh": "Still valid, but #377 should update AP2/FIDO/Verifiable Intent naming, mandate fields, and standardization status.",
        },
        {
            "sourceIssue": "#365",
            "assumption": "External tester cohort remains later and explicitly approval-gated.",
            "refresh": "Still valid; do not create cohort-0 execution until #374-#379 are complete or explicitly parked and Nissan approves bounded live devnet use.",
        },
        {
            "sourceIssue": "#366",
            "assumption": "Audit-readiness freeze needs authority, replay, privacy, settlement, and no-mainnet blockers.",
            "refresh": "Still valid; #375 should add receipt integrity threat benchmarks before docs refresh or live cohort planning.",
        },
        {
            "sourceIssue": "#206",
            "assumption": "Docs refresh should follow durable technical alignment.",
            "refresh": "Keep docs-only until #374 taxonomy/evidence lands or first implementation wave justifies a hub update.",
        },
    ]


def boundaries() -> dict[str, bool]:
    return {
        "researchSpecRoadmapOnly": True,
        "vendorContact": False,
        "signupRedemptionSpend": False,
        "credentialAccess": False,
        "deployment": False,
        "coolifySurfpoolDockerMutation": False,
        "liveMcpProviderInvocation": False,
        "devnetRun": False,
        "mainnetRun": False,
        "walletPaymentFacilitatorSettlementAction": False,
        "externalTesterExecution": False,
        "mainnetBlockedUntilOfficialAuditAndExplicitGoLive": True,
    }


def build_doc() -> dict[str, Any]:
    matrix = source_matrix()
    return {
        "mode": "agent-payments-standards-alignment-refresh",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "dateChecked": DATE_CHECKED,
        "status": "pass",
        "decision": "standards-refresh-ready-for-receipt-integrity-benchmark",
        "sourceMatrix": matrix,
        "sourceCount": sum(len(row["sources"]) for row in matrix),
        "protocolCount": len(matrix),
        "layerRules": layer_rules(),
        "issueLadder": issue_ladder(),
        "refreshAssumptions": refresh_assumptions(),
        "laterGateNotCreated": {
            "name": "bounded Solana devnet external tester cohort-0 execution",
            "reason": "Requires #374-#379 completion or explicit parking plus fresh bounded Nissan approval.",
        },
        "boundaries": boundaries(),
    }


def collect_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    matrix = doc.get("sourceMatrix", [])
    if len(matrix) != 10:
        findings.append({"path": "sourceMatrix", "reason": "Expected 10 protocol/project rows."})
    for row in matrix:
        for key in ("protocol", "layer", "confidence", "dateChecked", "sources", "relevance", "reddiagentAction"):
            if not row.get(key):
                findings.append({"path": f"sourceMatrix.{row.get('protocol', 'unknown')}.{key}", "reason": "Required field missing."})
        if row.get("dateChecked") != DATE_CHECKED:
            findings.append({"path": f"sourceMatrix.{row.get('protocol', 'unknown')}.dateChecked", "reason": "Unexpected date checked."})
    rules = " ".join(rule["rule"] for rule in doc.get("layerRules", []))
    required_phrases = [
        "x402 is payment evidence",
        "AP2/FIDO/Verifiable Intent is delegated authority",
        "MCP auth is protected resource access",
        "Solana is settlement/program evidence",
        "RAP binds receipt/accounting/dispute/eval/reputation evidence",
    ]
    for phrase in required_phrases:
        if phrase not in rules:
            findings.append({"path": "layerRules", "reason": f"Missing layer rule: {phrase}"})
    ladder = doc.get("issueLadder", [])
    if [row.get("issue") for row in ladder] != [374, 375, 376, 377, 378, 379, 380]:
        findings.append({"path": "issueLadder", "reason": "Unexpected issue order."})
    if doc.get("laterGateNotCreated", {}).get("name") != "bounded Solana devnet external tester cohort-0 execution":
        findings.append({"path": "laterGateNotCreated.name", "reason": "Live cohort gate must remain uncreated."})
    for key, expected in boundaries().items():
        if doc.get("boundaries", {}).get(key) is not expected:
            findings.append({"path": f"boundaries.{key}", "reason": f"Expected {expected!r}."})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write the fixture instead of printing JSON.")
    args = parser.parse_args()

    doc = build_doc()
    findings = collect_findings(doc)
    doc["findings"] = findings
    doc["status"] = "pass" if not findings else "fail"
    output = dump_json(doc)
    if args.write:
        FIXTURE.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
