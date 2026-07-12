#!/usr/bin/env python3
"""Static capability-policy checks for MCP tools and server refs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_CAPABILITIES = {"mcp.adapter.readonly"}


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def read_yaml(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def mcp_tools(adl: dict) -> list[dict]:
    return [tool for tool in (adl.get("harness") or {}).get("tools", []) if tool.get("type") == "mcp"]


def matching_policy(tool: dict, policies: list[dict]) -> dict | None:
    return next(
        (
            policy
            for policy in policies
            if policy.get("serverRef") == tool.get("serverRef")
            and policy.get("toolId") == tool.get("id")
            and policy.get("toolName") == tool.get("toolName")
        ),
        None,
    )


def check_policy(tool: dict, policy: dict | None) -> list[dict]:
    tool_id = str(tool.get("id", "<unknown>"))
    server_ref = str(tool.get("serverRef", ""))
    findings: list[dict] = []

    if not policy:
        return [
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP tool has no matching static capability policy.",
            }
        ]

    capabilities = set(policy.get("capabilities") or [])
    extra_capabilities = sorted(capabilities - ALLOWED_CAPABILITIES)
    missing_capabilities = sorted(ALLOWED_CAPABILITIES - capabilities)

    if missing_capabilities:
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP capability policy is missing required readonly capability.",
                "missingCapabilities": missing_capabilities,
            }
        )

    if extra_capabilities:
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP capability policy grants capabilities outside readonly adapter inspection.",
                "extraCapabilities": extra_capabilities,
            }
        )

    if policy.get("sourceGate") != "approved-source-output":
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP capability policy must require approved-source-output.",
            }
        )

    if (
        policy.get("networkAccess") is not False
        or policy.get("mcpInvocation") is not False
        or policy.get("paymentAccess") is not False
    ):
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP capability policy must not grant network, invocation, or payment access.",
            }
        )

    return findings


def report(adl_path: Path, policy_path: Path) -> dict:
    adl = read_yaml(adl_path)
    policy_doc = read_json(policy_path)
    policies = policy_doc.get("policies", [])
    findings: list[dict] = []

    for tool in mcp_tools(adl):
        findings.extend(check_policy(tool, matching_policy(tool, policies)))

    status = "fail" if findings else "pass"
    return {
        "adl": display_path(adl_path),
        "policy": display_path(policy_path),
        "mode": "static-mcp-capability-policy-check",
        "status": status,
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args()

    result = report(args.adl, args.policy)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
