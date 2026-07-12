# LangGraph Compatibility Report Target

_Issue: #166. Scope: static/report-only LangGraph compatibility._

## What Changed

- `scripts/provider_compatibility.py --target langgraph` now emits `compatibilityMode: langgraph-compatibility-report-only`.
- LangGraph rows include a deterministic `providerMapping` object with model profile, static graph, state schema, node, edge, checkpoint, interrupt, tool-node, MCP-tool-node, metadata-only, and unsupported-execution fields.
- `requiredSecrets` stays empty because the report does not call a hosted LangGraph service, provider, or model.
- Graphs are reported as `not-generated` and edges as `static-plan-only`; the checker never installs LangGraph, compiles a graph, invokes a graph, or starts a runtime.
- Reddi policy, eval, memory, data-source, x402, receipt, reputation, and MCP semantics are preserved as `metadataOnly` where LangGraph compatibility cannot enforce them directly.
- MCP execution remains hard blocked with `unsupportedFeatures: ["mcp_execution"]`.
- x402 real settlement remains hard blocked with `unsupportedFeatures: ["real_settlement"]`.

## Boundary

The target is compatibility-only. It does not:

- install, import, compile, or run LangGraph;
- generate starter graph code;
- call any hosted model provider or local model runtime;
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
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --target langgraph
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
```
