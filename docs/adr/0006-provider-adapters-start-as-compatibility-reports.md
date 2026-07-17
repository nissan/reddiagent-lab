# ADR 0006: Provider Adapters Start as Compatibility Reports

## Status

Accepted.

## Context

Provider and framework adapters can encourage builders to treat one target as the real product. ReddiAgent instead needs a way to compare targets while preserving ADL semantics and guardrails. Existing provider compatibility work already covers OpenAI, Anthropic, Gemini, Ollama/local, LangGraph, LlamaIndex, Strands, MCP, and related targets as deterministic reports.

Relevant references:

- `specs/PROVIDER-COMPATIBILITY-REPORT-v0.1.md`
- `specs/PROVIDER-MAPPING-v0.1.md`
- `mappings/OPENAI.md`
- `mappings/ANTHROPIC.md`
- `mappings/GEMINI.md`
- `mappings/LANGGRAPH.md`
- `mappings/LLAMAINDEX.md`
- `mappings/STRANDS.md`
- `tests/PROVIDER-COMPATIBILITY-REPORT.md`
- `tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md`

## Decision

Provider and framework adapters start as deterministic compatibility reports.

They may describe supported capabilities, gaps, warnings, lossless export readiness, unsupported runtime features, and implementation guidance. They should not call provider APIs or generate live adapter code as their first step.

## Consequences

- New adapter work should add fixtures, mappings, reports, and tests before runtime code.
- Provider-specific code generation should remain preview/report-only until guardrails prove what can be generated safely.
- Compatibility reports must keep ReddiAgent policy, memory, eval, source-boundary, MCP, payment, receipt, and reputation semantics visible even when a target lacks native support.
- Builders can compare targets before committing to a provider or framework.
