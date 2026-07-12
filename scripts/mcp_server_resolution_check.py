#!/usr/bin/env python3
"""Static fail-closed checks for MCP server resolution requirements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]

LIVE_SERVER_FIELDS = {
    "url",
    "serverUrl",
    "command",
    "args",
    "env",
    "headers",
    "token",
    "apiKey",
    "secret",
    "credential",
}


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


def registry_by_id(registry: dict) -> dict[str, dict]:
    return {str(server.get("id")): server for server in registry.get("servers", [])}


def mcp_tools(adl: dict) -> list[dict]:
    return [tool for tool in (adl.get("harness") or {}).get("tools", []) if tool.get("type") == "mcp"]


def check_server(tool: dict, server: dict | None) -> list[dict]:
    tool_id = str(tool.get("id", "<unknown>"))
    server_ref = str(tool.get("serverRef", ""))
    tool_name = str(tool.get("toolName", ""))
    findings: list[dict] = []

    if not server:
        return [
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP serverRef is not present in the static reviewed registry.",
            }
        ]

    if server.get("resolutionMode") != "static-reviewed":
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP serverRef is not marked static-reviewed.",
                "resolutionMode": server.get("resolutionMode"),
            }
        )

    live_fields = sorted(LIVE_SERVER_FIELDS.intersection(server.keys()))
    if live_fields:
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP server registry embeds live resolution fields.",
                "fields": live_fields,
            }
        )

    if server.get("networkAccess") is not False or server.get("mcpInvocation") is not False:
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "Static server resolution checks must not grant network access or MCP invocation.",
            }
        )

    allowed_tools = server.get("allowedTools") or []
    if tool_name not in allowed_tools:
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP toolName is not allowed by the static reviewed registry.",
                "toolName": tool_name,
            }
        )

    if server.get("sourceGate") != "approved-source-output":
        findings.append(
            {
                "toolId": tool_id,
                "serverRef": server_ref,
                "status": "fail",
                "reason": "MCP serverRef must declare approved-source-output as its source gate.",
            }
        )

    return findings


def report(adl_path: Path, registry_path: Path) -> dict:
    adl = read_yaml(adl_path)
    registry = read_json(registry_path)
    servers = registry_by_id(registry)
    findings: list[dict] = []

    for tool in mcp_tools(adl):
        server_ref = str(tool.get("serverRef", ""))
        findings.extend(check_server(tool, servers.get(server_ref)))

    status = "fail" if findings else "pass"
    return {
        "adl": display_path(adl_path),
        "registry": display_path(registry_path),
        "mode": "static-mcp-server-resolution-check",
        "status": status,
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    args = parser.parse_args()

    result = report(args.adl, args.registry)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
