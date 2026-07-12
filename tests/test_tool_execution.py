#!/usr/bin/env python3
"""Safe local tool execution fixture checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_tool_agent() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/run_local_agent.py", "examples/tool-agent.yaml", "--execute-tools"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_denied_agent(path: str) -> dict:
    proc = subprocess.run(
        [
            PYTHON,
            "scripts/run_local_agent.py",
            path,
            "--execute-tools",
            "--allow-denied-tools",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_strict_denied_agent(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/run_local_agent.py", path, "--execute-tools"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_fail_on_required_gate(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            PYTHON,
            "scripts/run_local_agent.py",
            path,
            "--execute-tools",
            "--allow-denied-tools",
            "--fail-on-required-gate",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_denied(doc: dict, expected_tool_id: str, expected_reason_fragment: str) -> None:
    execution = doc["toolExecution"]
    assert execution["networkAccess"] is False
    assert execution["paymentAccess"] is False
    assert execution["deniedCount"] == 1
    assert doc["completion"]["transportStatus"] == "pass"
    assert doc["completion"]["requiredGateStatus"] == "fail"
    assert doc["completion"]["status"] == "fail"
    result = execution["results"][0]
    assert result["toolId"] == expected_tool_id
    assert result["status"] == "denied"
    assert expected_reason_fragment in result["error"]
    assert result["guidance"]["tool_id"] == expected_tool_id
    assert result["guidance"]["reference"] == "specs/TOOL-REGISTRY-v0.1.md"
    assert "why" in " ".join(result["guidance"])
    assert "output" not in result
    events = [event["event"] for event in doc["trace"]]
    assert "tool.denied" in events
    assert "tool.executed" not in events
    assert doc["sourceChecks"] == []
    assert doc["sourceCheckSummary"] == {
        "total": 0,
        "passCount": 0,
        "failCount": 0,
        "requiredFailureCount": 0,
        "status": "pass",
    }


def assert_unapproved_source(doc: dict) -> None:
    execution = doc["toolExecution"]
    assert execution["networkAccess"] is False
    assert execution["paymentAccess"] is False
    assert execution["deniedCount"] == 0
    assert doc["completion"]["transportStatus"] == "pass"
    assert doc["completion"]["requiredGateStatus"] == "fail"
    assert doc["completion"]["status"] == "fail"
    assert doc["completion"]["reason"] == "dry-run transport completed, but required gates failed"
    result = execution["results"][0]
    assert result["toolId"] == "unsafe_source_docs"
    assert result["status"] == "success"
    assert result["output"]["title"] == "Unapproved External Source"
    assert result["output"]["url"] == "https://example.invalid/reddiagent"
    assert doc["sourceChecks"] == [
        {
            "gateId": "approved-source-output",
            "toolId": "unsafe_source_docs",
            "status": "fail",
            "title": "Unapproved External Source",
            "url": "https://example.invalid/reddiagent",
            "message": "Tool output cites a source outside the approved in-repo source list.",
            "guidance": {
                "gate_id": "approved-source-output",
                "tool_id": "unsafe_source_docs",
                "problem": (
                    "Tool output cites an unapproved source: title='Unapproved External Source', "
                    "url='https://example.invalid/reddiagent'."
                ),
                "why_it_matters": (
                    "A successful fixture tool call only proves execution succeeded. "
                    "Source trust must be checked separately so a local fixture cannot smuggle "
                    "unsupported web, MCP, credential, or payment evidence into the answer."
                ),
                "fix": (
                    "Return one of the approved in-repo sources from the local fixture, or add a "
                    "project-owned source to the approved list with review and tests."
                ),
                "snippet": (
                    "output:\n"
                    "  title: Tool Registry Contract v0.1\n"
                    "  url: specs/TOOL-REGISTRY-v0.1.md"
                ),
                "reference": "specs/DATA-SOURCE-CONTRACT-v0.1.md",
            },
        }
    ]
    assert doc["sourceCheckSummary"] == {
        "total": 1,
        "passCount": 0,
        "failCount": 1,
        "requiredFailureCount": 1,
        "status": "fail",
    }
    guidance = doc["sourceChecks"][0]["guidance"]
    assert guidance["tool_id"] == "unsafe_source_docs"
    assert guidance["reference"] == "specs/DATA-SOURCE-CONTRACT-v0.1.md"
    assert "Source trust" in guidance["why_it_matters"]
    assert "approved in-repo sources" in guidance["fix"]
    source_events = [event for event in doc["trace"] if event["event"] == "source.checked"]
    assert len(source_events) == 1
    assert source_events[0]["gateId"] == "approved-source-output"
    assert source_events[0]["toolId"] == "unsafe_source_docs"
    assert source_events[0]["status"] == "fail"
    completion_events = [event for event in doc["trace"] if event["event"] == "task.dry_run_completed"]
    assert completion_events[0]["status"] == "fail"
    assert completion_events[0]["reason"] == "dry-run transport completed, but required gates failed"


def main() -> int:
    doc = run_tool_agent()
    execution = doc["toolExecution"]
    assert execution["mode"] == "local-fixture"
    assert execution["networkAccess"] is False
    assert execution["paymentAccess"] is False
    assert doc["completion"] == {
        "transportStatus": "pass",
        "requiredGateStatus": "pass",
        "status": "pass",
        "reason": "dry-run transport completed and required gates passed",
    }
    assert len(execution["results"]) == 1
    result = execution["results"][0]
    assert result["toolId"] == "search_docs"
    assert result["status"] == "success"
    assert result["output"]["title"] == "Tool Registry Contract v0.1"
    assert doc["sourceChecks"] == [
        {
            "gateId": "approved-source-output",
            "toolId": "search_docs",
            "status": "pass",
            "title": "Tool Registry Contract v0.1",
            "url": "specs/TOOL-REGISTRY-v0.1.md",
            "message": "Tool output cites an approved in-repo source.",
        }
    ]
    assert doc["sourceCheckSummary"] == {
        "total": 1,
        "passCount": 1,
        "failCount": 0,
        "requiredFailureCount": 0,
        "status": "pass",
    }
    events = [event["event"] for event in doc["trace"]]
    assert events == [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "tool.executed",
        "source.checked",
        "task.dry_run_completed",
    ]
    undeclared = run_denied_agent("examples/unsafe/undeclared-tool-fixture.yaml")
    assert_denied(undeclared, "read_secret", "undeclared tool")
    unsupported = run_denied_agent("examples/unsafe/unsupported-tool-fixture.yaml")
    assert_denied(unsupported, "shell_exec", "unsupported local fixture tool")
    unapproved = run_denied_agent("examples/unsafe/unapproved-source-fixture.yaml")
    assert_unapproved_source(unapproved)
    fail_unapproved = run_fail_on_required_gate("examples/unsafe/unapproved-source-fixture.yaml")
    assert fail_unapproved.returncode == 3
    assert json.loads(fail_unapproved.stdout)["completion"]["requiredGateStatus"] == "fail"
    fail_undeclared = run_fail_on_required_gate("examples/unsafe/undeclared-tool-fixture.yaml")
    assert fail_undeclared.returncode == 3
    assert json.loads(fail_undeclared.stdout)["toolExecution"]["deniedCount"] == 1
    strict = run_strict_denied_agent("examples/unsafe/undeclared-tool-fixture.yaml")
    assert strict.returncode == 2
    assert "DENIED examples/unsafe/undeclared-tool-fixture.yaml" in strict.stderr
    assert "Why it matters" in strict.stderr
    assert "Minimal snippet" in strict.stderr
    strict_unsupported = run_strict_denied_agent("examples/unsafe/unsupported-tool-fixture.yaml")
    assert strict_unsupported.returncode == 2
    assert "declared but not implemented" in strict_unsupported.stderr
    print("PASS safe local tool execution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
