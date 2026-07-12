#!/usr/bin/env python3
"""Check report-only Agent Spec compatibility output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_report(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/agent_spec_compatibility.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/agent_spec_compatibility.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_static_boundaries(report: dict) -> None:
    assert report["runtimeExecutionAllowed"] is False
    assert report["networkAccess"] is False
    assert report["paymentAccess"] is False
    assert report["mcpInvocation"] is False
    mapped = report["mappedDocument"]
    assert mapped["format"] == "agent-spec-compatible-review"
    assert mapped["component"]["metadata"]["reddiagentApiVersion"] == "reddiagent.dev/v0.1"


def main() -> int:
    reports = run_report("examples/simple-agent.yaml", "examples/payment-agent.yaml")
    by_agent = {report["agent"]: report for report in reports}

    simple = by_agent["simple-research-helper"]
    assert simple["target"] == "agent-spec"
    assert simple["supported"] is True
    assert simple["lossless"] is False
    assert simple["unsupportedFeatures"] == []
    assert "harness.policies" in simple["metadataOnlyExtensions"]
    assert "harness.evalGates" in simple["metadataOnlyExtensions"]
    assert_static_boundaries(simple)

    payment = by_agent["paid-specialist-researcher"]
    assert payment["target"] == "agent-spec"
    assert payment["supported"] is True
    assert payment["lossless"] is False
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    assert payment["mappedDocument"]["component"]["metadata"]["extensions"]["x402"]["enabled"] is True
    assert_static_boundaries(payment)

    refused = run_command(
        "--export-agent-spec",
        "examples/simple-agent.yaml",
        "examples/payment-agent.yaml",
    )
    assert refused.returncode == 3
    assert refused.stdout == ""
    refusal = json.loads(refused.stderr)
    assert refusal["error"] == "agent_spec_export_would_drop_reddi_semantics"
    assert refusal["runtimeExecutionAllowed"] is False
    assert refusal["networkAccess"] is False
    assert refusal["paymentAccess"] is False
    assert refusal["mcpInvocation"] is False
    refused_agents = {item["agent"]: item for item in refusal["diagnostics"]}
    assert "harness.policies" in refused_agents["simple-research-helper"]["metadataOnlyExtensions"]
    assert "live_payment_execution" in refused_agents["paid-specialist-researcher"]["unsupportedFeatures"]

    exported = run_command(
        "--export-agent-spec",
        "--single",
        "tests/fixtures/agent-spec-lossless-agent.yaml",
    )
    assert exported.returncode == 0
    exported_doc = json.loads(exported.stdout)
    assert exported_doc["format"] == "agent-spec-compatible-review"
    assert exported_doc["component"]["name"] == "lossless-agent-spec-review-agent"
    assert exported_doc["component"]["metadata"]["metadataOnlySections"] == []

    exported_yaml = run_command(
        "--export-agent-spec",
        "--output-format",
        "yaml",
        "--single",
        "tests/fixtures/agent-spec-lossless-agent.yaml",
    )
    assert exported_yaml.returncode == 0
    assert "format: agent-spec-compatible-review" in exported_yaml.stdout
    assert "name: lossless-agent-spec-review-agent" in exported_yaml.stdout

    print("PASS Agent Spec compatibility")
    return 0


if __name__ == "__main__":
    sys.exit(main())
