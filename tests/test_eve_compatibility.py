#!/usr/bin/env python3
"""Check static Vercel eve compatibility reports."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "eve-compatibility-report.json"


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/eve_compatibility.py", *args],
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
    assert report["deploymentAllowed"] is False


def main() -> int:
    proc = run_command()
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    fixture_payload = json.loads(FIXTURE.read_text())
    assert payload == fixture_payload

    by_agent = {report["agent"]: report for report in payload}

    simple = by_agent["simple-research-helper"]
    assert simple["status"] == "report-ready-with-metadata-only-semantics"
    assert simple["unsupportedFeatures"] == []
    assert simple["metadataOnlySections"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.memory",
    ]
    assert simple["projectManifest"]["projectRoot"] == "eve/simple-research-helper"
    assert simple["projectManifest"]["files"][0]["path"] == "agent/instructions.md"
    assert_static_boundaries(simple)

    tool = by_agent["source-checker"]
    assert tool["supported"] is True
    assert tool["projectManifest"]["toolManifest"][0]["eveSlot"] == "agent/tools/search_docs.ts"
    assert tool["projectManifest"]["toolManifest"][0]["status"] == "static-stub-plan"
    assert "harness.policies" in tool["metadataOnlySections"]
    assert_static_boundaries(tool)

    mcp = by_agent["mcp-readonly-docs"]
    assert mcp["status"] == "report-ready-with-unsupported-runtime-features"
    assert mcp["unsupportedFeatures"] == ["mcp_runtime_invocation"]
    connection = mcp["projectManifest"]["connections"][0]
    assert connection["eveSlot"] == "agent/connections/docs_search.ts"
    assert connection["status"] == "metadata-only"
    assert connection["serverRef"] == "approved-docs-search"
    assert_static_boundaries(mcp)

    payment = by_agent["paid-specialist-researcher"]
    assert payment["status"] == "report-ready-with-unsupported-runtime-features"
    assert payment["unsupportedFeatures"] == [
        "non_local_runtime_execution",
        "live_payment_execution",
        "receipt_enforcement",
        "reputation_emission",
    ]
    assert "extensions.x402" in payment["metadataOnlySections"]
    assert "extensions.receipts" in payment["metadataOnlySections"]
    assert "extensions.reputation" in payment["metadataOnlySections"]
    assert_static_boundaries(payment)

    invalid = by_agent["invalid-missing-instructions"]
    assert invalid["supported"] is False
    assert invalid["status"] == "blocked-by-validation"
    assert invalid["unsupportedFeatures"] == ["validation_failed"]
    assert invalid["validationErrors"] == ["harness: 'instructions' is a required property"]
    assert_static_boundaries(invalid)

    single = run_command("--single", "examples/mcp-readonly-agent.yaml")
    assert single.returncode == 0
    single_payload = json.loads(single.stdout)
    assert single_payload["agent"] == "mcp-readonly-docs"
    assert single_payload["projectManifest"]["connections"][0]["toolName"] == "search"

    print("PASS Vercel eve compatibility report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
