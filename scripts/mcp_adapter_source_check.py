#!/usr/bin/env python3
"""Deterministic source checks for hypothetical MCP adapter outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from local_tool_registry import stable_hash
from source_check import check_tool_sources, summarize_source_checks


ROOT = Path(__file__).resolve().parents[1]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_fixture(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def fixture_to_tool_result(fixture: dict) -> dict:
    output = fixture.get("output") or {}
    return {
        "toolId": str(fixture.get("toolId", "")),
        "status": "success",
        "inputHash": stable_hash(
            {
                "adapter": fixture.get("adapter"),
                "serverRef": fixture.get("serverRef"),
                "toolName": fixture.get("toolName"),
            }
        ),
        "outputHash": stable_hash(output),
        "output": output,
    }


def report(path: Path) -> dict:
    fixture = load_fixture(path)
    tool_result = fixture_to_tool_result(fixture)
    source_checks = check_tool_sources([tool_result])
    summary = summarize_source_checks(source_checks)
    return {
        "path": display_path(path),
        "mode": "deterministic-adapter-output-source-check",
        "adapter": "mcp",
        "serverRef": fixture.get("serverRef"),
        "toolName": fixture.get("toolName"),
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "sourceChecks": source_checks,
        "sourceCheckSummary": summary,
        "status": summary["status"],
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
