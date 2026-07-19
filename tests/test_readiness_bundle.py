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
    "tests/BETA-OPERATOR-DRY-RUN-PACKAGE-REPORT.md",
    "tests/BETA-REVIEW-UI-REPORT.md",
    "tests/BETA-OPERATOR-DECISION-PACKAGE-REPORT.md",
    "tests/BETA-ACTIVATION-PREFLIGHT-GATE-REPORT.md",
    "tests/BETA-ACTIVATION-REHEARSAL-PACKAGE-REPORT.md",
    "tests/BETA-ACTIVATION-ACCEPTANCE-BUNDLE-REPORT.md",
    "tests/BETA-RELEASE-CANDIDATE-BUNDLE-REPORT.md",
    "tests/BETA-RELEASE-ARCHIVE-ASSEMBLER-REPORT.md",
    "tests/BETA-ONBOARDING-QUICKSTART-PACKAGE-REPORT.md",
    "tests/BETA-REVIEWER-ACCEPTANCE-CHECKLIST-REPORT.md",
    "tests/BETA-E2E-ACCEPTANCE-SMOKE-REPORT.md",
    "tests/BETA-RUNTIME-ACTIVATION-EVIDENCE-GATE-REPORT.md",
    "tests/BETA-RUNTIME-ACTIVATION-CANARY-RUNNER-REPORT.md",
    "tests/BETA-RUNTIME-SERVICE-ACTIVATION-APPROVAL-PACKET-REPORT.md",
    "tests/BETA-RUNTIME-SERVICE-ACTIVATION-EVIDENCE-GATE-REPORT.md",
    "tests/BETA-RUNTIME-SERVICE-ACTIVATION-LIVE-RUN-GATE-REPORT.md",
    "tests/COOLIFY-DEVNET-PUBLIC-DEMO-REPORT.md",
    "docs/beta-review-ui.html",
    "tests/PROVIDER-ADAPTER-GENERATED-CODE-SANDBOX-BETA-REPORT.md",
    "tests/RAP-BRIDGE-LOCAL-DRY-RUN-REPORT.md",
    "docs/BETA-RELEASE-READINESS-RUNBOOK.md",
    "tests/SURFPOOL-VALIDATOR-LANE-REPORT.md",
    "tests/DOCKER-TESTING-LANE-REPORT.md",
    "tests/COOLIFY-STAGING-LANE-REPORT.md",
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
    "tests/test_beta_operator_dry_run_package.py",
    "tests/test_beta_review_ui.py",
    "tests/test_beta_operator_decision_package.py",
    "tests/test_beta_activation_preflight_gate.py",
    "tests/test_beta_activation_rehearsal_package.py",
    "tests/test_beta_activation_acceptance_bundle.py",
    "tests/test_beta_release_candidate_bundle.py",
    "tests/test_beta_release_archive_assembler.py",
    "tests/test_beta_onboarding_quickstart_package.py",
    "tests/test_beta_reviewer_acceptance_checklist_package.py",
    "tests/test_beta_e2e_acceptance_smoke_runner.py",
    "tests/test_beta_runtime_activation_evidence_gate.py",
    "tests/test_beta_runtime_activation_canary_runner.py",
    "tests/test_beta_runtime_service_activation_approval_packet.py",
    "tests/test_beta_runtime_service_activation_evidence_gate.py",
    "tests/test_beta_runtime_service_activation_live_run_gate.py",
    "tests/test_coolify_devnet_public_demo.py",
    "tests/test_provider_adapter_generated_code_sandbox_beta.py",
    "tests/test_rap_bridge_local_dry_run.py",
    "tests/test_surfpool_validator_lane.py",
    "tests/test_docker_testing_lane.py",
    "tests/test_coolify_staging_lane.py",
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
    "tests/test_beta_operator_dry_run_package.py",
    "tests/test_beta_review_ui.py",
    "tests/test_beta_operator_decision_package.py",
    "tests/test_beta_activation_preflight_gate.py",
    "tests/test_beta_activation_rehearsal_package.py",
    "tests/test_beta_activation_acceptance_bundle.py",
    "tests/test_beta_release_candidate_bundle.py",
    "tests/test_beta_release_archive_assembler.py",
    "tests/test_beta_onboarding_quickstart_package.py",
    "tests/test_beta_reviewer_acceptance_checklist_package.py",
    "tests/test_beta_e2e_acceptance_smoke_runner.py",
    "tests/test_beta_runtime_activation_evidence_gate.py",
    "tests/test_beta_runtime_activation_canary_runner.py",
    "tests/test_beta_runtime_service_activation_approval_packet.py",
    "tests/test_beta_runtime_service_activation_evidence_gate.py",
    "tests/test_beta_runtime_service_activation_live_run_gate.py",
    "tests/test_coolify_devnet_public_demo.py",
    "tests/test_provider_adapter_generated_code_sandbox_beta.py",
    "tests/test_rap_bridge_local_dry_run.py",
    "tests/test_surfpool_validator_lane.py",
    "tests/test_docker_testing_lane.py",
    "tests/test_coolify_staging_lane.py",
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
