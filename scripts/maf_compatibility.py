#!/usr/bin/env python3
"""Report-only ADL v0.2 to Microsoft Agent Framework (MAF) compatibility checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "v0.2" / "simple-agent.yaml",
    ROOT / "examples" / "v0.2" / "tool-contract-agent.yaml",
    ROOT / "examples" / "v0.2" / "payment-agent.yaml",
    ROOT / "examples" / "v0.2" / "delegation-research-agent.yaml",
]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}
PINNED = {
    "package": "agent-framework",
    "range": ">=1.12,<2",
    "factory": "ChatClientPromptAgentFactory",
}
# ADL v0.2 provider ids with a first-party MAF chat-client connector. MAF also
# ships Foundry, AzureOpenAI, and Bedrock connectors, but ADL v0.2 has no
# provider ids for those yet.
MAF_CONNECTION_KINDS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "gemini": "Gemini",
    "ollama": "Ollama",
}
REDDI_PAYMENT_EXTENSIONS = (
    ("x402", "maf-has-no-payment-surface"),
    ("receipts", "maf-has-no-receipt-surface"),
    ("reputation", "maf-has-no-reputation-surface"),
)


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_adl(path: Path) -> object:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def structural_errors(doc: object) -> list[str]:
    if not isinstance(doc, dict):
        return ["document: must be a mapping"]

    errors = []
    metadata = doc.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
        errors.append("metadata.name: required string is missing")

    harness = doc.get("harness")
    if not isinstance(harness, dict):
        errors.append("harness: must be a mapping")
    else:
        instructions = harness.get("instructions")
        if not isinstance(instructions, dict):
            errors.append(
                "harness.instructions: must be an object with inline or path (bare strings are the legacy v0.1 shape)"
            )
        elif not isinstance(instructions.get("inline"), str) and not isinstance(instructions.get("path"), str):
            errors.append("harness.instructions: must define inline or path as a string")
        tools = harness.get("tools")
        if tools is not None and not isinstance(tools, list):
            errors.append("harness.tools: must be a list")

    model = doc.get("model")
    if model is not None and not isinstance(model, dict):
        errors.append("model: must be a mapping")

    extensions = doc.get("extensions")
    if extensions is not None and not isinstance(extensions, dict):
        errors.append("extensions: must be a mapping")

    return errors


def categorize(doc: dict) -> dict:
    supported: list[dict] = []
    unsupported: list[dict] = []
    degraded: list[dict] = []
    metadata_only: list[str] = []
    loss: list[dict] = []

    metadata = doc.get("metadata") or {}
    harness = doc.get("harness") or {}
    model = doc.get("model") or {}
    extensions = doc.get("extensions") or {}

    supported.append({"requirement": "metadata.name", "mafTarget": "name / displayName"})
    if metadata.get("description"):
        supported.append({"requirement": "metadata.description", "mafTarget": "description"})

    instructions = harness.get("instructions") or {}
    if isinstance(instructions.get("inline"), str):
        supported.append({"requirement": "harness.instructions.inline", "mafTarget": "instructions"})
    elif isinstance(instructions.get("path"), str):
        degraded.append(
            {
                "requirement": "harness.instructions.path",
                "mafTarget": "instructions",
                "degradedTo": "path-reference-metadata",
            }
        )
        loss.append(
            {
                "code": "adl-instruction-path-not-inlined",
                "path": "harness.instructions.path",
                "detail": "MAF `kind: Prompt` instructions are inline; the referenced file is not read during static review.",
            }
        )

    providers = model.get("providers") or {}
    preferred = providers.get("preferred")
    if preferred:
        connection_kind = MAF_CONNECTION_KINDS.get(preferred)
        if connection_kind:
            supported.append(
                {
                    "requirement": "model.providers.preferred",
                    "mafTarget": f"model.connection.kind={connection_kind}",
                    "note": "static metadata only; ADL carries no concrete model id, so model.id is left to =Env.* PowerFx interpolation",
                }
            )
        else:
            degraded.append(
                {
                    "requirement": "model.providers.preferred",
                    "mafTarget": "model.connection",
                    "degradedTo": "unmapped-provider-metadata",
                }
            )
            loss.append(
                {
                    "code": "no-maf-connector-for-provider",
                    "path": "model.providers.preferred",
                    "detail": f"No first-party MAF connector for provider '{preferred}'.",
                }
            )
    if providers.get("fallbacks"):
        degraded.append(
            {
                "requirement": "model.providers.fallbacks",
                "mafTarget": "model.connection",
                "degradedTo": "static-metadata",
            }
        )
        loss.append(
            {
                "code": "maf-prompt-single-model-connection",
                "path": "model.providers.fallbacks",
                "detail": "MAF `kind: Prompt` declares one model connection; ADL fallback providers survive as metadata only.",
            }
        )
    if model.get("capability"):
        supported.append(
            {
                "requirement": "model.capability",
                "mafTarget": "model.id selection input",
                "note": "static metadata only",
            }
        )

    requirements = model.get("requirements") or {}
    if requirements.get("toolCalling"):
        supported.append(
            {"requirement": "model.requirements.toolCalling", "mafTarget": "function tools / MCP tools"}
        )
    if requirements.get("structuredOutput"):
        degraded.append(
            {
                "requirement": "model.requirements.structuredOutput",
                "mafTarget": "outputSchema",
                "degradedTo": "empty-output-schema-slot",
            }
        )
        loss.append(
            {
                "code": "adl-has-no-output-schema",
                "path": "model.requirements.structuredOutput",
                "detail": "MAF exposes an outputSchema slot, but ADL v0.2 only carries a boolean structuredOutput requirement, so no schema exists to export. Tracked as issue #389 (first-class model.outputSchema).",
            }
        )
    if requirements.get("contextWindow"):
        supported.append(
            {
                "requirement": "model.requirements.contextWindow",
                "mafTarget": "model selection input",
                "note": "static metadata only",
            }
        )
    if requirements.get("modalities"):
        supported.append(
            {
                "requirement": "model.requirements.modalities",
                "mafTarget": "model selection input",
                "note": "static metadata only",
            }
        )

    for tool in harness.get("tools") or []:
        tool_id = tool.get("id") or tool.get("toolName") or "tool"
        tool_type = tool.get("type")
        if tool_type == "function":
            supported.append(
                {
                    "requirement": f"harness.tools.{tool_id}",
                    "toolType": "function",
                    "mafTarget": "function tool (static shape only)",
                }
            )
        elif tool_type == "mcp":
            supported.append(
                {
                    "requirement": f"harness.tools.{tool_id}",
                    "toolType": "mcp",
                    "mafTarget": "MCP tool (MAF native MCP client)",
                    "note": "static declaration only; no server is resolved or invoked",
                }
            )
        else:
            degraded.append(
                {
                    "requirement": f"harness.tools.{tool_id}",
                    "toolType": tool_type,
                    "degradedTo": "code-first-function-tool",
                }
            )
            loss.append(
                {
                    "code": "maf-no-declarative-tool-type",
                    "path": f"harness.tools.{tool_id}",
                    "detail": f"MAF `kind: Prompt` has no declarative '{tool_type}' tool; a code-first function wrapper would be required.",
                }
            )

    if harness.get("policies"):
        degraded.append(
            {
                "requirement": "harness.policies",
                "mafTarget": "function-approval middleware",
                "degradedTo": "function-approval-middleware",
            }
        )
        loss.append(
            {
                "code": "maf-approval-middleware-lacks-policy-semantics",
                "path": "harness.policies",
                "detail": "MAF function-approval middleware can gate calls but has no budget, scope, or rate semantics; ADL policies must remain enforced by ReddiAgent.",
            }
        )
    if harness.get("evalGates"):
        degraded.append(
            {
                "requirement": "harness.evalGates",
                "mafTarget": "Foundry evaluation (external)",
                "degradedTo": "foundry-external",
            }
        )
        loss.append(
            {
                "code": "maf-eval-gates-foundry-external",
                "path": "harness.evalGates",
                "detail": "MAF has no eval-gates-as-completion-contracts; Foundry evaluation is external and Azure-coupled.",
            }
        )
    if harness.get("observability"):
        degraded.append(
            {
                "requirement": "harness.observability",
                "mafTarget": "OpenTelemetry GenAI instrumentation",
                "degradedTo": "otel-advisory",
            }
        )
        loss.append(
            {
                "code": "maf-observability-otel-advisory",
                "path": "harness.observability",
                "detail": "MAF emits OTel GenAI spans, but ADL required-event, redaction, and retention contracts are advisory only in MAF.",
            }
        )
    if harness.get("memory"):
        metadata_only.append("harness.memory")
        loss.append(
            {
                "code": "maf-no-declarative-memory-contract",
                "path": "harness.memory",
                "detail": "MAF `kind: Prompt` has no declarative memory contract; ADL memory settings survive as metadata only.",
            }
        )

    for key, reason in REDDI_PAYMENT_EXTENSIONS:
        if extensions.get(key):
            metadata_only.append(f"extensions.{key}")
            unsupported.append({"requirement": f"extensions.{key}", "reason": reason})
            loss.append(
                {
                    "code": reason,
                    "path": f"extensions.{key}",
                    "detail": f"MAF has no x402/AP2, receipt, or reputation surface; extensions.{key} is metadata-only and unsupported for execution.",
                }
            )
    reddi_keys = {key for key, _ in REDDI_PAYMENT_EXTENSIONS}
    for key in sorted(extensions):
        if key not in reddi_keys and extensions.get(key):
            metadata_only.append(f"extensions.{key}")

    return {
        "supportedRequirements": supported,
        "unsupportedRequirements": unsupported,
        "degradedRequirements": degraded,
        "metadataOnlyExtensions": metadata_only,
        "lossMetadata": loss,
    }


def warnings_for(buckets: dict) -> list[str]:
    warnings = []
    if buckets["degradedRequirements"]:
        warnings.append(
            "Some ReddiAgent sections degrade in MAF; they must remain enforced by ReddiAgent until target enforcement exists."
        )
    if buckets["unsupportedRequirements"]:
        warnings.append(
            "x402 payment, receipt, and reputation data is metadata-only; MAF has no payment surface and no rail is executed."
        )
    if any(item.get("toolType") == "mcp" for item in buckets["supportedRequirements"]):
        warnings.append("MCP tool declarations are static only; no server is resolved or invoked.")
    return warnings


def maf_prompt_export(doc: dict) -> tuple[str | None, str | None]:
    """Best-effort `kind: Prompt` YAML when the core quartet (name, description,
    instructions, model connection) maps losslessly. Other sections may still
    be degraded or metadata-only; their loss is recorded in the report."""
    metadata = doc.get("metadata") or {}
    instructions = (doc.get("harness") or {}).get("instructions") or {}
    if not isinstance(instructions.get("inline"), str):
        return None, "instructions-path-ref-not-inlined"
    preferred = ((doc.get("model") or {}).get("providers") or {}).get("preferred")
    connection_kind = MAF_CONNECTION_KINDS.get(preferred)
    if not connection_kind:
        return None, "no-maf-connector-for-preferred-provider"

    prompt = {
        "kind": "Prompt",
        "name": metadata["name"],
        "displayName": metadata["name"],
    }
    if metadata.get("description"):
        prompt["description"] = metadata["description"]
    prompt["instructions"] = instructions["inline"]
    # ADL carries capability + provider, never a concrete model id or endpoint;
    # both are deferred to MAF PowerFx environment interpolation.
    prompt["model"] = {
        "id": "=Env.REDDIAGENT_MODEL_ID",
        "connection": {"kind": connection_kind, "endpoint": "=Env.REDDIAGENT_MODEL_ENDPOINT"},
    }
    return yaml.safe_dump(prompt, sort_keys=False), None


def unsupported_report(path: Path, doc: object, errors: list[str]) -> dict:
    agent = None
    if isinstance(doc, dict):
        metadata = doc.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("name"), str):
            agent = metadata["name"]
    return {
        "agent": agent,
        "source": display_path(path),
        "target": "maf",
        "supported": False,
        "lossless": False,
        "structuralErrors": errors,
        "warnings": ["Document failed static structural review; no MAF mapping was attempted."],
        "supportedRequirements": [],
        "unsupportedRequirements": [],
        "degradedRequirements": [],
        "metadataOnlyExtensions": [],
        "lossMetadata": [],
        "pinned": PINNED,
        "mafPromptYamlOmitted": {"reason": "structural-errors"},
        **BOUNDARY_FLAGS,
    }


def report_for(path: Path) -> dict:
    try:
        doc = read_adl(path)
    except (OSError, yaml.YAMLError) as exc:
        return unsupported_report(path, None, [f"unreadable: {exc}"])

    errors = structural_errors(doc)
    if errors:
        return unsupported_report(path, doc, errors)

    buckets = categorize(doc)
    lossless = not (
        buckets["unsupportedRequirements"]
        or buckets["degradedRequirements"]
        or buckets["metadataOnlyExtensions"]
        or buckets["lossMetadata"]
    )
    report = {
        "agent": doc["metadata"]["name"],
        "source": display_path(path),
        "target": "maf",
        "supported": True,
        "lossless": lossless,
        "structuralErrors": [],
        "warnings": warnings_for(buckets),
        **buckets,
        "pinned": PINNED,
        **BOUNDARY_FLAGS,
    }
    prompt_yaml, omit_reason = maf_prompt_export(doc)
    if prompt_yaml is not None:
        report["mafPromptYaml"] = prompt_yaml
    else:
        report["mafPromptYamlOmitted"] = {"reason": omit_reason}
    return report


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
