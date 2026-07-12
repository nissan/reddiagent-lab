# Ollama/Local Compatibility-Only Mode Report

_Issue: #165. Scope: static/report-only Ollama/local provider compatibility._

## What Changed

- `scripts/provider_compatibility.py --target ollama` now emits `compatibilityMode: ollama-local-provider-compatibility-only`.
- Ollama rows include a deterministic `providerMapping` object with local model profile metadata, non-probed endpoint/model fields, prompt, tool-call, structured-output, state/memory, metadata-only, and unsupported-execution fields.
- `requiredSecrets` stays empty for Ollama/local compatibility reports.
- Local endpoint and model id are reported as `not-probed` / `metadata-only`; the checker never starts, probes, or calls a local model runtime.
- Tool calling and structured output are marked `custom-harness-required` when the ADL requires them.
- Reddi policy, eval, memory, data-source, x402, receipt, reputation, and MCP semantics are preserved as `metadataOnly` where Ollama/local compatibility cannot enforce them directly.
- MCP execution remains hard blocked with `unsupportedFeatures: ["mcp_execution"]`.
- x402 real settlement remains hard blocked with `unsupportedFeatures: ["real_settlement"]`.

## Boundary

The mode is compatibility-only. It does not:

- start, probe, or call Ollama or any local model runtime;
- call any hosted model provider;
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
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --target ollama
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
```
