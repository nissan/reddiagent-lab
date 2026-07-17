#!/usr/bin/env python3
"""Validate ReddiAgent beta release readiness evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "tests" / "fixtures" / "beta-release-readiness.json"

REQUIRED_ENTRY_CRITERIA = {
    "smoke-validation-green",
    "prototype-evidence-current",
    "negative-fixtures-green",
    "operator-controls-reviewed",
    "mainnet-denial-explicit",
}
REQUIRED_EXIT_CRITERIA = {
    "incident-free-window",
    "operator-stop-drill",
    "cost-privacy-review",
    "rollback-evidence-current",
}
REQUIRED_EVENTS = {
    "session.started",
    "policy.checked",
    "eval.checked",
    "cost.estimated",
    "runtime.enabled",
    "runtime.disabled",
    "rollback.started",
    "rollback.completed",
    "incident.opened",
    "task.completed",
    "task.failed",
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
REQUIRED_OPERATOR_CONTROLS = {
    "enable-runtime-path",
    "disable-runtime-path",
    "pause-provider-calls",
    "pause-mcp-invocation",
    "pause-payment-handoff",
    "force-local-only-mode",
}
REQUIRED_INCIDENT_NOTES = {"cost", "safety", "privacy", "incident"}
REQUIRED_RELEASE_EVIDENCE = {
    "docs/LOCAL-RUNNER-READINESS-BUNDLE.md",
    "tests/LOCAL-EXECUTABLE-RUNTIME-PROTOTYPE-REPORT.md",
    "tests/PROVIDER-SANDBOX-PROTOTYPE-REPORT.md",
    "tests/LIVE-MCP-DEVNET-HANDOFF-PROTOTYPE-REPORT.md",
    "tests/BETA-RELEASE-READINESS-REPORT.md",
    "tests/fixtures/beta-release-readiness.json",
    "tests/smoke-validation.sh",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError("Evidence root must be a JSON object.")
    return doc


def values_with_id(rows: Any) -> set[str]:
    if not isinstance(rows, list):
        return set()
    return {row.get("id") for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}


def event_names(rows: Any) -> set[str]:
    if not isinstance(rows, list):
        return set()
    return {row.get("event") for row in rows if isinstance(row, dict) and isinstance(row.get("event"), str)}


def collect_findings(doc: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append({"path": path, "reason": reason})

    require(doc.get("releaseClass") == "executable-beta", "releaseClass", "Release class must be executable-beta.")
    require(doc.get("status") == "beta-candidate", "status", "Status must remain beta-candidate before release.")

    approvals = doc.get("approvals")
    require(isinstance(approvals, dict), "approvals", "Approvals must be present.")
    if isinstance(approvals, dict):
        require(approvals.get("devnetApproved") is True, "approvals.devnetApproved", "Devnet approval must be explicit.")
        require(approvals.get("mainnetApproved") is False, "approvals.mainnetApproved", "Mainnet must be explicitly not approved.")
        require(
            "separate signoff" in str(approvals.get("mainnetStatement", "")).lower(),
            "approvals.mainnetStatement",
            "Mainnet statement must require separate signoff.",
        )

    entry_ids = values_with_id(doc.get("betaEntryCriteria"))
    missing_entry = sorted(REQUIRED_ENTRY_CRITERIA - entry_ids)
    require(not missing_entry, "betaEntryCriteria", f"Missing entry criteria: {', '.join(missing_entry)}")
    for index, criterion in enumerate(doc.get("betaEntryCriteria", []) if isinstance(doc.get("betaEntryCriteria"), list) else []):
        require(criterion.get("required") is True, f"betaEntryCriteria[{index}].required", "Entry criteria must be required.")
        require(criterion.get("status") in {"pass", "ready"}, f"betaEntryCriteria[{index}].status", "Entry criteria must be pass or ready.")

    exit_ids = values_with_id(doc.get("betaExitCriteria"))
    missing_exit = sorted(REQUIRED_EXIT_CRITERIA - exit_ids)
    require(not missing_exit, "betaExitCriteria", f"Missing exit criteria: {', '.join(missing_exit)}")

    evidence_refs = set(doc.get("requiredReleaseEvidence", [])) if isinstance(doc.get("requiredReleaseEvidence"), list) else set()
    missing_evidence = sorted(REQUIRED_RELEASE_EVIDENCE - evidence_refs)
    require(not missing_evidence, "requiredReleaseEvidence", f"Missing release evidence: {', '.join(missing_evidence)}")

    observability = doc.get("observability")
    require(isinstance(observability, dict), "observability", "Observability schema expectations must be present.")
    if isinstance(observability, dict):
        missing_events = sorted(REQUIRED_EVENTS - set(observability.get("requiredEvents", [])))
        require(not missing_events, "observability.requiredEvents", f"Missing required events: {', '.join(missing_events)}")
        missing_fields = sorted(REQUIRED_TRACE_FIELDS - set(observability.get("requiredTraceFields", [])))
        require(not missing_fields, "observability.requiredTraceFields", f"Missing trace fields: {', '.join(missing_fields)}")
        require(
            observability.get("rawSecretLoggingAllowed") is False,
            "observability.rawSecretLoggingAllowed",
            "Raw secret logging must be denied.",
        )
        require(
            observability.get("rawPromptLoggingDefault") == "redacted",
            "observability.rawPromptLoggingDefault",
            "Raw prompt logging must default to redacted.",
        )

    controls = doc.get("operatorControls")
    control_ids = values_with_id(controls)
    missing_controls = sorted(REQUIRED_OPERATOR_CONTROLS - control_ids)
    require(not missing_controls, "operatorControls", f"Missing operator controls: {', '.join(missing_controls)}")
    for index, control in enumerate(controls if isinstance(controls, list) else []):
        require(control.get("ownerRole") == "operator", f"operatorControls[{index}].ownerRole", "Control owner must be operator.")
        require(control.get("auditRequired") is True, f"operatorControls[{index}].auditRequired", "Control must require audit evidence.")

    rollback = doc.get("rollback")
    require(isinstance(rollback, dict), "rollback", "Rollback procedure must be present.")
    if isinstance(rollback, dict):
        require(rollback.get("stopFirst") is True, "rollback.stopFirst", "Rollback must stop runtime paths first.")
        require(rollback.get("maxDisableWindowMinutes", 9999) <= 15, "rollback.maxDisableWindowMinutes", "Runtime disable window must be bounded.")
        steps = rollback.get("orderedSteps")
        require(isinstance(steps, list) and len(steps) >= 5, "rollback.orderedSteps", "Rollback needs at least five ordered steps.")
        require(rollback.get("mainnetRollback") == "not-applicable-mainnet-not-approved", "rollback.mainnetRollback", "Mainnet rollback must be not applicable.")

    note_ids = values_with_id(doc.get("riskAndIncidentNotes"))
    missing_notes = sorted(REQUIRED_INCIDENT_NOTES - note_ids)
    require(not missing_notes, "riskAndIncidentNotes", f"Missing notes: {', '.join(missing_notes)}")

    sample_events = event_names(doc.get("sampleTraceEvents"))
    require(REQUIRED_EVENTS <= sample_events, "sampleTraceEvents", "Sample trace must cover all required event names.")

    return findings


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    findings = collect_findings(doc)
    return {
        "mode": "beta-release-readiness-check",
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "summary": {
            "entryCriteria": len(doc.get("betaEntryCriteria", [])) if isinstance(doc.get("betaEntryCriteria"), list) else 0,
            "exitCriteria": len(doc.get("betaExitCriteria", [])) if isinstance(doc.get("betaExitCriteria"), list) else 0,
            "operatorControls": len(doc.get("operatorControls", [])) if isinstance(doc.get("operatorControls"), list) else 0,
            "sampleTraceEvents": len(doc.get("sampleTraceEvents", [])) if isinstance(doc.get("sampleTraceEvents"), list) else 0,
            "mainnetApproved": doc.get("approvals", {}).get("mainnetApproved") if isinstance(doc.get("approvals"), dict) else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="?", default=str(DEFAULT_EVIDENCE))
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(load_json(Path(args.evidence)))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload)
    else:
        sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 3


if __name__ == "__main__":
    sys.exit(main())
