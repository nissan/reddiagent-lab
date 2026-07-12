# Provider Adapter Codegen Plan Report

_Issue: #177. Scope: static/report-only provider adapter codegen planning._

## Summary

- Added `scripts/provider_adapter_codegen_plan.py`, a deterministic planner that consumes existing provider compatibility reports and summarizes future adapter file shapes.
- The plan covers OpenAI, Anthropic MCP, Gemini, Ollama/local, and LangGraph targets without generating runnable adapter code.
- Each target records planned review files, target-specific blockers, required secrets or hosted services as metadata, unsupported semantics, and validation gates.
- Codegen remains explicitly blocked until a future reviewed runtime adapter contract exists for each target.

## Static Boundary

Every plan preserves:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `writesFiles=false`
- `installsDependencies=false`
- `generatesRunnableCode=false`

## Target Coverage

| Target | Compatibility mode | Codegen status |
|---|---|---|
| OpenAI | `openai-adapter-compatibility-only` | `blocked-report-only` |
| Anthropic MCP | `anthropic-mcp-compatibility-only` | `blocked-report-only` |
| Gemini | `gemini-provider-compatibility-only` | `blocked-report-only` |
| Ollama/local | `ollama-local-provider-compatibility-only` | `blocked-report-only` |
| LangGraph | `langgraph-compatibility-report-only` | `blocked-report-only` |

## Validation

Run locally on 2026-07-13 AEST:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_adapter_codegen_plan.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_adapter_codegen_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --output tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md
```

The second command was used to confirm deterministic JSON output before this Markdown summary was written.

## Non-Goals

- No runnable provider adapter generation.
- No provider SDK install/import/call.
- No local model endpoint probe.
- No MCP server resolution or invocation.
- No credential lookup, wallet/facilitator/payment rail/settlement, deployment, production gateway mutation, or paid/model call.
