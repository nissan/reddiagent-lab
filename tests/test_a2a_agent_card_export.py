#!/usr/bin/env python3
"""Check report-only A2A Agent Card export output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_report(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/adl_to_a2a_agent_card.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/adl_to_a2a_agent_card.py", *args],
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
    assert mapped["format"] == "a2a-agent-card-review"
    assert mapped["targetPath"] == "/.well-known/agent-card.json"
    card_metadata = mapped["agentCard"]["metadata"]
    assert card_metadata["reddiagentApiVersion"] == "reddiagent.dev/v0.1"
    assert card_metadata["runtimeExecutionAllowed"] is False
    assert card_metadata["networkAccess"] is False
    assert card_metadata["paymentAccess"] is False
    assert card_metadata["mcpInvocation"] is False


def main() -> int:
    reports = run_report("examples/simple-agent.yaml", "examples/payment-agent.yaml")
    by_agent = {report["agent"]: report for report in reports}

    simple = by_agent["simple-research-helper"]
    assert simple["target"] == "a2a-agent-card"
    assert simple["supported"] is True
    assert simple["lossless"] is False
    assert simple["unsupportedFeatures"] == []
    assert "harness.instructions" in simple["metadataOnlyExtensions"]
    assert "harness.memory" in simple["metadataOnlyExtensions"]
    assert "harness.policies" in simple["metadataOnlyExtensions"]
    assert "harness.evalGates" in simple["metadataOnlyExtensions"]
    simple_card = simple["mappedDocument"]["agentCard"]
    assert simple_card["name"] == "simple-research-helper"
    assert simple_card["supportedInterfaces"][0]["protocolBinding"] == "HTTP+JSON"
    assert simple_card["supportedInterfaces"][0]["protocolVersion"] == "1.0"
    assert simple_card["defaultInputModes"] == ["text/plain"]
    assert simple_card["defaultOutputModes"] == ["text/plain", "application/json"]
    assert simple_card["skills"][0]["id"] == "simple-research-helper"
    assert_static_boundaries(simple)

    payment = by_agent["paid-specialist-researcher"]
    assert payment["target"] == "a2a-agent-card"
    assert payment["supported"] is True
    assert payment["lossless"] is False
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    payment_card = payment["mappedDocument"]["agentCard"]
    assert payment_card["skills"][0]["id"] == "fetch_approved_url"
    assert payment_card["metadata"]["extensions"]["x402"]["enabled"] is True
    assert_static_boundaries(payment)

    lossy = run_command(
        "--export-agent-card",
        "tests/fixtures/a2a-agent-card-lossy-agent.yaml",
    )
    assert lossy.returncode == 3
    assert lossy.stdout == ""
    refusal = json.loads(lossy.stderr)
    assert refusal["error"] == "a2a_agent_card_export_would_drop_reddi_semantics"
    assert refusal["runtimeExecutionAllowed"] is False
    assert refusal["networkAccess"] is False
    assert refusal["paymentAccess"] is False
    assert refusal["mcpInvocation"] is False
    assert "extensions.x402" in refusal["diagnostics"][0]["metadataOnlyExtensions"]
    assert "live_payment_execution" in refusal["diagnostics"][0]["unsupportedFeatures"]

    exported = run_command(
        "--export-agent-card",
        "--single",
        "tests/fixtures/a2a-agent-card-lossless-agent.yaml",
    )
    assert exported.returncode == 0
    exported_card = json.loads(exported.stdout)
    assert exported_card["name"] == "lossless-a2a-card-agent"
    assert exported_card["supportedInterfaces"][0]["url"] == "https://example.invalid/a2a/lossless-a2a-card-agent"
    assert exported_card["capabilities"]["streaming"] is False
    assert exported_card["skills"][0]["id"] == "lossless-a2a-card-agent"
    assert exported_card["metadata"]["metadataOnlySections"] == []
    assert exported_card["metadata"]["runtimeExecutionAllowed"] is False

    exported_yaml = run_command(
        "--export-agent-card",
        "--output-format",
        "yaml",
        "--single",
        "tests/fixtures/a2a-agent-card-lossless-agent.yaml",
    )
    assert exported_yaml.returncode == 0
    assert "name: lossless-a2a-card-agent" in exported_yaml.stdout
    assert "targetPath" not in exported_yaml.stdout

    print("PASS A2A Agent Card export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
