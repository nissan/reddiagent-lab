#!/usr/bin/env python3
"""Static Vercel eve compatibility report for ReddiAgent ADL examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "tool-agent.yaml",
    ROOT / "examples" / "mcp-readonly-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
    ROOT / "examples" / "invalid" / "missing-instructions.yaml",
]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
    "deploymentAllowed": False,
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


def schema_errors(doc: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    rendered = []
    for error in errors:
        loc = ".".join(str(part) for part in error.path) or "<root>"
        rendered.append(f"{loc}: {error.message}")
    return rendered


def snake(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not slug:
        slug = "item"
    if slug[0].isdigit():
        slug = f"item_{slug}"
    return slug


def metadata_only_sections(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    sections = []
    for section, value in [
        ("harness.policies", harness.get("policies")),
        ("harness.evalGates", harness.get("evalGates")),
        ("harness.memory", harness.get("memory")),
        ("harness.dataSources", harness.get("dataSources")),
    ]:
        if value:
            sections.append(section)
    for key in sorted(extensions):
        if extensions.get(key):
            sections.append(f"extensions.{key}")
    return sections


def unsupported_features(doc: dict) -> list[str]:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    features = []
    if harness.get("runtime", {}).get("target") not in (None, "local-python"):
        features.append("non_local_runtime_execution")
    for tool in harness.get("tools", []) or []:
        if tool.get("type") == "mcp":
            features.append("mcp_runtime_invocation")
            break
    if (extensions.get("x402") or {}).get("enabled"):
        features.append("live_payment_execution")
    if extensions.get("receipts"):
        features.append("receipt_enforcement")
    if extensions.get("reputation"):
        features.append("reputation_emission")
    return features


def tool_manifest(doc: dict) -> list[dict]:
    tools = (doc.get("harness") or {}).get("tools") or []
    manifest = []
    for tool in tools:
        tool_id = tool.get("id") or tool.get("toolName") or "tool"
        tool_type = tool.get("type")
        path_prefix = "connections" if tool_type == "mcp" else "tools"
        entry = {
            "id": tool_id,
            "type": tool_type,
            "eveSlot": f"agent/{path_prefix}/{snake(tool_id)}.ts",
            "status": "metadata-only" if tool_type == "mcp" else "static-stub-plan",
            "description": tool.get("description"),
        }
        if tool_type == "mcp":
            entry["serverRef"] = tool.get("serverRef")
            entry["toolName"] = tool.get("toolName")
            entry["unsupportedFeature"] = "mcp_runtime_invocation"
        manifest.append(entry)
    return manifest


def eval_manifest(doc: dict) -> list[dict]:
    evals = (doc.get("harness") or {}).get("evalGates") or []
    return [
        {
            "id": gate.get("id"),
            "type": gate.get("type"),
            "eveSlot": f"evals/{snake(gate.get('id', 'eval'))}.eval.ts",
            "status": "static-eval-plan",
        }
        for gate in evals
    ]


def project_manifest(doc: dict, source: Path, errors: list[str]) -> dict:
    metadata = doc.get("metadata") or {}
    agent_name = metadata.get("name") or source.stem
    harness = doc.get("harness") or {}
    tools = tool_manifest(doc)
    evals = eval_manifest(doc)
    files = [
        {
            "path": "agent/instructions.md",
            "source": "harness.instructions.inline"
            if (harness.get("instructions") or {}).get("inline")
            else "harness.instructions.path",
            "status": "blocked-by-validation" if errors else "static-content-plan",
        },
        {
            "path": "agent/agent.ts",
            "source": "model + static boundary metadata",
            "status": "blocked-by-validation" if errors else "static-config-plan",
        },
    ]
    files.extend({"path": item["eveSlot"], "source": f"harness.tools.{item['id']}", "status": item["status"]} for item in tools)
    files.extend({"path": item["eveSlot"], "source": f"harness.evalGates.{item['id']}", "status": item["status"]} for item in evals)
    files.append(
        {
            "path": "agent/reddiagent.metadata.json",
            "source": "ReddiAgent sections that eve cannot enforce natively",
            "status": "metadata-only",
        }
    )
    return {
        "projectRoot": f"eve/{agent_name}",
        "files": files,
        "toolManifest": tools,
        "evalManifest": evals,
        "connections": [item for item in tools if item["type"] == "mcp"],
    }


def compatibility_status(errors: list[str], unsupported: list[str], metadata_only: list[str]) -> tuple[bool, str]:
    if errors:
        return False, "blocked-by-validation"
    if unsupported:
        return True, "report-ready-with-unsupported-runtime-features"
    if metadata_only:
        return True, "report-ready-with-metadata-only-semantics"
    return True, "report-ready"


def report_for(path: Path) -> dict:
    doc = read_adl(path)
    errors = schema_errors(doc)
    metadata_only = [] if errors else metadata_only_sections(doc)
    unsupported = ["validation_failed"] if errors else unsupported_features(doc)
    supported, status = compatibility_status(errors, unsupported, metadata_only)
    model = doc.get("model") or {}
    providers = model.get("providers") or {}
    harness = doc.get("harness") or {}
    return {
        "format": "vercel-eve-compatibility-report",
        "issue": 202,
        "target": "vercel-eve",
        "source": display_path(path),
        "agent": (doc.get("metadata") or {}).get("name"),
        "supported": supported,
        "status": status,
        "validationErrors": errors,
        "modelMapping": {
            "preferredProvider": providers.get("preferred"),
            "fallbackProviders": providers.get("fallbacks", []),
            "eveSlot": "agent/agent.ts model metadata",
            "runtimeModelResolution": "not-probed",
        },
        "instructionMapping": {
            "source": "harness.instructions.inline"
            if (harness.get("instructions") or {}).get("inline")
            else "harness.instructions.path",
            "eveSlot": "agent/instructions.md",
        },
        "metadataOnlySections": metadata_only,
        "unsupportedFeatures": unsupported,
        "projectManifest": project_manifest(doc, path, errors),
        **BOUNDARY_FLAGS,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--single", action="store_true", help="Emit one report object instead of a list.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    if args.single and len(paths) != 1:
        print("--single requires exactly one ADL path", file=sys.stderr)
        return 2
    reports = [report_for(path) for path in paths]
    payload: object = reports[0] if args.single else reports
    print(json.dumps(payload, indent=2))
    return 1 if any(not report["supported"] for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
