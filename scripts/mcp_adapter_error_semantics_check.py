#!/usr/bin/env python3
"""Static error-semantics checks for deterministic MCP adapter fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATUSES = {"error", "denied"}
ALLOWED_ERROR_CODES = {
    "adapter.contract.invalid",
    "adapter.timeout",
    "adapter.unavailable",
    "capability.denied",
    "source.required",
}
FORBIDDEN_ERROR_FIELDS = {
    "rawError",
    "stack",
    "traceback",
    "headers",
    "credentials",
    "env",
    "serverUrl",
    "command",
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


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_error_semantics(fixture: dict) -> list[dict]:
    findings: list[dict] = []

    if fixture.get("adapter") != "mcp":
        findings.append(
            {
                "status": "fail",
                "field": "adapter",
                "reason": "MCP adapter error fixture must declare adapter=mcp.",
            }
        )

    if fixture.get("status") not in ALLOWED_STATUSES:
        findings.append(
            {
                "status": "fail",
                "field": "status",
                "reason": "MCP adapter error fixture status must be error or denied.",
            }
        )

    if fixture.get("output") is not None:
        findings.append(
            {
                "status": "fail",
                "field": "output",
                "reason": "MCP adapter error fixture must not include output payload data.",
            }
        )

    if fixture.get("completionImpact") != "required-gate-fail":
        findings.append(
            {
                "status": "fail",
                "field": "completionImpact",
                "reason": "MCP adapter errors must force required-gate failure.",
            }
        )

    for field in ["serverRef", "toolId", "toolName"]:
        if not non_empty_string(fixture.get(field)):
            findings.append(
                {
                    "status": "fail",
                    "field": field,
                    "reason": "MCP adapter error fixture identity fields must be non-empty strings.",
                }
            )

    error = fixture.get("error")
    if not isinstance(error, dict):
        findings.append(
            {
                "status": "fail",
                "field": "error",
                "reason": "MCP adapter error fixture must include a bounded error object.",
            }
        )
        return findings

    if error.get("code") not in ALLOWED_ERROR_CODES:
        findings.append(
            {
                "status": "fail",
                "field": "error.code",
                "reason": "MCP adapter error code is not in the reviewed static allowlist.",
            }
        )

    if not non_empty_string(error.get("message")):
        findings.append(
            {
                "status": "fail",
                "field": "error.message",
                "reason": "MCP adapter error must include a bounded builder-facing message.",
            }
        )

    if not isinstance(error.get("retryable"), bool):
        findings.append(
            {
                "status": "fail",
                "field": "error.retryable",
                "reason": "MCP adapter error retryability must be explicit.",
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
                "reason": "MCP adapter error fixture must not claim network, invocation, or payment access.",
            }
        )

    for field in sorted(FORBIDDEN_ERROR_FIELDS):
        if field in fixture or field in error:
            findings.append(
                {
                    "status": "fail",
                    "field": field,
                    "reason": "MCP adapter error fixture must not expose raw runtime, server, auth, or environment details.",
                }
            )

    return findings


def report(path: Path) -> dict:
    fixture = read_json(path)
    findings = check_error_semantics(fixture)
    return {
        "path": display_path(path),
        "mode": "static-mcp-adapter-error-semantics-check",
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
