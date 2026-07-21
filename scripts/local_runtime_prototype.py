#!/usr/bin/env python3
"""Run the bounded local executable ADL runtime prototype evidence suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_local_agent.py"


SCENARIOS = [
    {
        "id": "simple-agent-dry-run",
        "adl": "examples/simple-agent.yaml",
        "args": [],
        "expectedExitCode": 0,
        "expectedCompletionStatus": "pass",
        "expectedTraceEvents": [
            "session.started",
            "model.resolved",
            "tools.registered",
            "policies.loaded",
            "evals.loaded",
            "task.dry_run_completed",
        ],
        "expectedSafetyGate": "supported-simple-runtime",
    },
    {
        "id": "tool-agent-execute-tools",
        "adl": "examples/tool-agent.yaml",
        "args": ["--execute-tools"],
        "expectedExitCode": 0,
        "expectedCompletionStatus": "pass",
        "expectedTraceEvents": [
            "session.started",
            "model.resolved",
            "tools.registered",
            "policies.loaded",
            "evals.loaded",
            "tool.executed",
            "source.checked",
            "task.dry_run_completed",
        ],
        "expectedSafetyGate": "approved-tool-and-source",
    },
    {
        "id": "adl-v02-memory-observability-dry-run",
        "adl": "examples/v0.2/memory-observability-agent.yaml",
        "args": [],
        "expectedExitCode": 0,
        "expectedCompletionStatus": "pass",
        "expectedTraceEvents": [
            "session.started",
            "model.resolved",
            "tools.registered",
            "policies.loaded",
            "evals.loaded",
            "task.dry_run_completed",
        ],
        "expectedSafetyGate": "supported-adl-v02-local-runtime",
    },
    {
        "id": "unsupported-tool-strict-denial",
        "adl": "examples/unsafe/unsupported-tool-fixture.yaml",
        "args": ["--execute-tools"],
        "expectedExitCode": 2,
        "expectedCompletionStatus": None,
        "expectedTraceEvents": [],
        "expectedSafetyGate": "fail-closed-tool-denial",
    },
    {
        "id": "unapproved-source-report-mode",
        "adl": "examples/unsafe/unapproved-source-fixture.yaml",
        "args": ["--execute-tools", "--allow-denied-tools"],
        "expectedExitCode": 0,
        "expectedCompletionStatus": "fail",
        "expectedTraceEvents": [
            "session.started",
            "model.resolved",
            "tools.registered",
            "policies.loaded",
            "evals.loaded",
            "tool.executed",
            "source.checked",
            "task.dry_run_completed",
        ],
        "expectedSafetyGate": "fail-closed-source-check",
    },
    {
        "id": "invalid-runtime-validation",
        "adl": "examples/invalid/bad-runtime-target.yaml",
        "args": [],
        "expectedExitCode": 1,
        "expectedCompletionStatus": None,
        "expectedTraceEvents": [],
        "expectedSafetyGate": "fail-closed-adl-validation",
    },
    {
        "id": "invalid-adl-v02-payment-diagnostics",
        "adl": "examples/invalid/adl-v0.2-x402-missing-authority.yaml",
        "args": ["--json-validation-errors"],
        "expectedExitCode": 1,
        "expectedCompletionStatus": None,
        "expectedTraceEvents": [],
        "expectedSafetyGate": "fail-closed-adl-v02-validation-diagnostics",
    },
]


def compact_stdout(stdout: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(stdout), None
    except json.JSONDecodeError:
        first_line = stdout.strip().splitlines()[0] if stdout.strip() else None
        return None, first_line


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    command = [sys.executable, str(RUNNER), scenario["adl"], *scenario["args"]]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    summary, stdout_first_line = compact_stdout(proc.stdout)
    validation_diagnostics = (summary or {}).get("validationDiagnostics")
    trace_events = [event["event"] for event in (summary or {}).get("trace", [])]
    completion = (summary or {}).get("completion") or {}
    source_summary = (summary or {}).get("sourceCheckSummary")
    tool_execution = (summary or {}).get("toolExecution")
    status = "pass"
    reasons: list[str] = []
    if proc.returncode != scenario["expectedExitCode"]:
        status = "fail"
        reasons.append(f"exit code {proc.returncode} != {scenario['expectedExitCode']}")
    if scenario["expectedCompletionStatus"] is not None:
        if completion.get("status") != scenario["expectedCompletionStatus"]:
            status = "fail"
            reasons.append(f"completion {completion.get('status')} != {scenario['expectedCompletionStatus']}")
    if trace_events != scenario["expectedTraceEvents"]:
        status = "fail"
        reasons.append("trace event sequence mismatch")
    stderr_first_line = proc.stderr.strip().splitlines()[0] if proc.stderr.strip() else None
    return {
        "id": scenario["id"],
        "status": status,
        "reasons": reasons,
        "adl": scenario["adl"],
        "command": " ".join(["python", "scripts/run_local_agent.py", scenario["adl"], *scenario["args"]]),
        "exitCode": proc.returncode,
        "expectedExitCode": scenario["expectedExitCode"],
        "completion": completion or None,
        "traceEvents": trace_events,
        "safetyGate": scenario["expectedSafetyGate"],
        "toolExecution": {
            "mode": tool_execution.get("mode"),
            "networkAccess": tool_execution.get("networkAccess"),
            "paymentAccess": tool_execution.get("paymentAccess"),
            "deniedCount": tool_execution.get("deniedCount"),
        }
        if tool_execution
        else None,
        "sourceCheckSummary": source_summary,
        "stdoutFirstLine": stdout_first_line,
        "stderrFirstLine": stderr_first_line,
        "validationDiagnostics": validation_diagnostics,
    }


def build_report() -> dict[str, Any]:
    scenarios = [run_scenario(scenario) for scenario in SCENARIOS]
    status = "pass" if all(scenario["status"] == "pass" for scenario in scenarios) else "fail"
    return {
        "mode": "local-executable-adl-runtime-prototype",
        "status": status,
        "issue": 224,
        "supportedExamples": [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/v0.2/memory-observability-agent.yaml",
        ],
        "safetyExamples": [
            "examples/unsafe/unsupported-tool-fixture.yaml",
            "examples/unsafe/unapproved-source-fixture.yaml",
            "examples/invalid/bad-runtime-target.yaml",
            "examples/invalid/adl-v0.2-x402-missing-authority.yaml",
        ],
        "boundaries": {
            "localRuntimeExecutionAllowed": True,
            "deterministicLocalFixturesOnly": True,
            "networkAccess": False,
            "paymentAccess": False,
            "credentialAccess": False,
            "mcpInvocation": False,
            "mainnetAccess": False,
            "externalExecutionAllowed": False,
        },
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write the JSON evidence report to this path.")
    args = parser.parse_args()
    report = build_report()
    payload = json.dumps(report, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n")
    print(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
