#!/usr/bin/env python3
"""Report-only ADL to Agent Spec compatibility checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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


def instruction_mapping(instructions: object) -> dict:
    if isinstance(instructions, dict):
        if "inline" in instructions:
            return {"type": "inline", "value": instructions["inline"]}
        if "path" in instructions:
            return {"type": "path", "value": instructions["path"]}
    if isinstance(instructions, str):
        return {"type": "path", "value": instructions}
    return {"type": "unknown", "value": None}


def model_mapping(model: dict) -> dict:
    providers = model.get("providers") or {}
    requirements = model.get("requirements") or {}
    return {
        "preferredProvider": providers.get("preferred"),
        "fallbackProviders": providers.get("fallbacks", []),
        "capability": model.get("capability"),
        "requirements": {
            "toolCalling": bool(requirements.get("toolCalling")),
            "structuredOutput": bool(requirements.get("structuredOutput")),
            "contextWindow": requirements.get("contextWindow"),
            "modalities": requirements.get("modalities", []),
        },
    }


def tool_mapping(harness: dict) -> list[dict]:
    mapped = []
    for tool in harness.get("tools", []) or []:
        mapped.append(
            {
                "id": tool.get("id") or tool.get("toolName"),
                "type": tool.get("type"),
                "description": tool.get("description"),
                "serverRef": tool.get("serverRef"),
                "toolName": tool.get("toolName"),
                "inputSchema": tool.get("inputSchema"),
                "outputSchema": tool.get("outputSchema"),
                "schema": tool.get("schema"),
            }
        )
    return mapped


def red_extensions(doc: dict) -> list[str]:
    extensions = doc.get("extensions") or {}
    return [f"extensions.{key}" for key in sorted(extensions)]


def metadata_only_sections(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    sections = []
    if harness.get("policies"):
        sections.append("harness.policies")
    if harness.get("evalGates"):
        sections.append("harness.evalGates")
    if harness.get("memory"):
        sections.append("harness.memory")
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
        warnings.append("Some ReddiAgent sections can only be exported as metadata in this static Agent Spec mapping.")
    if "live_payment_execution" in unsupported:
        warnings.append("x402 payment data is metadata-only; no payment rail or settlement adapter is executed.")
    if "mcp_runtime_invocation" in unsupported:
        warnings.append("MCP tool declarations are static only; no server is resolved or invoked.")
    if "non_local_runtime_execution" in unsupported:
        warnings.append("Non-local runtime targets require a separate reviewed runtime adapter before execution.")
    return warnings


def mapped_agent_spec_document(path: Path, doc: dict, metadata_only: list[str]) -> dict:
    harness = doc.get("harness") or {}
    return {
        "format": "agent-spec-compatible-review",
        "source": display_path(path),
        "component": {
            "type": "agent",
            "name": doc["metadata"]["name"],
            "description": doc["metadata"].get("description"),
            "model": model_mapping(doc.get("model") or {}),
            "instructions": instruction_mapping(harness.get("instructions")),
            "tools": tool_mapping(harness),
            "metadata": {
                "reddiagentApiVersion": doc.get("apiVersion"),
                "reddiagentKind": doc.get("kind"),
                "metadataOnlySections": metadata_only,
                "extensions": doc.get("extensions") or {},
            },
        },
    }


def report_for(path: Path) -> dict:
    doc = read_adl(path)
    metadata_only = metadata_only_sections(doc)
    unsupported = unsupported_features(doc)
    return {
        "agent": doc["metadata"]["name"],
        "source": display_path(path),
        "target": "agent-spec",
        "supported": True,
        "lossless": not metadata_only and not unsupported,
        "warnings": warnings_for(metadata_only, unsupported),
        "unsupportedFeatures": unsupported,
        "metadataOnlyExtensions": metadata_only,
        "redactedOrMetadataOnlyExtensions": metadata_only,
        "requiredRuntimeAdapters": ["agent-spec-runtime-adapter"],
        **BOUNDARY_FLAGS,
        "mappedDocument": mapped_agent_spec_document(path, doc, metadata_only),
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
    documents = [report["mappedDocument"] for report in reports]
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
        "--export-agent-spec",
        action="store_true",
        help="Emit mapped Agent Spec review documents only when every input is lossless.",
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

    if args.export_agent_spec:
        diagnostics = loss_diagnostics(reports)
        if diagnostics:
            error_payload = {
                "error": "agent_spec_export_would_drop_reddi_semantics",
                "message": "Strict Agent Spec export refused because at least one input is not lossless.",
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
