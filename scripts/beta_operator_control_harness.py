#!/usr/bin/env python3
"""Run deterministic beta operator-control harness scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-control-scenarios.json"

REQUIRED_CONTROLS = {
    "enable-runtime-path",
    "disable-runtime-path",
    "pause-provider-calls",
    "pause-mcp-invocation",
    "pause-payment-handoff",
    "force-local-only-mode",
}
REQUIRED_EVENTS = {
    "policy.checked",
    "cost.estimated",
    "runtime.enabled",
    "runtime.disabled",
    "rollback.started",
    "rollback.completed",
}
REQUIRED_TRACE_FIELDS = {
    "traceId",
    "agentId",
    "taskId",
    "releaseId",
    "operatorId",
    "runtimeMode",
    "environment",
    "policyResults",
    "evalResults",
    "costEstimate",
    "privacyRedactions",
    "mainnetAllowed",
    "rollbackReference",
    "incidentReference",
}
SENSITIVE_FIELDS = {"rawPrompt", "rawSecret", "credential", "walletHandle", "paymentProof"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError("Harness fixture root must be a JSON object.")
    return doc


def privacy_redactions(scenario: dict[str, Any]) -> dict[str, Any]:
    payload = scenario.get("privacyPayload", {})
    sensitive = sorted(field for field in payload if field in SENSITIVE_FIELDS)
    return {
        "status": "fail" if sensitive else "pass",
        "rawPromptLogging": "redacted",
        "redactedFields": sensitive,
        "redactedPromptRef": payload.get("redactedPromptRef"),
    }


def trace_context(doc: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    cost = scenario["costEstimate"]
    rollback = scenario.get("rollback", {})
    return {
        "traceId": scenario["traceId"],
        "agentId": scenario.get("agentId", "reddiagent-local-beta-agent"),
        "taskId": scenario.get("taskId", scenario["id"]),
        "releaseId": doc.get("releaseId"),
        "operatorId": scenario.get("operatorId", "operator://local-beta"),
        "runtimeMode": scenario["runtimeMode"],
        "environment": scenario["environment"],
        "policyResults": {
            "localOnly": scenario["localOnly"],
            "mainnetRequested": scenario.get("mainnetRequested") is True,
            "requiredControlsPresent": REQUIRED_CONTROLS <= set(scenario["operatorControls"]),
        },
        "evalResults": {
            "status": "not-run-before-operator-gate",
            "reason": "operator-control-harness",
        },
        "costEstimate": {
            "amountUsd": cost["amountUsd"],
            "ceilingUsd": cost["ceilingUsd"],
            "withinCeiling": cost["amountUsd"] <= cost["ceilingUsd"],
        },
        "privacyRedactions": privacy_redactions(scenario),
        "mainnetAllowed": doc.get("approvals", {}).get("mainnetApproved") is True,
        "rollbackReference": rollback.get("reference"),
        "incidentReference": scenario.get("incidentReference", "none"),
    }


def event(context: dict[str, Any], name: str, status: str = "pass", **fields: Any) -> dict[str, Any]:
    payload = {"event": name, "status": status, **context}
    payload.update(fields)
    return payload


def denied_result(scenario: dict[str, Any], reason: str, trace: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "expectedCompletionStatus": scenario["expectedCompletionStatus"],
        "completionStatus": "fail",
        "failClosed": True,
        "reason": reason,
        "enabledRuntimePath": None,
        "nextRuntimeMode": "local-only",
        "traceEvents": trace,
    }


def evaluate_scenario(doc: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    context = trace_context(doc, scenario)
    approvals = doc["approvals"]
    cost = scenario["costEstimate"]
    controls = set(scenario["operatorControls"])
    trace = [
        event(
            context,
            "policy.checked",
            mainnetAllowed=approvals["mainnetApproved"],
            runtimeMode=scenario["runtimeMode"],
            environment=scenario["environment"],
            localOnly=scenario["localOnly"],
        ),
        event(
            context,
            "cost.estimated",
            amountUsd=cost["amountUsd"],
            ceilingUsd=cost["ceilingUsd"],
            withinCeiling=cost["amountUsd"] <= cost["ceilingUsd"],
        ),
    ]

    if scenario["environment"] == "mainnet" or scenario.get("mainnetRequested"):
        trace.append(event(context, "runtime.disabled", "fail", reason="mainnet-not-approved"))
        return denied_result(scenario, "mainnet-not-approved", trace)

    if not scenario["localOnly"]:
        trace.append(event(context, "runtime.disabled", "fail", reason="non-local-runtime-disabled"))
        return denied_result(scenario, "non-local-runtime-disabled", trace)

    if cost["amountUsd"] > cost["ceilingUsd"]:
        trace.append(event(context, "runtime.disabled", "fail", reason="cost-ceiling-exceeded"))
        return denied_result(scenario, "cost-ceiling-exceeded", trace)

    if any(field in scenario.get("privacyPayload", {}) for field in SENSITIVE_FIELDS):
        trace.append(event(context, "runtime.disabled", "fail", reason="sensitive-payload-denied"))
        return denied_result(scenario, "sensitive-payload-denied", trace)

    missing_controls = REQUIRED_CONTROLS - controls
    if missing_controls:
        trace.append(
            event(
                context,
                "runtime.disabled",
                "fail",
                reason="operator-control-missing",
                missingControls=sorted(missing_controls),
            )
        )
        return denied_result(scenario, "operator-control-missing", trace)

    rollback = scenario["rollback"]
    if not rollback.get("stopFirst") or not rollback.get("disableVerified"):
        trace.append(event(context, "runtime.disabled", "fail", reason="rollback-stop-not-verified"))
        return denied_result(scenario, "rollback-stop-not-verified", trace)

    trace.extend(
        [
            event(
                context,
                "runtime.enabled",
                runtimePath=scenario["runtimePath"],
                runtimeMode=scenario["runtimeMode"],
                localOnly=True,
            ),
            event(context, "runtime.disabled", runtimePath=scenario["runtimePath"], reason="operator-drill"),
            event(context, "rollback.started", rollbackReference=rollback["reference"]),
            event(
                context,
                "rollback.completed",
                rollbackReference=rollback["reference"],
                disableVerified=True,
                mainnetRollback="not-applicable-mainnet-not-approved",
            ),
        ]
    )
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "expectedCompletionStatus": scenario["expectedCompletionStatus"],
        "completionStatus": "pass",
        "failClosed": False,
        "reason": "operator-control-drill-complete",
        "enabledRuntimePath": scenario["runtimePath"],
        "nextRuntimeMode": "local-only",
        "traceEvents": trace,
    }


def collect_findings(doc: dict[str, Any], results: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append({"path": path, "reason": reason})

    approvals = doc.get("approvals")
    require(isinstance(approvals, dict), "approvals", "Approvals must be present.")
    if isinstance(approvals, dict):
        require(approvals.get("mainnetApproved") is False, "approvals.mainnetApproved", "Mainnet must remain not approved.")
        require("separate signoff" in approvals.get("mainnetStatement", "").lower(), "approvals.mainnetStatement", "Mainnet statement must require separate signoff.")

    boundary = doc.get("boundaries")
    require(isinstance(boundary, dict), "boundaries", "Boundaries must be present.")
    if isinstance(boundary, dict):
        require(boundary.get("localOnly") is True, "boundaries.localOnly", "Harness must be local-only.")
        require(boundary.get("networkAccess") is False, "boundaries.networkAccess", "Harness must not use network access.")
        require(boundary.get("credentialAccess") is False, "boundaries.credentialAccess", "Harness must not access credentials.")
        require(boundary.get("paymentAccess") is False, "boundaries.paymentAccess", "Harness must not access payment rails.")
        require(boundary.get("mainnetAccess") is False, "boundaries.mainnetAccess", "Harness must not use mainnet.")

    scenario_rows = doc.get("scenarios")
    require(isinstance(scenario_rows, list) and len(scenario_rows) >= 5, "scenarios", "Harness needs one positive and at least four negative scenarios.")
    require(any(row.get("kind") == "positive" for row in scenario_rows if isinstance(row, dict)), "scenarios", "Missing positive control scenario.")
    require(any(row.get("kind") == "negative" for row in scenario_rows if isinstance(row, dict)), "scenarios", "Missing fail-closed negative scenarios.")

    for index, result in enumerate(results):
        require(
            result["completionStatus"] == result["expectedCompletionStatus"],
            f"results[{index}].completionStatus",
            "Scenario did not match expected completion status.",
        )
        if result["kind"] == "negative":
            require(result["completionStatus"] == "fail", f"results[{index}].completionStatus", "Negative scenario must fail.")
            require(result["failClosed"] is True, f"results[{index}].failClosed", "Negative scenario must fail closed.")

    all_events = {row["event"] for result in results for row in result["traceEvents"]}
    missing_events = sorted(REQUIRED_EVENTS - all_events)
    require(not missing_events, "traceEvents", f"Missing required events: {', '.join(missing_events)}")
    for result_index, result in enumerate(results):
        for event_index, trace_event in enumerate(result["traceEvents"]):
            missing_fields = sorted(REQUIRED_TRACE_FIELDS - set(trace_event))
            require(
                not missing_fields,
                f"results[{result_index}].traceEvents[{event_index}]",
                f"Missing required trace fields: {', '.join(missing_fields)}",
            )

    return findings


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    results = [evaluate_scenario(doc, scenario) for scenario in doc["scenarios"]]
    findings = collect_findings(doc, results)
    return {
        "mode": "beta-operator-control-harness",
        "issue": 235,
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "releaseId": doc.get("releaseId"),
        "boundaries": doc.get("boundaries"),
        "operatorControls": sorted(REQUIRED_CONTROLS),
        "requiredEvents": sorted(REQUIRED_EVENTS),
        "requiredTraceFields": sorted(REQUIRED_TRACE_FIELDS),
        "summary": {
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["failClosed"]),
            "mainnetApproved": doc.get("approvals", {}).get("mainnetApproved") if isinstance(doc.get("approvals"), dict) else None,
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="?", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(load_json(Path(args.scenarios)))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 3


if __name__ == "__main__":
    sys.exit(main())
