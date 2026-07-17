#!/usr/bin/env python3
"""Check UI-safe RAP/provider handoff summaries."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "rap-provider-handoff-ui-summaries.json"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/rap_provider_handoff_summaries.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def assert_static_boundary(item: dict) -> None:
    assert item["runtimeExecutionAllowed"] is False
    assert item["networkAccess"] is False
    assert item["paymentAccess"] is False
    assert item["mcpInvocation"] is False


def main() -> int:
    proc = run_cli()
    payload = json.loads(proc.stdout)
    fixture = json.loads(FIXTURE.read_text())
    assert payload == fixture

    assert payload["format"] == "ui-safe-rap-provider-handoff-summaries"
    assert payload["guardrails"]["uiSafe"] is True
    assert payload["guardrails"]["staticFixtureOnly"] is True
    assert payload["guardrails"]["redactsSecrets"] is True
    assert_static_boundary(payload["guardrails"])

    by_kind = {item["kind"]: item for item in payload["summaries"]}
    assert set(by_kind) == {"rap-bridge", "provider-adapter"}

    rap = by_kind["rap-bridge"]
    assert rap["readiness"] == "report-ready"
    assert rap["uiBadge"] == "ready-static-report"
    assert rap["summary"]["bridgeReady"] is True
    assert rap["summary"]["unsafeCount"] == 0
    assert rap["summary"]["unsupportedCount"] == 0
    assert rap["summary"]["conformanceStatus"] == "pass"
    assert "x402.PaymentRequired" in rap["summary"]["metadataOnlySections"]
    assert "tests/test_rap_bridge_report.py" in rap["validationRefs"]
    assert_static_boundary(rap)

    provider = by_kind["provider-adapter"]
    assert provider["status"] == "blocked-report-only"
    assert provider["readiness"] == "blocked-before-codegen"
    assert provider["uiBadge"] == "blocked-static-plan"
    assert provider["summary"]["targetCount"] == 5
    assert provider["summary"]["plannedFileCount"] == 20
    assert provider["summary"]["generationAllowed"] is False
    assert provider["summary"]["requiredSecretRefs"] == [
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
    ]
    assert provider["summary"]["hostedServiceRefs"] == ["mcp:approved-docs-search"]
    assert provider["summary"]["validationGateIds"] == [
        "manifest-fixture-deterministic",
        "manifest-files-report-only",
        "manifest-target-support-metadata",
        "manifest-runtime-boundary-disabled",
    ]
    assert all(item["ids"] for item in provider["summary"]["blockers"])
    assert "tests/test_provider_adapter_codegen_plan.py" in provider["validationRefs"]
    assert_static_boundary(provider)

    for item in payload["summaries"]:
        warnings = item["blockedLiveActionWarnings"]
        assert "no provider or local model call" in warnings
        assert "no MCP server resolution or invocation" in warnings
        assert "no wallet, facilitator, payment rail, or settlement access" in warnings

    single = run_cli(
        "--rap-fixture",
        "tests/fixtures/rap-bridge-x402-paid-mcp-ready.json",
        "--provider-example",
        "examples/mcp-readonly-agent.yaml",
    )
    single_payload = json.loads(single.stdout)
    single_provider = {
        item["kind"]: item for item in single_payload["summaries"]
    }["provider-adapter"]
    assert single_provider["summary"]["plannedFileCount"] == 20
    assert single_provider["summary"]["hostedServiceRefs"] == ["mcp:approved-docs-search"]

    print("PASS RAP/provider handoff summaries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
