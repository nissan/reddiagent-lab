#!/usr/bin/env python3
"""Read-only adapter shape checks for ReddiAgent ADL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"

LIVE_MCP_FIELDS = {
    "serverUrl",
    "url",
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


def load_adl(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def validate_schema(doc: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    return [error.message for error in errors]


def check_mcp_shape(doc: dict) -> list[dict]:
    findings: list[dict] = []
    for tool in (doc.get("harness") or {}).get("tools", []):
        if tool.get("type") != "mcp":
            continue

        tool_id = tool.get("id", "<unknown>")
        for required in ("serverRef", "toolName"):
            if not tool.get(required):
                findings.append(
                    {
                        "toolId": tool_id,
                        "status": "fail",
                        "reason": f"MCP tool is missing required read-only adapter field: {required}",
                    }
                )

        live_fields = sorted(LIVE_MCP_FIELDS.intersection(tool.keys()))
        if live_fields:
            findings.append(
                {
                    "toolId": tool_id,
                    "status": "fail",
                    "reason": "MCP tool embeds live execution fields instead of a named serverRef.",
                    "fields": live_fields,
                }
            )

    return findings


def readiness_report(path: Path) -> dict:
    doc = load_adl(path)
    schema_errors = validate_schema(doc)
    findings = [
        {"toolId": "<schema>", "status": "fail", "reason": error}
        for error in schema_errors
    ]
    if not schema_errors:
        findings.extend(check_mcp_shape(doc))

    tools = (doc.get("harness") or {}).get("tools", [])
    mcp_tools = [tool for tool in tools if tool.get("type") == "mcp"]
    status = "fail" if findings else "pass"
    return {
        "path": display_path(path),
        "mode": "read-only-adapter-shape",
        "status": status,
        "adapter": "mcp",
        "mcpToolCount": len(mcp_tools),
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", type=Path)
    args = parser.parse_args()

    report = readiness_report(args.adl)
    print(json.dumps(report, indent=2))
    return 2 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
