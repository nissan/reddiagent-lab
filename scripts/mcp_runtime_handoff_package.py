#!/usr/bin/env python3
"""Static checks for MCP runtime handoff package artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path("specs/MCP-RUNTIME-HANDOFF-PACKAGE.schema.json")
REQUIRED_STATIC_FALSE_FLAGS = [
    "runtimeExecutionAllowed",
    "networkAccess",
    "paymentAccess",
    "mcpInvocation",
]
REQUIRED_EVIDENCE_GATES = {
    "mcp-adapter-shape",
    "mcp-adapter-contract",
    "mcp-adapter-error-semantics",
    "mcp-adapter-aggregation",
    "mcp-adapter-source-check",
    "mcp-server-resolution",
    "mcp-capability-policy",
    "mcp-readiness-evidence",
}
REQUIRED_READINESS_EVENTS = {
    "mcp.adapter_shape_checked",
    "mcp.adapter_source_checked",
    "mcp.adapter_aggregation_checked",
    "mcp.server_resolution_checked",
    "mcp.capability_policy_checked",
    "mcp.readiness_completed",
}
FORBIDDEN_KEYS = {
    "serverUrl",
    "urlTemplate",
    "command",
    "args",
    "env",
    "headers",
    "credentials",
    "credential",
    "secret",
    "token",
    "apiKey",
    "privateKey",
    "wallet",
    "facilitatorUrl",
    "settlementUrl",
    "rawPrompt",
    "prompt",
    "taskBody",
}


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_finding(findings: list[dict], field: str, reason: str) -> None:
    findings.append({"status": "fail", "field": field, "reason": reason})


def access_is_static(payload: dict) -> bool:
    return all(payload.get(flag) is False for flag in REQUIRED_STATIC_FALSE_FLAGS)


def scan_forbidden_keys(value: object, path: str, findings: list[dict]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in FORBIDDEN_KEYS:
                add_finding(
                    findings,
                    child_path,
                    "MCP runtime handoff packages must not include live runtime, credential, payment, or raw prompt fields.",
                )
            scan_forbidden_keys(child, child_path, findings)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden_keys(child, f"{path}[{index}]", findings)


def check_evidence(package: dict, findings: list[dict]) -> None:
    evidence = package.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        add_finding(findings, "evidence", "MCP runtime handoff package must include reviewed evidence gates.")
        return

    observed_gates: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            add_finding(findings, f"evidence[{index}]", "Every evidence entry must be an object.")
            continue

        gate_id = item.get("gateId")
        if non_empty_string(gate_id):
            observed_gates.add(gate_id)
        else:
            add_finding(findings, f"evidence[{index}].gateId", "Evidence entries must declare a non-empty gateId.")

        if item.get("status") != "pass":
            add_finding(findings, f"evidence[{index}].status", "Every evidence gate in the handoff package must pass.")

        if not non_empty_string(item.get("artifact")):
            add_finding(findings, f"evidence[{index}].artifact", "Evidence entries must point at a local artifact path.")

        if not access_is_static(item):
            add_finding(findings, f"evidence[{index}].access", "Evidence entries must preserve all static access flags as false.")

    missing = sorted(REQUIRED_EVIDENCE_GATES - observed_gates)
    for gate_id in missing:
        add_finding(findings, "evidence", f"Missing required MCP runtime handoff evidence gate: {gate_id}.")


def check_server_manifest(package: dict, findings: list[dict]) -> None:
    manifest = package.get("serverManifest")
    if not isinstance(manifest, dict):
        add_finding(findings, "serverManifest", "MCP runtime handoff package must include a static server manifest.")
        return

    if manifest.get("resolutionMode") != "static-reviewed":
        add_finding(findings, "serverManifest.resolutionMode", "Server manifest resolutionMode must be static-reviewed.")

    if not non_empty_string(manifest.get("serverRef")):
        add_finding(findings, "serverManifest.serverRef", "Server manifest must include a non-empty serverRef.")

    tools = manifest.get("tools")
    if not isinstance(tools, list) or not tools:
        add_finding(findings, "serverManifest.tools", "Server manifest must include at least one static tool contract.")
    else:
        for index, tool in enumerate(tools):
            if not isinstance(tool, dict):
                add_finding(findings, f"serverManifest.tools[{index}]", "Each tool contract must be an object.")
                continue
            if not non_empty_string(tool.get("toolId")):
                add_finding(findings, f"serverManifest.tools[{index}].toolId", "Tool contracts must include a toolId.")
            if not non_empty_string(tool.get("capabilityPolicyRef")):
                add_finding(
                    findings,
                    f"serverManifest.tools[{index}].capabilityPolicyRef",
                    "Tool contracts must reference a capability policy.",
                )
            if not non_empty_string(tool.get("sourceGate")):
                add_finding(findings, f"serverManifest.tools[{index}].sourceGate", "Tool contracts must reference a source gate.")
            if not access_is_static(tool):
                add_finding(findings, f"serverManifest.tools[{index}].access", "Tool contracts must preserve all static access flags as false.")

    if not access_is_static(manifest):
        add_finding(findings, "serverManifest.access", "Server manifest must preserve all static access flags as false.")


def check_handoff_constraints(package: dict, findings: list[dict]) -> None:
    constraints = package.get("handoffConstraints")
    if not isinstance(constraints, dict):
        add_finding(findings, "handoffConstraints", "MCP runtime handoff package must include explicit handoff constraints.")
        return

    expected_booleans = {
        "requiresHumanApprovalBeforeRuntime": True,
        "allowsServerResolution": False,
        "allowsMcpInvocation": False,
        "allowsNetworkAccess": False,
        "allowsPaymentAccess": False,
        "allowsCredentialAccess": False,
    }
    for field, expected in expected_booleans.items():
        if constraints.get(field) is not expected:
            add_finding(findings, f"handoffConstraints.{field}", "MCP runtime handoff constraints must fail closed.")

    required_notes = constraints.get("requiredNotes")
    if not isinstance(required_notes, list) or not required_notes:
        add_finding(findings, "handoffConstraints.requiredNotes", "Handoff constraints must include builder-facing required notes.")


def check_readiness_trace(package: dict, findings: list[dict]) -> None:
    trace = package.get("readinessTrace")
    if not isinstance(trace, dict):
        add_finding(findings, "readinessTrace", "MCP runtime handoff package must include readiness trace evidence.")
        return

    events = trace.get("events")
    if not isinstance(events, list):
        add_finding(findings, "readinessTrace.events", "Readiness trace must include events.")
        return

    observed_events = {event.get("event") for event in events if isinstance(event, dict)}
    missing = sorted(REQUIRED_READINESS_EVENTS - observed_events)
    for event in missing:
        add_finding(findings, "readinessTrace.events", f"Missing required MCP readiness trace event: {event}.")

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            add_finding(findings, f"readinessTrace.events[{index}]", "Readiness trace events must be objects.")
            continue
        if event.get("status") != "pass":
            add_finding(findings, f"readinessTrace.events[{index}].status", "Readiness trace events must pass before handoff.")
        if not all(event.get(flag) is False for flag in ["networkAccess", "paymentAccess", "mcpInvocation"]):
            add_finding(findings, f"readinessTrace.events[{index}].access", "Readiness trace events must preserve static access flags.")


def check_package(package: dict) -> list[dict]:
    findings: list[dict] = []

    if package.get("schema") != str(SCHEMA_PATH):
        add_finding(findings, "schema", "MCP runtime handoff package must reference the canonical schema path.")

    if package.get("packageType") != "mcp-runtime-handoff":
        add_finding(findings, "packageType", "MCP runtime handoff package must declare packageType=mcp-runtime-handoff.")

    if not non_empty_string(package.get("packageId")):
        add_finding(findings, "packageId", "MCP runtime handoff package must have a non-empty packageId.")

    if package.get("mode") != "static-report-only":
        add_finding(findings, "mode", "MCP runtime handoff package must use mode=static-report-only.")

    if not access_is_static(package):
        add_finding(findings, "access", "MCP runtime handoff package must set runtime/network/payment/MCP access flags to false.")

    scan_forbidden_keys(package, "", findings)
    check_evidence(package, findings)
    check_server_manifest(package, findings)
    check_readiness_trace(package, findings)
    check_handoff_constraints(package, findings)
    return findings


def report(path: Path) -> dict:
    package = read_json(path)
    findings = check_package(package)
    return {
        "path": display_path(path),
        "schema": str(SCHEMA_PATH),
        "mode": "static-mcp-runtime-handoff-package-check",
        "packageId": package.get("packageId"),
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
        "handoffReady": not findings,
        "status": "fail" if findings else "pass",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    result = report(args.package)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
