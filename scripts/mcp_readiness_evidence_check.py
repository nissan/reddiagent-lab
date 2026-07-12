#!/usr/bin/env python3
"""Static trace/evidence checks for MCP readiness gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_GATE_EVENTS = [
    ("mcp.adapter_shape_checked", "mcp-adapter-shape"),
    ("mcp.adapter_source_checked", "mcp-adapter-source-check"),
    ("mcp.adapter_aggregation_checked", "mcp-adapter-aggregation"),
    ("mcp.server_resolution_checked", "mcp-server-resolution"),
    ("mcp.capability_policy_checked", "mcp-capability-policy"),
]
COMPLETION_EVENT = "mcp.readiness_completed"


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def event_access_is_static(event: dict) -> bool:
    return (
        event.get("networkAccess") is False
        and event.get("mcpInvocation") is False
        and event.get("paymentAccess") is False
    )


def check_gate_events(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    cursor = 0

    for expected_event, expected_gate in REQUIRED_GATE_EVENTS:
        match_index = next(
            (
                index
                for index in range(cursor, len(events))
                if events[index].get("event") == expected_event
                and events[index].get("gateId") == expected_gate
            ),
            None,
        )
        if match_index is None:
            findings.append(
                {
                    "status": "fail",
                    "event": expected_event,
                    "gateId": expected_gate,
                    "reason": "Missing required MCP readiness gate evidence event.",
                }
            )
            continue

        event = events[match_index]
        cursor = match_index + 1

        if event.get("status") != "pass":
            findings.append(
                {
                    "status": "fail",
                    "event": expected_event,
                    "gateId": expected_gate,
                    "reason": "Required MCP readiness gate evidence must pass.",
                }
            )

        if not event_access_is_static(event):
            findings.append(
                {
                    "status": "fail",
                    "event": expected_event,
                    "gateId": expected_gate,
                    "reason": "MCP readiness evidence must not claim network, invocation, or payment access.",
                }
            )

    return findings


def check_completion(events: list[dict], gate_findings: list[dict]) -> list[dict]:
    findings: list[dict] = []
    completion_events = [event for event in events if event.get("event") == COMPLETION_EVENT]

    if len(completion_events) != 1:
        return [
            {
                "status": "fail",
                "event": COMPLETION_EVENT,
                "reason": "MCP readiness evidence must include exactly one completion event.",
            }
        ]

    completion = completion_events[0]
    expected_status = "fail" if gate_findings else "pass"

    if completion.get("status") != expected_status or completion.get("requiredGateStatus") != expected_status:
        findings.append(
            {
                "status": "fail",
                "event": COMPLETION_EVENT,
                "reason": "MCP readiness completion status must match required gate status.",
                "expectedStatus": expected_status,
            }
        )

    if not event_access_is_static(completion):
        findings.append(
            {
                "status": "fail",
                "event": COMPLETION_EVENT,
                "reason": "MCP readiness completion must not claim network, invocation, or payment access.",
            }
        )

    return findings


def report(evidence_path: Path) -> dict:
    evidence = read_json(evidence_path)
    events = evidence.get("events", [])

    findings = check_gate_events(events)
    findings.extend(check_completion(events, findings))

    observed_events = [event.get("event") for event in events]
    status = "fail" if findings else "pass"

    return {
        "evidence": display_path(evidence_path),
        "mode": "static-mcp-readiness-evidence-check",
        "status": status,
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "requiredEvents": [event for event, _gate in REQUIRED_GATE_EVENTS] + [COMPLETION_EVENT],
        "observedEvents": observed_events,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    result = report(args.evidence)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
