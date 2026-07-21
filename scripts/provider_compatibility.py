#!/usr/bin/env python3
"""Emit provider compatibility reports for ReddiAgent examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml

from adl_v02_conformance import conformance_report


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
TARGETS = ["openai", "anthropic", "gemini", "ollama", "langgraph", "mcp-readonly", "local-python"]
MODEL_PROVIDER_IDS = ["openai", "anthropic", "gemini", "ollama"]
HOSTED_MODEL_PROVIDERS = {
    "openai": True,
    "anthropic": True,
    "gemini": True,
    "ollama": False,
}
PROVIDER_SECRETS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
PROVIDER_CAPABILITIES = {
    "openai": {
        "capabilities": {"chat", "reasoning", "code", "vision", "audio", "embedding"},
        "modalities": {"text", "image", "audio", "embedding"},
        "contextWindow": 128000,
        "maxOutputTokens": 16384,
        "toolCalling": True,
        "structuredOutput": True,
        "streaming": True,
        "jsonMode": True,
    },
    "anthropic": {
        "capabilities": {"chat", "reasoning", "code", "vision"},
        "modalities": {"text", "image"},
        "contextWindow": 200000,
        "maxOutputTokens": 8192,
        "toolCalling": True,
        "structuredOutput": True,
        "streaming": True,
        "jsonMode": False,
    },
    "gemini": {
        "capabilities": {"chat", "reasoning", "code", "vision", "audio", "embedding"},
        "modalities": {"text", "image", "audio", "embedding"},
        "contextWindow": 1000000,
        "maxOutputTokens": 8192,
        "toolCalling": True,
        "structuredOutput": True,
        "streaming": True,
        "jsonMode": True,
    },
    "ollama": {
        "capabilities": {"chat", "code", "embedding"},
        "modalities": {"text", "embedding"},
        "contextWindow": 32000,
        "maxOutputTokens": 4096,
        "toolCalling": "degraded",
        "structuredOutput": "degraded",
        "streaming": True,
        "jsonMode": "degraded",
    },
}
REPORT_ONLY_BOUNDARY = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}
OPENAI_COMPATIBILITY_MODE = "openai-adapter-compatibility-only"
ANTHROPIC_COMPATIBILITY_MODE = "anthropic-mcp-compatibility-only"
GEMINI_COMPATIBILITY_MODE = "gemini-provider-compatibility-only"
OLLAMA_COMPATIBILITY_MODE = "ollama-local-provider-compatibility-only"
LANGGRAPH_COMPATIBILITY_MODE = "langgraph-compatibility-report-only"
ADL_V02_SCHEMA_VALIDATION_UNSUPPORTED = "adl_v0_2_schema_validation"
MODEL_REQUIREMENT_UNSUPPORTED_PREFIX = "model_requirement"
PROVIDER_NOT_DECLARED_UNSUPPORTED = "provider_not_declared"


def load_adl(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def object_or_empty(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def load_v02_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def validation_error_path(error: jsonschema.ValidationError) -> str:
    if error.path:
        return ".".join(str(part) for part in error.path)
    return "<root>"


def adl_v02_validation_errors(doc: dict) -> list[jsonschema.ValidationError]:
    if doc.get("apiVersion") != "reddiagent.dev/v0.2":
        return []
    validator = jsonschema.Draft202012Validator(load_v02_schema())
    return sorted(validator.iter_errors(doc), key=lambda error: list(error.path))


def unsupported_schema_report(path: Path, doc: dict, target: str, errors: list[jsonschema.ValidationError]) -> dict:
    metadata = object_or_empty(doc.get("metadata"))
    model = object_or_empty(doc.get("model"))
    requirements = object_or_empty(model.get("requirements"))
    diagnostics = [
        {
            "path": validation_error_path(error),
            "message": error.message,
        }
        for error in errors
    ]
    result = {
        "agent": metadata.get("name", path.stem),
        "target": target,
        "supported": False,
        "level": 0,
        "warnings": ["ADL v0.2 schema validation failed; provider compatibility report refused."],
        "unsupportedFeatures": [ADL_V02_SCHEMA_VALIDATION_UNSUPPORTED],
        "providerResolution": {
            "requestedTarget": target,
            "orderedCandidates": ordered_provider_candidates(doc),
            "selectedProvider": None,
            "selectedRole": "schema-invalid",
            "hostedProvider": False,
        },
        "modelCapabilityRequirements": {
            "vocabularyVersion": "adl-v0.2-model-requirements",
            "provider": None,
            "capability": model.get("capability"),
            "requested": requirements,
            "supportedRequirements": [],
            "unsupportedRequirements": [],
            "degradedRequirements": [],
            "lossMetadata": [],
        },
        "requiredSecrets": [],
        "requiredHostedServices": [],
        "suggestedFallback": "fix-adl-v0.2-schema-errors",
        "boundary": REPORT_ONLY_BOUNDARY,
        "compatibilityMode": "provider-compatibility-report-refused",
        "dataSourceTypes": [],
        "sourceBoundary": [],
        "validationDiagnostics": diagnostics,
    }
    if doc.get("apiVersion") == "reddiagent.dev/v0.2":
        result["conformance"] = conformance_metadata(path)
    return result


def conformance_metadata(path: Path) -> dict:
    report = conformance_report(path)
    return {
        "requestedLevel": report["requestedLevel"],
        "achievedLevel": report["achievedLevel"],
        "status": report["status"],
        "missingFieldsByLevel": report["missingFieldsByLevel"],
        "forbiddenCapabilitiesByLevel": report["forbiddenCapabilitiesByLevel"],
    }


def source_boundary_metadata(doc: dict) -> list[dict]:
    sources = doc.get("harness", {}).get("dataSources", [])
    return [
        {
            "id": source.get("id"),
            "type": source.get("type"),
            "sourceRef": source.get("sourceRef"),
            "trust": source.get("trust"),
            "citationRequired": source.get("citationRequired"),
            "sourceCheckRequired": (source.get("sourceCheck") or {}).get("required"),
            "sourceCheckExpectation": (source.get("sourceCheck") or {}).get("expectation"),
        }
        for source in sources
    ]


def ordered_provider_candidates(doc: dict) -> list[str]:
    model = object_or_empty(doc.get("model"))
    providers = object_or_empty(model.get("providers"))
    fallbacks = providers.get("fallbacks", [])
    if not isinstance(fallbacks, list):
        fallbacks = []
    return [
        provider
        for provider in [providers.get("preferred"), *fallbacks]
        if isinstance(provider, str) and provider
    ]


def provider_for_target(doc: dict, target: str) -> str | None:
    candidates = ordered_provider_candidates(doc)
    if target in MODEL_PROVIDER_IDS:
        return target if target in candidates else None
    if target == "local-python":
        return "ollama" if "ollama" in candidates else None
    if target == "langgraph":
        return candidates[0] if candidates else None
    return candidates[0] if candidates else None


def provider_resolution(doc: dict, target: str, selected_provider: str | None) -> dict:
    candidates = ordered_provider_candidates(doc)
    if selected_provider is None and target in MODEL_PROVIDER_IDS:
        role = "not-declared"
    elif selected_provider is None:
        role = "not-applicable"
    elif candidates and selected_provider == candidates[0]:
        role = "preferred"
    elif selected_provider in candidates[1:]:
        role = "fallback"
    elif target in MODEL_PROVIDER_IDS:
        role = "not-declared"
    else:
        role = "target-derived"
    return {
        "requestedTarget": target,
        "orderedCandidates": candidates,
        "selectedProvider": selected_provider,
        "selectedRole": role,
        "hostedProvider": bool(selected_provider and HOSTED_MODEL_PROVIDERS.get(selected_provider, False)),
    }


def model_requirement_report(doc: dict, provider_id: str | None) -> dict:
    model = doc.get("model", {})
    requested = model.get("requirements", {})
    diagnostics = {
        "vocabularyVersion": "adl-v0.2-model-requirements",
        "provider": provider_id,
        "capability": model.get("capability"),
        "requested": requested,
        "supportedRequirements": [],
        "unsupportedRequirements": [],
        "degradedRequirements": [],
        "lossMetadata": [],
    }
    if provider_id not in PROVIDER_CAPABILITIES:
        diagnostics["unsupportedRequirements"].append(
            {
                "requirement": "model.providers",
                "requested": provider_id,
                "reason": "No model provider capability table is available for this target.",
            }
        )
        return diagnostics

    caps = PROVIDER_CAPABILITIES[provider_id]
    capability = model.get("capability")
    if capability in caps["capabilities"]:
        diagnostics["supportedRequirements"].append({"requirement": "capability", "requested": capability})
    else:
        diagnostics["unsupportedRequirements"].append(
            {
                "requirement": "capability",
                "requested": capability,
                "reason": f"{provider_id} does not advertise this ADL capability.",
            }
        )

    for key in ("toolCalling", "structuredOutput", "streaming", "jsonMode"):
        if key not in requested or requested[key] is False:
            continue
        support = caps[key]
        if support is True:
            diagnostics["supportedRequirements"].append({"requirement": key, "requested": True})
        elif support == "degraded":
            diagnostics["degradedRequirements"].append(
                {
                    "requirement": key,
                    "requested": True,
                    "reason": f"{provider_id} requires a reviewed custom harness for provider-native {key}.",
                }
            )
            diagnostics["lossMetadata"].append(
                {
                    "field": f"model.requirements.{key}",
                    "loss": "provider-native-enforcement-not-guaranteed",
                }
            )
        else:
            diagnostics["unsupportedRequirements"].append(
                {
                    "requirement": key,
                    "requested": True,
                    "reason": f"{provider_id} does not support this requirement in the static capability table.",
                }
            )

    for key in ("contextWindow", "maxOutputTokens"):
        if key not in requested:
            continue
        limit = caps[key]
        value = requested[key]
        if value <= limit:
            diagnostics["supportedRequirements"].append({"requirement": key, "requested": value, "limit": limit})
        else:
            diagnostics["unsupportedRequirements"].append(
                {
                    "requirement": key,
                    "requested": value,
                    "limit": limit,
                    "reason": f"{provider_id} static capability limit is lower than requested.",
                }
            )

    for modality in requested.get("modalities", []):
        if modality in caps["modalities"]:
            diagnostics["supportedRequirements"].append({"requirement": "modalities", "requested": modality})
        else:
            diagnostics["unsupportedRequirements"].append(
                {
                    "requirement": "modalities",
                    "requested": modality,
                    "reason": f"{provider_id} does not advertise this modality.",
                }
            )

    return diagnostics


def unsupported_requirement_features(requirement_report: dict) -> list[str]:
    return [
        f"{MODEL_REQUIREMENT_UNSUPPORTED_PREFIX}:{item['requirement']}"
        for item in requirement_report["unsupportedRequirements"]
    ]


def openai_mapping(doc: dict, mcp_tools: list[dict]) -> dict:
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    regular_tools = [tool for tool in tools if tool.get("type") != "mcp"]

    metadata_only = []
    if harness.get("policies"):
        metadata_only.append("harness.policies")
    if harness.get("evalGates"):
        metadata_only.append("harness.evalGates")
    if harness.get("memory"):
        metadata_only.append("harness.memory")
    if harness.get("dataSources"):
        metadata_only.append("harness.dataSources")
    if extensions.get("x402"):
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")
    if mcp_tools:
        metadata_only.append("harness.tools[type=mcp]")

    return {
        "mode": OPENAI_COMPATIBILITY_MODE,
        "provider": "openai",
        "modelProfile": {
            "capability": model.get("capability"),
            "preferredProvider": model.get("providers", {}).get("preferred"),
            "fallbackProviders": model.get("providers", {}).get("fallbacks", []),
            "requirements": model.get("requirements", {}),
        },
        "adapterMapping": {
            "instructions": "harness.instructions.inline",
            "tools": [tool.get("id") for tool in regular_tools],
            "structuredOutput": bool(model.get("requirements", {}).get("structuredOutput")),
            "sourceBoundary": source_boundary_metadata(doc),
            "metadataOnly": metadata_only,
            "unsupportedExecution": [tool.get("id") for tool in mcp_tools],
        },
        "reportOnly": True,
    }


def anthropic_mapping(doc: dict, mcp_tools: list[dict]) -> dict:
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    regular_tools = [tool for tool in tools if tool.get("type") != "mcp"]

    metadata_only = []
    if harness.get("policies"):
        metadata_only.append("harness.policies")
    if harness.get("evalGates"):
        metadata_only.append("harness.evalGates")
    if harness.get("memory"):
        metadata_only.append("harness.memory")
    if harness.get("dataSources"):
        metadata_only.append("harness.dataSources")
    if extensions.get("x402"):
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")

    return {
        "mode": ANTHROPIC_COMPATIBILITY_MODE,
        "provider": "anthropic",
        "modelProfile": {
            "capability": model.get("capability"),
            "preferredProvider": model.get("providers", {}).get("preferred"),
            "fallbackProviders": model.get("providers", {}).get("fallbacks", []),
            "requirements": model.get("requirements", {}),
        },
        "adapterMapping": {
            "systemPrompt": "harness.instructions.inline",
            "toolUseSchemas": [tool.get("id") for tool in regular_tools],
            "mcpDeclarations": [
                {
                    "id": tool.get("id"),
                    "serverRef": tool.get("serverRef"),
                    "toolName": tool.get("toolName"),
                }
                for tool in mcp_tools
            ],
            "sourceBoundary": source_boundary_metadata(doc),
            "sourceBoundaryMode": "metadata-only",
            "metadataOnly": metadata_only,
            "unsupportedExecution": [tool.get("id") for tool in mcp_tools],
        },
        "reportOnly": True,
    }


def gemini_mapping(doc: dict, mcp_tools: list[dict]) -> dict:
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    regular_tools = [tool for tool in tools if tool.get("type") != "mcp"]

    metadata_only = []
    if harness.get("policies"):
        metadata_only.append("harness.policies")
    if harness.get("evalGates"):
        metadata_only.append("harness.evalGates")
    if harness.get("memory"):
        metadata_only.append("harness.memory")
    if harness.get("dataSources"):
        metadata_only.append("harness.dataSources")
    if extensions.get("x402"):
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")
    if mcp_tools:
        metadata_only.append("harness.tools[type=mcp]")

    return {
        "mode": GEMINI_COMPATIBILITY_MODE,
        "provider": "gemini",
        "modelProfile": {
            "capability": model.get("capability"),
            "preferredProvider": model.get("providers", {}).get("preferred"),
            "fallbackProviders": model.get("providers", {}).get("fallbacks", []),
            "requirements": model.get("requirements", {}),
        },
        "adapterMapping": {
            "systemInstruction": "harness.instructions.inline",
            "functionDeclarations": [tool.get("id") for tool in regular_tools],
            "structuredOutput": bool(model.get("requirements", {}).get("structuredOutput")),
            "grounding": "not-configured",
            "codeExecution": "unsupported",
            "sourceBoundary": source_boundary_metadata(doc),
            "metadataOnly": metadata_only,
            "unsupportedExecution": [tool.get("id") for tool in mcp_tools],
        },
        "reportOnly": True,
    }


def ollama_mapping(doc: dict, mcp_tools: list[dict]) -> dict:
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    regular_tools = [tool for tool in tools if tool.get("type") != "mcp"]
    providers = model.get("providers", {})
    declared_providers = [providers.get("preferred"), *providers.get("fallbacks", [])]

    metadata_only = []
    if harness.get("policies"):
        metadata_only.append("harness.policies")
    if harness.get("evalGates"):
        metadata_only.append("harness.evalGates")
    if harness.get("memory"):
        metadata_only.append("harness.memory")
    if harness.get("dataSources"):
        metadata_only.append("harness.dataSources")
    if extensions.get("x402"):
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")
    if mcp_tools:
        metadata_only.append("harness.tools[type=mcp]")

    return {
        "mode": OLLAMA_COMPATIBILITY_MODE,
        "provider": "ollama",
        "modelProfile": {
            "capability": model.get("capability"),
            "preferredProvider": providers.get("preferred"),
            "fallbackProviders": providers.get("fallbacks", []),
            "localProviderDeclared": "ollama" in declared_providers,
            "requirements": model.get("requirements", {}),
        },
        "adapterMapping": {
            "localEndpoint": "not-probed",
            "modelId": "metadata-only",
            "promptTemplate": "harness.instructions.inline",
            "toolCalls": "custom-harness-required"
            if model.get("requirements", {}).get("toolCalling")
            else "not-required",
            "structuredOutput": "custom-harness-required"
            if model.get("requirements", {}).get("structuredOutput")
            else "not-required",
            "stateAndMemory": "external-harness-owned",
            "functionTools": [tool.get("id") for tool in regular_tools],
            "sourceBoundary": source_boundary_metadata(doc),
            "metadataOnly": metadata_only,
            "unsupportedExecution": [tool.get("id") for tool in mcp_tools],
        },
        "reportOnly": True,
    }


def langgraph_mapping(doc: dict, mcp_tools: list[dict]) -> dict:
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    regular_tools = [tool for tool in tools if tool.get("type") != "mcp"]

    metadata_only = []
    if harness.get("policies"):
        metadata_only.append("harness.policies")
    if harness.get("evalGates"):
        metadata_only.append("harness.evalGates")
    if harness.get("memory"):
        metadata_only.append("harness.memory")
    if harness.get("dataSources"):
        metadata_only.append("harness.dataSources")
    if extensions.get("x402"):
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")
    if mcp_tools:
        metadata_only.append("harness.tools[type=mcp]")

    graph_nodes = ["model"]
    if regular_tools:
        graph_nodes.append("tools")
    if harness.get("evalGates"):
        graph_nodes.append("eval-gates")
    if extensions.get("receipts"):
        graph_nodes.append("receipt-metadata")

    return {
        "mode": LANGGRAPH_COMPATIBILITY_MODE,
        "provider": "langgraph",
        "modelProfile": {
            "capability": model.get("capability"),
            "preferredProvider": model.get("providers", {}).get("preferred"),
            "fallbackProviders": model.get("providers", {}).get("fallbacks", []),
            "requirements": model.get("requirements", {}),
        },
        "adapterMapping": {
            "graph": "not-generated",
            "stateSchema": {
                "messages": "harness-owned",
                "memory": "metadata-only" if harness.get("memory") else "not-declared",
                "policyResults": "metadata-only" if harness.get("policies") else "not-declared",
                "evalResults": "metadata-only" if harness.get("evalGates") else "not-declared",
                "receipt": "metadata-only" if extensions.get("receipts") else "not-declared",
            },
            "nodes": graph_nodes,
            "toolNodes": [tool.get("id") for tool in regular_tools],
            "mcpToolNodes": [tool.get("id") for tool in mcp_tools],
            "edges": "static-plan-only",
            "checkpointing": "metadata-only" if harness.get("memory") else "not-declared",
            "interrupts": "metadata-only" if harness.get("policies") else "not-declared",
            "sourceBoundary": source_boundary_metadata(doc),
            "metadataOnly": metadata_only,
            "unsupportedExecution": [tool.get("id") for tool in mcp_tools],
        },
        "reportOnly": True,
    }


def report(path: Path, target: str) -> dict:
    doc = load_adl(path)
    schema_errors = adl_v02_validation_errors(doc)
    if schema_errors:
        return unsupported_schema_report(path, doc, target, schema_errors)

    harness = doc["harness"]
    model = doc["model"]
    extensions = doc.get("extensions") or {}
    tools = harness.get("tools", [])
    mcp_tools = [tool for tool in tools if tool.get("type") == "mcp"]
    source_boundaries = source_boundary_metadata(doc)
    warnings = []
    unsupported = []
    required_secrets = []
    required_hosted_services = []
    compatibility_mode = "provider-compatibility-report-only"
    provider_mapping = None
    selected_provider = provider_for_target(doc, target)
    resolution = provider_resolution(doc, target, selected_provider)
    requirement_diagnostics = model_requirement_report(doc, selected_provider)

    if target == "local-python":
        level = 1 if harness["runtime"]["target"] == "local-python" else 0
    elif target == "mcp-readonly":
        level = 2 if mcp_tools else 0
    elif target == "ollama":
        level = 2
        compatibility_mode = OLLAMA_COMPATIBILITY_MODE
        provider_mapping = ollama_mapping(doc, mcp_tools)
        warnings.append(
            "Ollama/local compatibility is report-only; local endpoint, model id, "
            "tool calling, structured output, memory, policy, eval, payment, receipt, "
            "reputation, and MCP semantics remain metadata-only or external-harness-owned "
            "unless a reviewed local adapter enforces them."
        )
    elif target in ["openai", "anthropic", "gemini", "langgraph"]:
        level = 2
        if selected_provider in PROVIDER_SECRETS:
            required_secrets.append(PROVIDER_SECRETS[selected_provider])
        if target == "openai":
            compatibility_mode = OPENAI_COMPATIBILITY_MODE
            provider_mapping = openai_mapping(doc, mcp_tools)
            if provider_mapping["adapterMapping"]["metadataOnly"]:
                warnings.append(
                    "OpenAI compatibility is report-only; Reddi policy, eval, memory, "
                    "payment, receipt, reputation, and MCP semantics remain metadata-only "
                    "unless a reviewed runtime adapter enforces them."
                )
        if target == "anthropic":
            compatibility_mode = ANTHROPIC_COMPATIBILITY_MODE
            provider_mapping = anthropic_mapping(doc, mcp_tools)
            warnings.append(
                "Anthropic MCP compatibility is report-only; Reddi policy, eval, memory, "
                "data-source, payment, receipt, reputation, and MCP semantics remain "
                "metadata-only unless a reviewed runtime adapter enforces them."
            )
        if target == "gemini":
            compatibility_mode = GEMINI_COMPATIBILITY_MODE
            provider_mapping = gemini_mapping(doc, mcp_tools)
            warnings.append(
                "Gemini compatibility is report-only; Reddi policy, eval, memory, "
                "data-source, payment, receipt, reputation, grounding, code execution, "
                "and MCP semantics remain metadata-only or unsupported unless a reviewed "
                "runtime adapter enforces them."
            )
        if target == "langgraph":
            compatibility_mode = LANGGRAPH_COMPATIBILITY_MODE
            provider_mapping = langgraph_mapping(doc, mcp_tools)
            warnings.append(
                "LangGraph compatibility is report-only; graph, state, node, edge, "
                "checkpoint, interrupt, policy, eval, memory, payment, receipt, "
                "reputation, and MCP semantics remain metadata-only or static-plan-only "
                "unless a reviewed runtime graph enforces them."
            )
    else:
        level = 0

    if resolution["selectedRole"] == "not-declared":
        unsupported.append(PROVIDER_NOT_DECLARED_UNSUPPORTED)
        warnings.append(
            f"Requested provider target {target!r} is not declared in model.providers; "
            "provider compatibility remains unsupported until it is preferred or listed as a fallback."
        )

    if (extensions.get("x402") or {}).get("enabled"):
        warnings.append("Payment extension is dry-run only until receipt and policy enforcement land.")
        if target != "local-python":
            unsupported.append("real_settlement")

    if requirement_diagnostics["unsupportedRequirements"]:
        unsupported.extend(unsupported_requirement_features(requirement_diagnostics))
    if requirement_diagnostics["degradedRequirements"]:
        warnings.append(
            "Some model capability requirements are degraded; review lossMetadata before runtime use."
        )

    if mcp_tools:
        warnings.append("MCP declarations are read-only adapter shapes until server resolution lands.")
        unsupported.append("mcp_execution")
        required_hosted_services.extend(
            f"mcp:{tool.get('serverRef', '<missing-serverRef>')}" for tool in mcp_tools
        )

    result = {
        "agent": doc["metadata"]["name"],
        "target": target,
        "supported": not unsupported,
        "level": level,
        "warnings": warnings,
        "unsupportedFeatures": sorted(set(unsupported), key=unsupported.index),
        "providerResolution": resolution,
        "modelCapabilityRequirements": requirement_diagnostics,
        "requiredSecrets": required_secrets,
        "requiredHostedServices": required_hosted_services,
        "suggestedFallback": "local-python",
        "boundary": REPORT_ONLY_BOUNDARY,
        "compatibilityMode": compatibility_mode,
        "dataSourceTypes": [source["type"] for source in source_boundaries],
        "sourceBoundary": source_boundaries,
    }
    if doc.get("apiVersion") == "reddiagent.dev/v0.2":
        result["conformance"] = conformance_metadata(path)
    if provider_mapping is not None:
        result["providerMapping"] = provider_mapping
    return result


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

    try:
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
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
