# Gemini Compatibility-Only Mode Report

_Issue: #164. Scope: static/report-only Gemini provider compatibility._

## What Changed

- `scripts/provider_compatibility.py --target gemini` now emits `compatibilityMode: gemini-provider-compatibility-only`.
- Gemini rows include a deterministic `providerMapping` object with model profile, system instruction, function declaration, structured-output, metadata-only, and unsupported-execution fields.
- Grounding is reported as `not-configured`, and code execution is explicitly `unsupported`.
- Reddi policy, eval, memory, data-source, x402, receipt, reputation, and MCP semantics are preserved as `metadataOnly` when Gemini compatibility cannot enforce them directly.
- MCP execution remains hard blocked with `unsupportedFeatures: ["mcp_execution"]`.
- x402 real settlement remains hard blocked with `unsupportedFeatures: ["real_settlement"]`.

## Boundary

The mode is compatibility-only. It does not:

- call Gemini or any model provider;
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
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --target gemini
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
```
