"""Stable validation diagnostics for ADL schema errors."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Iterable

from jsonschema.exceptions import ValidationError
import yaml
from yaml.nodes import MappingNode, Node, SequenceNode


@dataclass(frozen=True)
class SourceLocation:
    line: int | None
    column: int | None


def path_to_string(path: Iterable[Any]) -> str:
    parts = [str(part) for part in path]
    return ".".join(parts) if parts else "<root>"


def error_path(error: ValidationError) -> str:
    missing = missing_required_location(error)
    if missing:
        return missing
    return path_to_string(error.path)


def missing_required_location(error: ValidationError) -> str | None:
    if error.validator != "required":
        return None
    match = re.match(r"'([^']+)' is a required property", error.message)
    if not match:
        return None
    parent = path_to_string(error.path)
    child = match.group(1)
    return child if parent == "<root>" else f"{parent}.{child}"


def diagnostic_code(error: ValidationError) -> str:
    location = error_path(error).replace(".", "_").replace("<root>", "root")
    location = re.sub(r"[^A-Za-z0-9_]+", "_", location).strip("_") or "root"
    return f"adl_v0_2_schema.{error.validator}.{location}"


def diagnostic_category(location: str) -> str:
    if location in {"apiVersion", "kind", "metadata", "model", "harness", "<root>"}:
        return "shape"
    if location.startswith("model."):
        return "provider"
    if location.startswith("harness.policies"):
        return "policy"
    if location.startswith("harness.evalGates"):
        return "gate"
    if location.startswith("harness.runtime") or location.startswith("harness.deployment"):
        return "runtime"
    if location.startswith("harness.observability"):
        return "observability"
    if location.startswith("harness.memory"):
        return "memory"
    if location.startswith("extensions.x402") or location.startswith("extensions.receipts"):
        return "payment"
    if location.startswith("extensions.reputation"):
        return "reputation"
    if location.startswith("extensions"):
        return "extension"
    return "schema"


def _node_location(node: Node | None) -> SourceLocation:
    if node is None:
        return SourceLocation(line=None, column=None)
    return SourceLocation(line=node.start_mark.line + 1, column=node.start_mark.column + 1)


def _child_for_mapping(node: MappingNode, key: str) -> Node | None:
    for key_node, value_node in node.value:
        if key_node.value == key:
            return value_node
    return None


def _node_at_path(node: Node | None, path: Iterable[Any]) -> Node | None:
    current = node
    for part in path:
        if isinstance(current, MappingNode):
            current = _child_for_mapping(current, str(part))
        elif isinstance(current, SequenceNode) and isinstance(part, int):
            if part < 0 or part >= len(current.value):
                return None
            current = current.value[part]
        else:
            return None
    return current


def source_location(path: Path, error: ValidationError) -> SourceLocation:
    try:
        root_node = yaml.compose(path.read_text())
    except yaml.YAMLError:
        return SourceLocation(line=None, column=None)
    lookup_path = list(error.path)
    node = _node_at_path(root_node, lookup_path)
    return _node_location(node)


def format_validation_error(error: ValidationError, source_path: Path | None = None) -> dict:
    location = error_path(error)
    source = source_location(source_path, error) if source_path else SourceLocation(line=None, column=None)
    return {
        "code": diagnostic_code(error),
        "severity": "error",
        "category": diagnostic_category(location),
        "path": location,
        "line": source.line,
        "column": source.column,
        "message": error.message,
    }


def format_validation_errors(errors: Iterable[ValidationError], source_path: Path | None = None) -> list[dict]:
    return [format_validation_error(error, source_path) for error in errors]
