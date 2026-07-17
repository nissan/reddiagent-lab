#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" scripts/validate_examples.py
"$PYTHON" tests/test_provider_compatibility_cli.py
"$PYTHON" tests/test_provider_adapter_codegen_plan.py
"$PYTHON" tests/test_validation_guidance.py
"$PYTHON" tests/test_tool_execution.py
"$PYTHON" tests/test_cli_usage_matrix.py
"$PYTHON" tests/test_readiness_bundle.py
"$PYTHON" tests/test_adapter_readiness.py
"$PYTHON" tests/test_mcp_adapter_contract.py
"$PYTHON" tests/test_mcp_adapter_error_semantics.py
"$PYTHON" tests/test_mcp_adapter_aggregation.py
"$PYTHON" tests/test_mcp_adapter_source_check.py
"$PYTHON" tests/test_mcp_server_resolution.py
"$PYTHON" tests/test_mcp_capability_policy.py
"$PYTHON" tests/test_mcp_readiness_evidence.py
"$PYTHON" tests/test_mcp_readiness_release.py
"$PYTHON" tests/test_mcp_runtime_handoff_package.py
"$PYTHON" tests/test_agent_spec_compatibility.py
"$PYTHON" tests/test_a2a_agent_card_export.py
"$PYTHON" tests/test_agent_skill_export.py
"$PYTHON" tests/test_rap_bridge_report.py
"$PYTHON" tests/test_rap_provider_handoff_summaries.py
"$PYTHON" tests/test_eve_compatibility.py
"$PYTHON" tests/test_ap2_x402_mandate_report.py
"$PYTHON" tests/test_prosumer_builder_plan.py
"$PYTHON" tests/test_static_export_target_parity.py
"$PYTHON" tests/test_protected_docs_package.py
"$PYTHON" tests/test_public_blog_draft.py
"$PYTHON" tests/test_open_spec_review_intake.py
"$PYTHON" tests/test_prosumer_builder_static_export.py
"$PYTHON" tests/test_starter_code_plan.py
"$PYTHON" tests/test_local_runner_plugin_interface.py
"$PYTHON" tests/test_local_runtime_prototype.py
"$PYTHON" tests/test_provider_sandbox_prototype.py
"$PYTHON" tests/test_payment_dry_run_receipt.py
"$PYTHON" tests/test_adl_validation_ui.py
