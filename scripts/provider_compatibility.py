#!/usr/bin/env python3
"""Emit provider compatibility reports for ReddiAgent examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["openai", "anthropic", "gemini", "ollama", "langgraph", "mcp-readonly", "local-python"]
REPORT_ONLY_BOUNDARY = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}


def load_adl(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def report(path: Path, target: str) -> dict:
    doc = load_adl(path)
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
    elif target == "mcp-readonly":
        level = 2 if mcp_tools else 0
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
        "boundary": REPORT_ONLY_BOUNDARY,
    }


def selected_targets(values: list[str]) -> list[str]:
    if not values or "all" in values:
        return TARGETS
    return values


def selected_examples(paths: list[str], agents: list[str]) -> list[Path]:
    examples = [Path(path) for path in paths] if paths else sorted((ROOT / "examples").glob("*.yaml"))
    resolved = [(path if path.is_absolute() else ROOT / path) for path in examples]
    if not agents:
        return resolved

    names = set(agents)
    selected = []
    for path in resolved:
        doc = load_adl(path)
        if doc["metadata"]["name"] in names:
            selected.append(path)
    return selected


def render_json(reports: list[dict]) -> str:
    return json.dumps(reports, indent=2) + "\n"


def render_summary(reports: list[dict]) -> str:
    lines = [
        "Provider compatibility report (report-only)",
        "boundary: runtimeExecutionAllowed=false networkAccess=false paymentAccess=false mcpInvocation=false",
    ]
    for item in reports:
        warnings = ",".join(item["warnings"]) if item["warnings"] else "none"
        unsupported = ",".join(item["unsupportedFeatures"]) if item["unsupportedFeatures"] else "none"
        lines.append(
            f"- {item['agent']} -> {item['target']}: "
            f"supported={str(item['supported']).lower()} level={item['level']} "
            f"warnings={warnings} unsupported={unsupported}"
        )
    return "\n".join(lines) + "\n"


def write_or_print(content: str, output: Path | None) -> None:
    if output is None:
        print(content, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", nargs="*", help="ADL example paths. Defaults to examples/*.yaml.")
    parser.add_argument(
        "--target",
        action="append",
        choices=["all", *TARGETS],
        default=[],
        help="Compatibility target to include. Repeat for multiple targets. Defaults to all.",
    )
    parser.add_argument(
        "--agent",
        action="append",
        default=[],
        help="Filter by metadata.name. Repeat for multiple agents.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="json",
        help="Output format. JSON remains the deterministic snapshot format.",
    )
    parser.add_argument("--output", type=Path, help="Write the report to a file instead of stdout.")
    parser.add_argument("--list-targets", action="store_true", help="List supported report-only targets.")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    if args.list_targets:
        print("\n".join(TARGETS))
        return 0

    examples = selected_examples(args.examples, args.agent)
    if not examples:
        print("No ADL examples matched the requested selection.", file=sys.stderr)
        return 1

    reports = []
    for example in examples:
        for target in selected_targets(args.target):
            reports.append(report(example, target))

    content = render_json(reports) if args.format == "json" else render_summary(reports)
    write_or_print(content, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
