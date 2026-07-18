#!/usr/bin/env python3
"""Readiness bundle drift checks."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs" / "LOCAL-RUNNER-READINESS-BUNDLE.md"
SMOKE = ROOT / "tests" / "smoke-validation.sh"

REQUIRED_BUNDLE_REFERENCES = [
    "tests/TOOL-EXECUTION-FIXTURE-REPORT.md",
    "tests/CLI-USAGE-MATRIX.md",
    "tests/LEVEL-1-CONFORMANCE-REPORT.md",
    "tests/MCP-ADAPTER-SHAPE-REPORT.md",
    "tests/MCP-ADAPTER-CONTRACT-REPORT.md",
    "tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md",
    "tests/MCP-ADAPTER-AGGREGATION-REPORT.md",
    "tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md",
    "tests/MCP-SERVER-RESOLUTION-REPORT.md",
    "tests/MCP-CAPABILITY-POLICY-REPORT.md",
    "tests/MCP-READINESS-EVIDENCE-REPORT.md",
    "docs/MCP-READINESS-RELEASE-CHECKLIST.md",
    "tests/BETA-OPERATOR-CONTROL-HARNESS-REPORT.md",
    "tests/BETA-RELEASE-READINESS-REPORT.md",
    "tests/BETA-LOCAL-RUNTIME-RC-GATE-REPORT.md",
    "tests/PROVIDER-ADAPTER-GENERATED-CODE-SANDBOX-BETA-REPORT.md",
    "tests/RAP-BRIDGE-LOCAL-DRY-RUN-REPORT.md",
    "docs/BETA-RELEASE-READINESS-RUNBOOK.md",
    "tests/test_tool_execution.py",
    "tests/test_cli_usage_matrix.py",
    "tests/test_readiness_bundle.py",
    "tests/test_adapter_readiness.py",
    "tests/test_mcp_adapter_contract.py",
    "tests/test_mcp_adapter_error_semantics.py",
    "tests/test_mcp_adapter_aggregation.py",
    "tests/test_mcp_adapter_source_check.py",
    "tests/test_mcp_server_resolution.py",
    "tests/test_mcp_capability_policy.py",
    "tests/test_mcp_readiness_evidence.py",
    "tests/test_mcp_readiness_release.py",
    "tests/test_beta_operator_control_harness.py",
    "tests/test_beta_release_readiness.py",
    "tests/test_beta_local_runtime_rc_gate.py",
    "tests/test_provider_adapter_generated_code_sandbox_beta.py",
    "tests/test_rap_bridge_local_dry_run.py",
    "--fail-on-required-gate",
    "completion.status",
    "No live retriever.",
    "No MCP server invocation.",
    "No live x402 payment or settlement.",
    "No mainnet deployment, settlement, or run without separate signoff.",
]

REQUIRED_SMOKE_COMMANDS = [
    "scripts/validate_examples.py",
    "tests/test_tool_execution.py",
    "tests/test_cli_usage_matrix.py",
    "tests/test_readiness_bundle.py",
    "tests/test_adapter_readiness.py",
    "tests/test_mcp_adapter_contract.py",
    "tests/test_mcp_adapter_error_semantics.py",
    "tests/test_mcp_adapter_aggregation.py",
    "tests/test_mcp_adapter_source_check.py",
    "tests/test_mcp_server_resolution.py",
    "tests/test_mcp_capability_policy.py",
    "tests/test_mcp_readiness_evidence.py",
    "tests/test_mcp_readiness_release.py",
    "tests/test_beta_operator_control_harness.py",
    "tests/test_beta_release_readiness.py",
    "tests/test_beta_local_runtime_rc_gate.py",
    "tests/test_provider_adapter_generated_code_sandbox_beta.py",
    "tests/test_rap_bridge_local_dry_run.py",
]


def main() -> int:
    bundle = BUNDLE.read_text()
    smoke = SMOKE.read_text()

    for reference in REQUIRED_BUNDLE_REFERENCES:
        assert reference in bundle, f"Missing readiness reference: {reference}"

    for command in REQUIRED_SMOKE_COMMANDS:
        assert command in smoke, f"Missing smoke command: {command}"

    checklist_items = [line for line in bundle.splitlines() if line.startswith("- [ ] ")]
    assert len(checklist_items) >= 8, "Readiness checklist is too thin."

    print("PASS readiness bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
