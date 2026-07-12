#!/usr/bin/env python3
"""Deterministic local tool fixtures for ReddiAgent dry-run conformance."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from tool_denial_guidance import guidance_for_denial


APPROVED_DOCS = [
    {
        "title": "ReddiAgent ADL v0.1",
        "url": "specs/ADL-v0.1.md",
        "snippet": "ADL describes the model, harness, policies, eval gates, and extensions for a ReddiAgent.",
    },
    {
        "title": "Tool Registry Contract v0.1",
        "url": "specs/TOOL-REGISTRY-v0.1.md",
        "snippet": "Tools are typed, permissioned, observable, and replaceable harness capabilities.",
    },
    {
        "title": "Harness Lifecycle v0.1",
        "url": "specs/HARNESS-LIFECYCLE-v0.1.md",
        "snippet": "The harness lifecycle covers validation, dry-run execution, trace capture, and conformance review.",
    },
]
APPROVED_SOURCE_URLS = {doc["url"] for doc in APPROVED_DOCS}
APPROVED_SOURCE_TITLES = {doc["title"] for doc in APPROVED_DOCS}


class ToolExecutionError(ValueError):
    """Raised when a local fixture call is invalid or denied."""


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def search_docs(args: dict[str, Any]) -> dict[str, str]:
    query = str(args.get("query", "")).strip().lower()
    if not query:
        raise ToolExecutionError("search_docs requires a non-empty query")
    for doc in APPROVED_DOCS:
        haystack = " ".join([doc["title"], doc["snippet"]]).lower()
        if any(token in haystack for token in query.split()):
            return doc
    return APPROVED_DOCS[0]


def unsafe_source_docs(args: dict[str, Any]) -> dict[str, str]:
    query = str(args.get("query", "")).strip()
    if not query:
        raise ToolExecutionError("unsafe_source_docs requires a non-empty query")
    return {
        "title": "Unapproved External Source",
        "url": "https://example.invalid/reddiagent",
        "snippet": "This deterministic fixture proves successful tool output still fails source checks.",
    }


TOOLS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "search_docs": search_docs,
    "unsafe_source_docs": unsafe_source_docs,
}


def denied_result(tool_id: str, args: Any, reason: str) -> dict[str, Any]:
    safe_args = args if isinstance(args, dict) else {"_invalidArgs": str(type(args).__name__)}
    guidance = guidance_for_denial(tool_id, reason)
    return {
        "toolId": tool_id,
        "status": "denied",
        "inputHash": stable_hash(safe_args),
        "outputHash": stable_hash({"denied": reason}),
        "error": reason,
        "guidance": guidance.to_dict(),
    }


def execute_tool(tool_id: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool_id not in TOOLS:
        raise ToolExecutionError(f"unsupported local fixture tool: {tool_id}")
    if not isinstance(args, dict):
        raise ToolExecutionError("tool args must be an object")
    output = TOOLS[tool_id](args)
    return {
        "toolId": tool_id,
        "status": "success",
        "inputHash": stable_hash(args),
        "outputHash": stable_hash(output),
        "output": output,
    }
