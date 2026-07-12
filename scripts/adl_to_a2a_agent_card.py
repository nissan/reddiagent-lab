#!/usr/bin/env python3
"""Report-only ADL to A2A Agent Card export checks."""

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
A2A_PROTOCOL_VERSION = "1.0"
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "agent"


def red_extensions(doc: dict) -> list[str]:
    extensions = doc.get("extensions") or {}
    return [f"extensions.{key}" for key in sorted(extensions)]


def metadata_only_sections(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    sections = []
    if harness.get("instructions"):
        sections.append("harness.instructions")
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
    sections.extend(red_extensions(doc))
    return sections


def unsupported_features(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    features = []

    if harness.get("runtime", {}).get("target") != "local-python":
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
        warnings.append("Some ReddiAgent sections can only be exported as Agent Card metadata in this static mapping.")
    if "live_payment_execution" in unsupported:
        warnings.append("x402 payment data is metadata-only; no wallet, facilitator, payment rail, or settlement adapter is executed.")
    if "mcp_runtime_invocation" in unsupported:
        warnings.append("MCP tool declarations are static only; no server is resolved or invoked.")
    if "non_local_runtime_execution" in unsupported:
        warnings.append("Non-local runtime targets require a separate reviewed A2A runtime adapter before execution.")
    return warnings


def input_modes(doc: dict) -> list[str]:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    return a2a.get("defaultInputModes") or ["text/plain"]


def output_modes(doc: dict) -> list[str]:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    requirements = (doc.get("model") or {}).get("requirements") or {}
    if a2a.get("defaultOutputModes"):
        return a2a["defaultOutputModes"]
    if requirements.get("structuredOutput"):
        return ["text/plain", "application/json"]
    return ["text/plain"]


def capabilities(doc: dict) -> dict:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    configured = a2a.get("capabilities") or {}
    return {
        "streaming": bool(configured.get("streaming", False)),
        "pushNotifications": bool(configured.get("pushNotifications", False)),
        "extensions": configured.get("extensions", []),
        "extendedAgentCard": bool(configured.get("extendedAgentCard", False)),
    }


def supported_interfaces(doc: dict) -> list[dict]:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    configured = a2a.get("supportedInterfaces") or []
    if configured:
        return configured

    name = doc.get("metadata", {}).get("name", "agent")
    return [
        {
            "url": f"https://example.invalid/a2a/{slugify(name)}",
            "protocolBinding": "HTTP+JSON",
            "protocolVersion": A2A_PROTOCOL_VERSION,
        }
    ]


def skill_from_tool(tool: dict) -> dict:
    skill_id = tool.get("id") or tool.get("toolName") or "tool"
    return {
        "id": skill_id,
        "name": skill_id.replace("_", " ").replace("-", " ").title(),
        "description": tool.get("description") or f"Static declaration for ADL tool {skill_id}.",
        "tags": [tag for tag in ["tool", tool.get("type")] if tag],
    }


def skills(doc: dict) -> list[dict]:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    if a2a.get("skills"):
        return a2a["skills"]

    harness = doc.get("harness") or {}
    tools = harness.get("tools") or []
    if tools:
        return [skill_from_tool(tool) for tool in tools]

    name = doc.get("metadata", {}).get("name", "agent")
    return [
        {
            "id": slugify(name),
            "name": name.replace("-", " ").replace("_", " ").title(),
            "description": doc.get("metadata", {}).get("description") or "Static ReddiAgent capability.",
            "tags": ["reddiagent", (doc.get("model") or {}).get("capability", "agent")],
        }
    ]


def security_fields(doc: dict) -> dict:
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    fields = {}
    if a2a.get("securitySchemes") is not None:
        fields["securitySchemes"] = a2a["securitySchemes"]
    if a2a.get("securityRequirements") is not None:
        fields["securityRequirements"] = a2a["securityRequirements"]
    return fields


def agent_card(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> dict:
    metadata = doc.get("metadata") or {}
    a2a = (doc.get("extensions") or {}).get("a2a") or {}
    card = {
        "name": metadata["name"],
        "description": metadata.get("description") or "",
        "supportedInterfaces": supported_interfaces(doc),
        "version": a2a.get("version") or "0.1.0",
        "capabilities": capabilities(doc),
        "defaultInputModes": input_modes(doc),
        "defaultOutputModes": output_modes(doc),
        "skills": skills(doc),
        "metadata": {
            "reddiagentApiVersion": doc.get("apiVersion"),
            "reddiagentKind": doc.get("kind"),
            "source": display_path(path),
            "metadataOnlySections": metadata_only,
            "unsupportedFeatures": unsupported,
            "extensions": doc.get("extensions") or {},
            **BOUNDARY_FLAGS,
        },
    }
    if a2a.get("provider"):
        card["provider"] = a2a["provider"]
    if a2a.get("documentationUrl"):
        card["documentationUrl"] = a2a["documentationUrl"]
    card.update(security_fields(doc))
    return card


def mapped_document(path: Path, doc: dict, metadata_only: list[str], unsupported: list[str]) -> dict:
    return {
        "format": "a2a-agent-card-review",
        "targetPath": "/.well-known/agent-card.json",
        "source": display_path(path),
        "agentCard": agent_card(path, doc, metadata_only, unsupported),
    }


def report_for(path: Path) -> dict:
    doc = read_adl(path)
    metadata_only = metadata_only_sections(doc)
    unsupported = unsupported_features(doc)
    return {
        "agent": doc["metadata"]["name"],
        "source": display_path(path),
        "target": "a2a-agent-card",
        "supported": True,
        "lossless": not metadata_only and not unsupported,
        "warnings": warnings_for(metadata_only, unsupported),
        "unsupportedFeatures": unsupported,
        "metadataOnlyExtensions": metadata_only,
        "redactedOrMetadataOnlyExtensions": metadata_only,
        "requiredRuntimeAdapters": ["a2a-runtime-adapter"],
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
    documents = [report["mappedDocument"]["agentCard"] for report in reports]
    return documents[0] if single else documents


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
        "--export-agent-card",
        action="store_true",
        help="Emit A2A Agent Card JSON only when every input is lossless.",
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

    if args.export_agent_card:
        diagnostics = loss_diagnostics(reports)
        if diagnostics:
            error_payload = {
                "error": "a2a_agent_card_export_would_drop_reddi_semantics",
                "message": "Strict A2A Agent Card export refused because at least one input is not lossless.",
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
