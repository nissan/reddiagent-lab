#!/usr/bin/env python3
"""Report-only ADL to Agent Skills / SKILL.md export checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_adl(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def skill_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug or "agent-skill")[:64].strip("-") or "agent-skill"


def agent_skill_extension(doc: dict) -> dict:
    return (doc.get("extensions") or {}).get("agentSkills") or {}


def red_extensions(doc: dict) -> list[str]:
    extensions = doc.get("extensions") or {}
    return [f"extensions.{key}" for key in sorted(extensions) if key != "agentSkills"]


def metadata_only_sections(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    sections = []
    if doc.get("model"):
        sections.append("model")
    instructions = harness.get("instructions")
    if isinstance(instructions, dict) and instructions.get("path"):
        sections.append("harness.instructions.path")
    if harness.get("tools"):
        sections.append("harness.tools")
    if harness.get("dataSources"):
        sections.append("harness.dataSources")
    if harness.get("memory"):
        sections.append("harness.memory")
    if harness.get("policies"):
        sections.append("harness.policies")
    if harness.get("evalGates"):
        sections.append("harness.evalGates")
    if harness.get("runtime"):
        sections.append("harness.runtime")
    sections.extend(red_extensions(doc))
    return sections


def unsupported_features(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    features = []

    if harness.get("runtime", {}).get("target") not in (None, "local-python"):
        features.append("non_local_runtime_execution")

    if (extensions.get("x402") or {}).get("enabled"):
        features.append("live_payment_execution")

    for tool in harness.get("tools", []) or []:
        if tool.get("type") == "mcp":
            features.append("mcp_runtime_invocation")
            break

    return features


def warnings_for(metadata_only: list[str], unsupported: list[str]) -> list[str]:
    warnings = []
    if metadata_only:
        warnings.append("Some ReddiAgent sections can only be preserved as SKILL.md metadata or body notes.")
    if "live_payment_execution" in unsupported:
        warnings.append("x402 payment data is metadata-only; no wallet, facilitator, payment rail, or settlement adapter is executed.")
    if "mcp_runtime_invocation" in unsupported:
        warnings.append("MCP declarations are static only; no server is resolved or invoked.")
    if "non_local_runtime_execution" in unsupported:
        warnings.append("Non-local runtime targets require a separate reviewed runtime adapter before execution.")
    return warnings


def instruction_text(doc: dict) -> str:
    instructions = (doc.get("harness") or {}).get("instructions")
    if isinstance(instructions, dict):
        if instructions.get("inline"):
            return str(instructions["inline"])
        if instructions.get("path"):
            return f"Read the bundled instruction file before acting: {instructions['path']}"
    if isinstance(instructions, str):
        return f"Read the bundled instruction file before acting: {instructions}"
    return "Follow the ReddiAgent harness instructions captured in package metadata."


def allowed_tools_value(extension: dict) -> str | None:
    allowed = extension.get("allowedTools")
    if isinstance(allowed, list):
        return " ".join(str(item) for item in allowed)
    if isinstance(allowed, str):
        return allowed
    return None


def package_metadata(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> dict:
    return {
        "reddiagent.source": display_path(path),
        "reddiagent.apiVersion": str(doc.get("apiVersion", "")),
        "reddiagent.kind": str(doc.get("kind", "")),
        "reddiagent.metadataOnlySections": json.dumps(metadata_only, separators=(",", ":")),
        "reddiagent.unsupportedFeatures": json.dumps(unsupported, separators=(",", ":")),
        "reddiagent.runtimeExecutionAllowed": "false",
        "reddiagent.networkAccess": "false",
        "reddiagent.paymentAccess": "false",
        "reddiagent.mcpInvocation": "false",
    }


def frontmatter(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> dict:
    metadata = doc.get("metadata") or {}
    extension = agent_skill_extension(doc)
    fm = {
        "name": skill_name(metadata.get("name", "agent-skill")),
        "description": metadata.get("description") or f"Static skill package for {metadata.get('name', 'a ReddiAgent agent')}.",
    }
    if extension.get("license"):
        fm["license"] = extension["license"]
    if extension.get("compatibility"):
        fm["compatibility"] = extension["compatibility"]
    allowed_tools = allowed_tools_value(extension)
    if allowed_tools:
        fm["allowed-tools"] = allowed_tools
    fm["metadata"] = package_metadata(path, doc, metadata_only, unsupported)
    return fm


def body_sections(doc: dict, metadata_only: list[str], unsupported: list[str]) -> str:
    extension = agent_skill_extension(doc)
    lines = [
        "# Instructions",
        "",
        instruction_text(doc),
        "",
        "# ReddiAgent Boundary",
        "",
        "- Runtime execution is not allowed by this static export.",
        "- Network access is not allowed by this static export.",
        "- Payment access is not allowed by this static export.",
        "- MCP invocation is not allowed by this static export.",
    ]

    references = extension.get("references") or []
    scripts = extension.get("scripts") or []
    assets = extension.get("assets") or []
    if references:
        lines.extend(["", "# References", ""])
        lines.extend(f"- {item}" for item in references)
    if scripts:
        lines.extend(["", "# Scripts", ""])
        lines.extend(f"- {item} (static declaration only)" for item in scripts)
    if assets:
        lines.extend(["", "# Assets", ""])
        lines.extend(f"- {item}" for item in assets)
    if metadata_only or unsupported:
        lines.extend(["", "# Static Review Notes", ""])
        for section in metadata_only:
            lines.append(f"- Metadata-only: `{section}`")
        for feature in unsupported:
            lines.append(f"- Unsupported for execution: `{feature}`")
    return "\n".join(lines) + "\n"


def skill_md(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> str:
    fm = yaml.safe_dump(frontmatter(path, doc, metadata_only, unsupported), sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body_sections(doc, metadata_only, unsupported)}"


def mapped_document(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> dict:
    name = frontmatter(path, doc, metadata_only, unsupported)["name"]
    return {
        "format": "agent-skill-package-review",
        "skillDirectory": name,
        "source": display_path(path),
        "files": [
            {
                "path": f"{name}/SKILL.md",
                "content": skill_md(path, doc, metadata_only, unsupported),
            }
        ],
    }


def report_for(path: Path) -> dict:
    doc = read_adl(path)
    metadata_only = metadata_only_sections(doc)
    unsupported = unsupported_features(doc)
    return {
        "agent": doc["metadata"]["name"],
        "source": display_path(path),
        "target": "agent-skills-skill-md",
        "supported": True,
        "lossless": not metadata_only and not unsupported,
        "warnings": warnings_for(metadata_only, unsupported),
        "unsupportedFeatures": unsupported,
        "metadataOnlyExtensions": metadata_only,
        "redactedOrMetadataOnlyExtensions": metadata_only,
        "requiredRuntimeAdapters": [],
        **BOUNDARY_FLAGS,
        "mappedDocument": mapped_document(path, doc, metadata_only, unsupported),
    }


def loss_diagnostics(reports: list[dict]) -> list[dict]:
    diagnostics = []
    for report in reports:
        if report["lossless"]:
            continue
        diagnostics.append(
            {
                "agent": report["agent"],
                "source": report["source"],
                "lossless": False,
                "metadataOnlyExtensions": report["metadataOnlyExtensions"],
                "unsupportedFeatures": report["unsupportedFeatures"],
                "warnings": report["warnings"],
            }
        )
    return diagnostics


def export_payload(reports: list[dict], single: bool) -> object:
    packages = [report["mappedDocument"] for report in reports]
    return packages[0] if single else packages


def emit_payload(payload: object, output_format: str) -> None:
    if output_format == "yaml":
        print(yaml.safe_dump(payload, sort_keys=False))
        return
    print(json.dumps(payload, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--single", action="store_true", help="Emit one report object instead of a list.")
    parser.add_argument(
        "--export-skill-package",
        action="store_true",
        help="Emit static SKILL.md package files only when every input is lossless.",
    )
    parser.add_argument(
        "--output-format",
        choices=("json", "yaml"),
        default="json",
        help="Output format for reports or strict export payloads.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    if args.single and len(paths) != 1:
        print("--single requires exactly one ADL path", file=sys.stderr)
        return 2

    reports = [report_for(path) for path in paths]

    if args.export_skill_package:
        diagnostics = loss_diagnostics(reports)
        if diagnostics:
            error_payload = {
                "error": "agent_skill_export_would_drop_reddi_semantics",
                "message": "Strict SKILL.md package export refused because at least one input is not lossless.",
                "diagnostics": diagnostics,
                **BOUNDARY_FLAGS,
            }
            print(json.dumps(error_payload, indent=2), file=sys.stderr)
            return 3
        emit_payload(export_payload(reports, args.single), args.output_format)
        return 0

    payload: object = reports[0] if args.single else reports
    emit_payload(payload, args.output_format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
