#!/usr/bin/env python3
"""Dry-run a ReddiAgent ADL file on the local-python target."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import jsonschema
import yaml

from local_tool_registry import ToolExecutionError, denied_result, execute_tool
from source_check import check_tool_sources, summarize_source_checks
from tool_denial_guidance import guidance_for_denial, render_tool_denial
from validation_guidance import format_errors, render_text


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validate(doc: dict) -> list[jsonschema.ValidationError]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    return sorted(validator.iter_errors(doc), key=lambda e: list(e.path))


def stable_id(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_trace(
    doc: dict,
    path: Path,
    tool_results: list[dict] | None = None,
    source_checks: list[dict] | None = None,
    completion_status: str = "pass",
    completion_reason: str = "dry-run transport completed",
) -> list[dict]:
    metadata = doc["metadata"]
    harness = doc["harness"]
    model = doc["model"]
    agent = metadata["name"]
    trace_id = stable_id(agent, path.name, "dry-run")
    events = [
        {
            "event": "session.started",
            "traceId": trace_id,
            "agent": agent,
            "runtime": harness["runtime"]["target"],
        },
        {
            "event": "model.resolved",
            "traceId": trace_id,
            "provider": model["providers"]["preferred"],
            "capability": model["capability"],
        },
        {
            "event": "tools.registered",
            "traceId": trace_id,
            "count": len(harness.get("tools", [])),
        },
        {
            "event": "policies.loaded",
            "traceId": trace_id,
            "count": len(harness.get("policies", [])),
        },
        {
            "event": "evals.loaded",
            "traceId": trace_id,
            "count": len(harness.get("evalGates", [])),
        },
    ]
    for result in tool_results or []:
        event_name = "tool.denied" if result["status"] == "denied" else "tool.executed"
        events.append(
            {
                "event": event_name,
                "traceId": trace_id,
                "toolId": result["toolId"],
                "status": result["status"],
                "inputHash": result["inputHash"],
                "outputHash": result["outputHash"],
            }
        )
    for check in source_checks or []:
        events.append(
            {
                "event": "source.checked",
                "traceId": trace_id,
                "gateId": check["gateId"],
                "toolId": check["toolId"],
                "status": check["status"],
            }
        )
    events.append(
        {
            "event": "task.dry_run_completed",
            "traceId": trace_id,
            "status": completion_status,
            "reason": completion_reason,
        }
    )
    return events


def run_tool_fixtures(doc: dict, allow_denied: bool = False) -> list[dict]:
    harness = doc["harness"]
    declared_tools = {tool["id"] for tool in harness.get("tools", [])}
    results: list[dict] = []
    for call in harness.get("toolFixtures", []):
        tool_id = str(call.get("toolId", ""))
        args = call.get("args", {})
        if tool_id not in declared_tools:
            reason = f"tool fixture references undeclared tool: {tool_id}"
            if allow_denied:
                results.append(denied_result(tool_id, args, reason))
                continue
            raise ToolExecutionError(reason)
        try:
            results.append(execute_tool(tool_id, args))
        except ToolExecutionError as exc:
            if allow_denied:
                results.append(denied_result(tool_id, args, str(exc)))
                continue
            raise
    return results


def dry_run(
    path: Path,
    execute_tools_flag: bool = False,
    allow_denied_tools: bool = False,
    fail_on_required_gate: bool = False,
) -> int:
    doc = load_yaml(path)
    errors = validate(doc)
    if errors:
        print(render_text(display_path(path), format_errors(errors)))
        return 1

    metadata = doc["metadata"]
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}

    try:
        tool_results = run_tool_fixtures(doc, allow_denied=allow_denied_tools) if execute_tools_flag else []
    except ToolExecutionError as exc:
        tool_id = str(getattr(exc, "tool_id", "")) or "unknown"
        reason = str(exc)
        if "tool:" in reason:
            tool_id = reason.rsplit(":", 1)[-1].strip()
        print(render_tool_denial(display_path(path), guidance_for_denial(tool_id, reason)), file=sys.stderr)
        return 2

    source_checks = check_tool_sources(tool_results) if execute_tools_flag else []
    source_check_summary = summarize_source_checks(source_checks) if execute_tools_flag else None
    denied_count = sum(1 for result in tool_results if result["status"] == "denied")
    required_gate_status = "fail" if denied_count or (source_check_summary or {}).get("status") == "fail" else "pass"
    completion_reason = (
        "dry-run transport completed, but required gates failed"
        if required_gate_status == "fail"
        else "dry-run transport completed and required gates passed"
    )
    completion = {
        "transportStatus": "pass",
        "requiredGateStatus": required_gate_status,
        "status": required_gate_status,
        "reason": completion_reason,
    }
    trace = build_trace(
        doc,
        path,
        tool_results,
        source_checks,
        completion_status=completion["status"],
        completion_reason=completion_reason,
    )
    summary = {
        "agent": metadata["name"],
        "description": metadata["description"],
        "runtime": harness["runtime"]["target"],
        "modelCapability": model["capability"],
        "preferredProvider": model["providers"]["preferred"],
        "fallbackProviders": model["providers"].get("fallbacks", []),
        "toolCount": len(harness.get("tools", [])),
        "policyCount": len(harness.get("policies", [])),
        "evalGateCount": len(harness.get("evalGates", [])),
        "paymentEnabled": bool((extensions.get("x402") or {}).get("enabled")),
        "mode": "dry-run",
        "level": 1,
        "completion": completion,
        "trace": trace,
    }
    if execute_tools_flag:
        summary["toolExecution"] = {
            "mode": "local-fixture",
            "networkAccess": False,
            "paymentAccess": False,
            "deniedCount": denied_count,
            "results": tool_results,
        }
        summary["sourceChecks"] = source_checks
        summary["sourceCheckSummary"] = source_check_summary

    print(json.dumps(summary, indent=2))
    if fail_on_required_gate and completion["status"] == "fail":
        return 3
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", type=Path)
    parser.add_argument(
        "--execute-tools",
        action="store_true",
        help="Execute deterministic local tool fixtures declared in harness.toolFixtures.",
    )
    parser.add_argument(
        "--allow-denied-tools",
        action="store_true",
        help="Report denied local tool fixture calls instead of failing the dry run.",
    )
    parser.add_argument(
        "--fail-on-required-gate",
        action="store_true",
        help="Return exit code 3 when the dry run completed but required gates failed.",
    )
    args = parser.parse_args()
    return dry_run(
        args.adl,
        execute_tools_flag=args.execute_tools,
        allow_denied_tools=args.allow_denied_tools,
        fail_on_required_gate=args.fail_on_required_gate,
    )


if __name__ == "__main__":
    sys.exit(main())
