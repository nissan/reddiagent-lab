#!/usr/bin/env python3
"""Static local runner plugin declaration checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_KEYS = {
    "url",
    "endpoint",
    "serverUrl",
    "command",
    "args",
    "env",
    "headers",
    "token",
    "apiKey",
    "secret",
    "credential",
    "wallet",
    "privateKey",
    "facilitator",
    "paymentRail",
}
REQUIRED_FALSE_CAPABILITIES = [
    "networkAccess",
    "shellAccess",
    "credentialAccess",
    "paymentAccess",
    "mcpInvocation",
    "filesystemMutation",
]
REQUIRED_FALSE_BOUNDARIES = ["runtimeExecutionAllowed", "externalExecutionAllowed"]
ALLOWED_MODES = {"deterministic-local-fixture"}
ALLOWED_ENTRYPOINT_KINDS = {"python-function", "static-fixture"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def add_issue(issues: list[dict[str, str]], path: str, message: str) -> None:
    issues.append({"path": path, "message": message})


def scan_for_live_fields(value: Any, path: str, issues: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in FORBIDDEN_KEYS:
                add_issue(issues, child_path, "Plugin declaration embeds a live execution field.")
            scan_for_live_fields(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_for_live_fields(child, f"{path}.{index}", issues)
    elif isinstance(value, str) and ("http://" in value or "https://" in value):
        add_issue(issues, path, "Plugin declaration embeds a live URL.")


def validate_declaration(doc: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if doc.get("schemaVersion") != "local-runner-plugin.v0.1":
        add_issue(issues, "schemaVersion", "Expected local-runner-plugin.v0.1.")

    plugin = doc.get("plugin")
    if not isinstance(plugin, dict):
        add_issue(issues, "plugin", "Plugin declaration must include a plugin object.")
        plugin = {}
    for field in ["id", "name", "mode", "entrypoint", "tools"]:
        if field not in plugin:
            add_issue(issues, f"plugin.{field}", "Required plugin field is missing.")
    if plugin.get("mode") not in ALLOWED_MODES:
        add_issue(issues, "plugin.mode", "Only deterministic-local-fixture mode is allowed.")

    entrypoint = plugin.get("entrypoint")
    if not isinstance(entrypoint, dict):
        add_issue(issues, "plugin.entrypoint", "Entrypoint metadata must be an object.")
    elif entrypoint.get("kind") not in ALLOWED_ENTRYPOINT_KINDS:
        add_issue(issues, "plugin.entrypoint.kind", "Entrypoint kind is not allowed.")

    tools = plugin.get("tools")
    if not isinstance(tools, list) or not tools:
        add_issue(issues, "plugin.tools", "Plugin must declare at least one local fixture tool.")
    elif any(not isinstance(tool, dict) or not tool.get("id") for tool in tools):
        add_issue(issues, "plugin.tools", "Every declared tool must be an object with an id.")

    capabilities = doc.get("capabilities")
    if not isinstance(capabilities, dict):
        add_issue(issues, "capabilities", "Capabilities must be explicit.")
        capabilities = {}
    for key in REQUIRED_FALSE_CAPABILITIES:
        if capabilities.get(key) is not False:
            add_issue(issues, f"capabilities.{key}", "Capability must be false.")

    boundaries = doc.get("boundaries")
    if not isinstance(boundaries, dict):
        add_issue(issues, "boundaries", "Execution boundaries must be explicit.")
        boundaries = {}
    for key in REQUIRED_FALSE_BOUNDARIES:
        if boundaries.get(key) is not False:
            add_issue(issues, f"boundaries.{key}", "Execution boundary must be false.")

    contract = doc.get("fixtureContract")
    if not isinstance(contract, dict):
        add_issue(issues, "fixtureContract", "Fixture contract must be explicit.")
        contract = {}
    if contract.get("deterministic") is not True:
        add_issue(issues, "fixtureContract.deterministic", "Fixture contract must be deterministic.")
    if contract.get("approvedSourcesOnly") is not True:
        add_issue(issues, "fixtureContract.approvedSourcesOnly", "Fixture outputs must use approved sources only.")
    if contract.get("sideEffects") != "none":
        add_issue(issues, "fixtureContract.sideEffects", "Fixture side effects must be none.")

    scan_for_live_fields(doc, "", issues)
    return issues


def report(path: Path) -> dict[str, Any]:
    doc = read_json(path)
    issues = validate_declaration(doc)
    return {
        "declaration": display_path(path),
        "mode": "static-local-runner-plugin-interface",
        "status": "fail" if issues else "pass",
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
        "externalExecutionAllowed": False,
        "pluginLoaded": False,
        "pluginInvoked": False,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("declaration", type=Path)
    args = parser.parse_args()
    result = report(args.declaration)
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
