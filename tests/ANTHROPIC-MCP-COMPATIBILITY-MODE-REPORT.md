# Anthropic MCP Compatibility-Only Mode Report

_Issue: #155. Scope: static/report-only Anthropic MCP compatibility._

## What Changed

- `scripts/provider_compatibility.py --target anthropic` now emits `compatibilityMode: anthropic-mcp-compatibility-only`.
- Anthropic rows include a deterministic `providerMapping` object with model profile, system prompt, tool-use schema ids, MCP declaration metadata, metadata-only Reddi semantics, and unsupported-execution fields.
- MCP declarations are preserved as metadata (`id`, `serverRef`, `toolName`) without resolving or invoking servers.
- Reddi policy, eval, memory, data-source, x402, receipt, and reputation semantics are preserved as `metadataOnly` when Anthropic compatibility cannot enforce them directly.
- MCP execution remains hard blocked with `unsupportedFeatures: ["mcp_execution"]`.
- x402 real settlement remains hard blocked with `unsupportedFeatures: ["real_settlement"]`.

## Boundary

The mode is compatibility-only. It does not:

- call Anthropic or any model provider;
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
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --target anthropic
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
```
