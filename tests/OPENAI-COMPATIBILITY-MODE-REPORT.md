# OpenAI Compatibility-Only Mode Report

_Issue: #154. Scope: static/report-only OpenAI adapter compatibility._

## What Changed

- `scripts/provider_compatibility.py --target openai` now emits `compatibilityMode: openai-adapter-compatibility-only`.
- OpenAI rows include a deterministic `providerMapping` object with model profile, instruction, function-tool, metadata-only, and unsupported-execution fields.
- Reddi policy, eval, memory, x402, receipt, reputation, and MCP semantics are preserved as `metadataOnly` when OpenAI compatibility cannot enforce them directly.
- MCP declarations remain hard blocked for execution with `unsupportedFeatures: ["mcp_execution"]`.
- x402 real settlement remains hard blocked with `unsupportedFeatures: ["real_settlement"]`.

## Boundary

The mode is compatibility-only. It does not:

- call OpenAI or any model provider;
- look up, read, or validate credentials;
- activate a runtime;
- resolve or invoke MCP servers;
- touch wallets, facilitators, payment rails, settlement, production gateway config, or live cron definitions;
- make paid/model calls.

Every row keeps:

```json
{
  "runtimeExecutionAllowed": false,
  "networkAccess": false,
  "paymentAccess": false,
  "mcpInvocation": false
}
```

## Validation

Run locally on 2026-07-12 AEST:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_compatibility_cli.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_snapshots.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --target openai
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
```
