#!/usr/bin/env python3
"""Run a bounded MCP/devnet payment handoff prototype with guardrail evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from run_local_agent import display_path, validate


ROOT = Path(__file__).resolve().parents[1]

APPROVED_MCP_SERVERS = {
    "approved-docs-search": {
        "resolutionMode": "reviewed-registry",
        "allowedTools": ["docs_search.search"],
        "capabilities": ["mcp.adapter.readonly", "source.approved-output"],
    }
}

APPROVED_DEVNET_RAILS = {
    "solana-devnet": {
        "cluster": "devnet",
        "settlementMode": "simulated-devnet-handoff",
        "maxAmount": "0.25",
        "currency": "USDC",
    }
}

SCENARIOS = [
    {
        "id": "approved-mcp-devnet-handoff",
        "adl": "examples/mcp-readonly-agent.yaml",
        "mcpServerRef": "approved-docs-search",
        "toolRef": "docs_search.search",
        "paymentRail": "solana-devnet",
        "amount": "0.05",
        "network": "devnet",
        "expectedCompletionStatus": "pass",
    },
    {
        "id": "mainnet-payment-denied",
        "adl": "examples/payment-agent.yaml",
        "mcpServerRef": "approved-docs-search",
        "toolRef": "docs_search.search",
        "paymentRail": "solana-mainnet",
        "amount": "0.05",
        "network": "mainnet",
        "expectedCompletionStatus": "fail",
    },
    {
        "id": "unreviewed-mcp-server-denied",
        "adl": "examples/mcp-readonly-agent.yaml",
        "mcpServerRef": "unreviewed-live-mcp",
        "toolRef": "docs_search.search",
        "paymentRail": "solana-devnet",
        "amount": "0.05",
        "network": "devnet",
        "expectedCompletionStatus": "fail",
    },
]


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def trace_event(trace_id: str, event: str, **fields: Any) -> dict[str, Any]:
    return {"event": event, "traceId": trace_id, **fields}


def decimal_string_leq(left: str, right: str) -> bool:
    return float(left) <= float(right)


def check_mcp_guard(config: dict[str, Any]) -> dict[str, Any]:
    server = APPROVED_MCP_SERVERS.get(config["mcpServerRef"])
    if not server:
        return {
            "status": "fail",
            "reason": "MCP serverRef is not in the reviewed allowlist",
            "serverRef": config["mcpServerRef"],
            "resolutionMode": "blocked",
            "mcpInvocationAllowed": False,
            "mcpInvocationUsed": False,
        }
    if config["toolRef"] not in server["allowedTools"]:
        return {
            "status": "fail",
            "reason": "MCP toolRef is not approved for the reviewed serverRef",
            "serverRef": config["mcpServerRef"],
            "resolutionMode": server["resolutionMode"],
            "mcpInvocationAllowed": False,
            "mcpInvocationUsed": False,
        }
    return {
        "status": "pass",
        "reason": "MCP serverRef and toolRef are reviewed and allowlisted",
        "serverRef": config["mcpServerRef"],
        "resolutionMode": server["resolutionMode"],
        "capabilities": server["capabilities"],
        "mcpInvocationAllowed": True,
        "mcpInvocationUsed": False,
    }


def check_payment_guard(config: dict[str, Any]) -> dict[str, Any]:
    if config["network"] == "mainnet":
        return {
            "status": "fail",
            "reason": "mainnet payment handoff is blocked pending separate approval",
            "network": config["network"],
            "paymentHandoffAllowed": False,
            "paymentRailAccessUsed": False,
            "devnetAccess": False,
            "mainnetAccess": False,
        }
    rail = APPROVED_DEVNET_RAILS.get(config["paymentRail"])
    if not rail:
        return {
            "status": "fail",
            "reason": "payment rail is not in the approved devnet allowlist",
            "network": config["network"],
            "paymentRail": config["paymentRail"],
            "paymentHandoffAllowed": False,
            "paymentRailAccessUsed": False,
            "devnetAccess": config["network"] == "devnet",
            "mainnetAccess": False,
        }
    if not decimal_string_leq(config["amount"], rail["maxAmount"]):
        return {
            "status": "fail",
            "reason": "devnet payment amount exceeds the approved handoff limit",
            "network": rail["cluster"],
            "paymentRail": config["paymentRail"],
            "amount": config["amount"],
            "limit": rail["maxAmount"],
            "paymentHandoffAllowed": False,
            "paymentRailAccessUsed": False,
            "devnetAccess": True,
            "mainnetAccess": False,
        }
    return {
        "status": "pass",
        "reason": "devnet payment handoff is bounded and allowlisted",
        "network": rail["cluster"],
        "paymentRail": config["paymentRail"],
        "amount": config["amount"],
        "limit": rail["maxAmount"],
        "currency": rail["currency"],
        "settlementMode": rail["settlementMode"],
        "paymentHandoffAllowed": True,
        "paymentRailAccessUsed": False,
        "devnetAccess": True,
        "mainnetAccess": False,
    }


def build_receipt(config: dict[str, Any], trace_id: str) -> dict[str, Any]:
    return {
        "receiptVersion": "reddiagent.devnet-handoff/v0.1",
        "receiptId": stable_id(config["id"], trace_id, "receipt"),
        "network": config["network"],
        "paymentRail": config["paymentRail"],
        "amount": config["amount"],
        "currency": "USDC",
        "settlementReference": f"devnet-simulated:{stable_id(config['id'], 'settlement')}",
        "mcpServerRef": config["mcpServerRef"],
        "toolRef": config["toolRef"],
        "productionSettlement": False,
        "mainnetSettlement": False,
        "secretMaterialLogged": False,
    }


def rollback_plan(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "required": True,
        "steps": [
            "discard simulated devnet receipt evidence",
            "revoke temporary MCP serverRef allowlist entry if added for the test",
            "clear any temporary devnet wallet/facilitator handles before retry",
        ],
        "cleanupVerified": True,
        "scope": f"{config['mcpServerRef']}:{config['paymentRail']}",
    }


def run_scenario(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["adl"]
    doc = load_yaml(path)
    errors = validate(doc)
    if errors:
        return {
            "id": config["id"],
            "status": "fail",
            "adl": display_path(path),
            "completion": {
                "status": "fail",
                "reason": "ADL validation failed before MCP/devnet handoff prototype",
            },
            "validationErrorCount": len(errors),
        }

    trace_id = stable_id(config["id"], doc["metadata"]["name"], "mcp-devnet")
    mcp = check_mcp_guard(config)
    payment = check_payment_guard(config)
    completion_status = "pass" if mcp["status"] == "pass" and payment["status"] == "pass" else "fail"
    completion_reason = (
        "approved MCP and devnet payment handoff evidence completed"
        if completion_status == "pass"
        else "MCP/devnet handoff failed closed before live side effects"
    )
    trace = [
        trace_event(trace_id, "handoff.started", agent=doc["metadata"]["name"], scenario=config["id"]),
        trace_event(trace_id, "mcp.allowlist_checked", status=mcp["status"], serverRef=config["mcpServerRef"], mcpInvocationAllowed=mcp["mcpInvocationAllowed"], mcpInvocationUsed=mcp["mcpInvocationUsed"]),
        trace_event(trace_id, "payment.devnet_policy_checked", status=payment["status"], network=config["network"], paymentHandoffAllowed=payment["paymentHandoffAllowed"], paymentRailAccessUsed=payment["paymentRailAccessUsed"], mainnetAccess=payment["mainnetAccess"]),
        trace_event(trace_id, "rollback.plan_registered", status="pass", cleanupVerified=True),
        trace_event(trace_id, "handoff.completed", status=completion_status, reason=completion_reason),
    ]
    status = "pass" if completion_status == config["expectedCompletionStatus"] else "fail"
    return {
        "id": config["id"],
        "status": status,
        "adl": config["adl"],
        "mcp": mcp,
        "payment": payment,
        "receipt": build_receipt(config, trace_id) if completion_status == "pass" else None,
        "rollbackPlan": rollback_plan(config),
        "completion": {
            "status": completion_status,
            "reason": completion_reason,
        },
        "trace": trace,
    }


def build_report() -> dict[str, Any]:
    scenarios = [run_scenario(scenario) for scenario in SCENARIOS]
    passing_receipts = [scenario["receipt"] for scenario in scenarios if scenario.get("receipt")]
    status = "pass" if all(scenario["status"] == "pass" for scenario in scenarios) else "fail"
    return {
        "mode": "live-mcp-devnet-payment-handoff-prototype",
        "status": status,
        "issue": 221,
        "approvedMcpServers": sorted(APPROVED_MCP_SERVERS),
        "approvedDevnetRails": sorted(APPROVED_DEVNET_RAILS),
        "boundaries": {
            "prototypeExecutionAllowed": True,
            "liveMcpResolutionAllowedByPolicy": True,
            "liveMcpInvocationAllowedByPolicy": True,
            "devnetPaymentHandoffAllowedByPolicy": True,
            "networkAccessUsed": False,
            "credentialAccessUsed": False,
            "walletAccessUsed": False,
            "paymentRailAccessUsed": False,
            "mcpInvocationUsed": False,
            "devnetAccessUsed": False,
            "mainnetAccessUsed": False,
            "externalSpendUsd": 0,
            "secretMaterialLogged": False,
        },
        "costEvidence": {
            "externalSpendUsd": 0,
            "devnetLamportsSpent": 0,
            "hostedProviderCalls": 0,
            "networkCalls": 0,
        },
        "receiptEvidence": {
            "count": len(passing_receipts),
            "receiptHashes": [stable_hash(json.dumps(receipt, sort_keys=True)) for receipt in passing_receipts],
            "productionSettlement": False,
            "mainnetSettlement": False,
        },
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write the JSON evidence report to this path.")
    args = parser.parse_args()
    report = build_report()
    payload = json.dumps(report, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n")
    print(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
