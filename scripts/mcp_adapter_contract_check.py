#!/usr/bin/env python3
"""Static contract checks for deterministic MCP adapter fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOP_LEVEL = ["adapter", "serverRef", "toolId", "toolName", "output"]
REQUIRED_OUTPUT_FIELDS = ["title", "url", "snippet"]
FORBIDDEN_LIVE_FIELDS = ["serverUrl", "command", "env", "headers", "credentials"]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_contract(fixture: dict) -> list[dict]:
    findings: list[dict] = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in fixture:
            findings.append(
                {
                    "status": "fail",
                    "field": field,
                    "reason": "MCP adapter fixture is missing a required top-level field.",
                }
            )

    if fixture.get("adapter") != "mcp":
        findings.append(
            {
                "status": "fail",
                "field": "adapter",
                "reason": "MCP adapter fixture must declare adapter=mcp.",
            }
        )

    for field in ["serverRef", "toolId", "toolName"]:
        if field in fixture and not non_empty_string(fixture.get(field)):
            findings.append(
                {
                    "status": "fail",
                    "field": field,
                    "reason": "MCP adapter fixture identity fields must be non-empty strings.",
                }
            )

    for field in FORBIDDEN_LIVE_FIELDS:
        if field in fixture:
            findings.append(
                {
                    "status": "fail",
                    "field": field,
                    "reason": "MCP adapter fixture must not embed live server, process, auth, or credential fields.",
                }
            )

    if (
        fixture.get("networkAccess") is True
        or fixture.get("mcpInvocation") is True
        or fixture.get("paymentAccess") is True
    ):
        findings.append(
            {
                "status": "fail",
                "field": "access",
                "reason": "MCP adapter fixture must not claim network, invocation, or payment access.",
            }
        )

    output = fixture.get("output")
    if not isinstance(output, dict):
        findings.append(
            {
                "status": "fail",
                "field": "output",
                "reason": "MCP adapter fixture output must be an object.",
            }
        )
        return findings

    for field in REQUIRED_OUTPUT_FIELDS:
        if not non_empty_string(output.get(field)):
            findings.append(
                {
                    "status": "fail",
                    "field": f"output.{field}",
                    "reason": "MCP adapter fixture output must include non-empty title, url, and snippet strings.",
                }
            )

    return findings


def report(path: Path) -> dict:
    fixture = read_json(path)
    findings = check_contract(fixture)
    return {
        "path": display_path(path),
        "mode": "static-mcp-adapter-contract-check",
        "adapter": fixture.get("adapter"),
        "serverRef": fixture.get("serverRef"),
        "toolName": fixture.get("toolName"),
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "status": "fail" if findings else "pass",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    result = report(args.fixture)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
