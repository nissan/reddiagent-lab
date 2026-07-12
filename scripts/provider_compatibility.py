#!/usr/bin/env python3
"""Emit provider compatibility reports for ReddiAgent examples."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["openai", "anthropic", "gemini", "ollama", "langgraph", "local-python"]


def report(path: Path, target: str) -> dict:
    doc = yaml.safe_load(path.read_text())
    harness = doc["harness"]
    model = doc["model"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    mcp_tools = [tool for tool in tools if tool.get("type") == "mcp"]
    warnings = []
    unsupported = []
    required_secrets = []
    required_hosted_services = []

    if target == "ollama" and model["requirements"].get("toolCalling"):
        warnings.append("Tool calling may require custom local harness parsing.")
    if target == "local-python":
        level = 1 if harness["runtime"]["target"] == "local-python" else 0
    elif target in ["openai", "anthropic", "gemini", "langgraph"]:
        level = 2
        required_secrets.append(f"{target.upper().replace('-', '_')}_API_KEY")
    else:
        level = 0

    if (extensions.get("x402") or {}).get("enabled"):
        warnings.append("Payment extension is dry-run only until receipt and policy enforcement land.")
        if target != "local-python":
            unsupported.append("real_settlement")

    if mcp_tools:
        warnings.append("MCP declarations are read-only adapter shapes until server resolution lands.")
        unsupported.append("mcp_execution")
        required_hosted_services.extend(
            f"mcp:{tool.get('serverRef', '<missing-serverRef>')}" for tool in mcp_tools
        )

    return {
        "agent": doc["metadata"]["name"],
        "target": target,
        "supported": not unsupported,
        "level": level,
        "warnings": warnings,
        "unsupportedFeatures": unsupported,
        "requiredSecrets": required_secrets,
        "requiredHostedServices": required_hosted_services,
        "suggestedFallback": "local-python",
    }


def main() -> int:
    examples = sorted((ROOT / "examples").glob("*.yaml"))
    reports = []
    for example in examples:
        for target in TARGETS:
            reports.append(report(example, target))
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
