#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_compatibility_cli.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_validation_guidance.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_tool_execution.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_cli_usage_matrix.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_adapter_readiness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_contract.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_error_semantics.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_aggregation.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_source_check.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_server_resolution.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_capability_policy.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_readiness_evidence.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_readiness_release.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_runtime_handoff_package.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_agent_spec_compatibility.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_a2a_agent_card_export.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_agent_skill_export.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_rap_bridge_report.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_ap2_x402_mandate_report.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_prosumer_builder_plan.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_local_runner_plugin_interface.py
