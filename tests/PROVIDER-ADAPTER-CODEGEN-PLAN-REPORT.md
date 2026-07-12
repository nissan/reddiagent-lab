# Provider Adapter Codegen Plan Report

_Issue: #177 and #186. Scope: static/report-only provider adapter codegen planning and manifest fixtures._

## Summary

- Added `scripts/provider_adapter_codegen_plan.py`, a deterministic planner that consumes existing provider compatibility reports and summarizes future adapter file shapes.
- The plan covers OpenAI, Anthropic MCP, Gemini, Ollama/local, and LangGraph targets without generating runnable adapter code.
- Each target records planned review files, target-specific blockers, required secrets or hosted services as metadata, unsupported semantics, and validation gates.
- Issue #186 adds `adapterManifestFixture` output plus `tests/fixtures/provider-adapter-codegen-manifest.json`, pinning manifest ids, planned file purposes/formats, support metadata, blocker ids, and validation gate ids for each provider target.
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

## Manifest Fixture Coverage

`tests/fixtures/provider-adapter-codegen-manifest.json` pins:

- `schemaVersion=provider-adapter-codegen-manifest-fixture.v0.1`
- `fixtureStatus=blocked-report-only`
- the same disabled boundary as the planner output
- four manifest validation gates:
  - `manifest-fixture-deterministic`
  - `manifest-files-report-only`
  - `manifest-target-support-metadata`
  - `manifest-runtime-boundary-disabled`
- five target manifests: OpenAI, Anthropic MCP, Gemini, Ollama/local, and LangGraph

Every planned file entry is `plannedOnly=true`, `generatedByThisPlan=false`, and
`validationStatus=not-generated`.

## Validation

Run locally on 2026-07-13 AEST:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_adapter_codegen_plan.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_adapter_codegen_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml examples/mcp-readonly-agent.yaml --output tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_adapter_codegen_plan.py tests/test_provider_adapter_codegen_plan.py
```

The manifest fixture was generated from the deterministic JSON output and is checked back against
the planner by `tests/test_provider_adapter_codegen_plan.py`.

## Non-Goals

- No runnable provider adapter generation.
- No provider SDK install/import/call.
- No local model endpoint probe.
- No MCP server resolution or invocation.
- No credential lookup, wallet/facilitator/payment rail/settlement, deployment, production gateway mutation, or paid/model call.
