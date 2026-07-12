# Agent Spec Compatibility v0.1

_Added: 2026-05-31. Anchor: Open Agent Specification comparison._

## Purpose

Open Agent Specification / Agent Spec is a portability target for ReddiAgent, not the canonical source of truth.

ReddiAgent ADL remains the product-owned definition format because it carries Reddi-specific harness policy, source-boundary checks, payment intents, receipts, reputation, and fail-closed readiness evidence. Agent Spec compatibility should let builders exchange ordinary agent and flow definitions with the broader ecosystem without weakening those ReddiAgent guarantees.

## Positioning

Agent Spec answers:

- how to describe agents and structured flows so compatible runtimes can execute them;
- how to serialize those definitions as JSON/YAML;
- how to run them through framework adapters.

ReddiAgent adds:

- policy-before-execution readiness gates;
- deterministic local fixture evidence;
- MCP static review and fail-closed handoff contracts;
- x402/payment dry-run receipts and later settlement adapters;
- source checks, trace completion semantics, reputation signals, and builder-facing repair guidance.

## Compatibility Strategy

Treat Agent Spec as a Level 2 provider/runtime compatibility target.

The first integration is report-only:

1. Map ADL concepts to Agent Spec concepts.
2. Produce an Agent Spec compatibility report for current examples.
3. Emit static JSON/YAML only after report warnings are explicit.
4. Validate that Reddi-only extensions survive as namespaced metadata.
5. Do not execute Agent Spec runtimes, install runtime adapters, or call external tools.

## Initial Mapping

| ReddiAgent ADL | Agent Spec target | Notes |
|---|---|---|
| `metadata.name` / `metadata.description` | Agent identity fields | Direct mapping. |
| `model.providers` / `model.requirements` | LLM/model config | Provider-specific values may be partial or warning-only. |
| `harness.instructions` | Agent system prompt / instruction source | Preserve file reference when possible. |
| `harness.tools` / `harness.functions` | Tool definitions | Static schemas only; no live invocation. |
| `harness.skills` | Component metadata or extension metadata | Agent Spec has no guaranteed equivalent for every Reddi skill package. |
| `harness.policies` | Guardrails or metadata | Must remain fail-closed in ReddiAgent if target cannot enforce them. |
| `harness.evalGates` | Evaluation metadata | Agent Spec evaluation support may be partial. |
| `harness.runtime` | Runtime adapter target | Compatibility-only until a reviewed runtime exists. |
| `extensions.x402` | Namespaced Reddi extension metadata | Must not become live payment behavior. |
| `extensions.receipts` | Namespaced Reddi extension metadata | Preserve shape for ReddiAgent validators. |
| `extensions.reputation` | Namespaced Reddi extension metadata | Preserve as metadata; no reputation mutation. |

## Compatibility Report Requirements

An Agent Spec compatibility report must include:

- `target: agent-spec`
- `supported: true|false`
- `lossless: true|false`
- `warnings`
- `unsupportedFeatures`
- `redactedOrMetadataOnlyExtensions`
- `requiredRuntimeAdapters`
- `runtimeExecutionAllowed: false`
- `networkAccess: false`
- `paymentAccess: false`
- `mcpInvocation: false`

Any policy, payment, source-boundary, or MCP feature that Agent Spec cannot enforce must be reported as either unsupported or metadata-only. Metadata-only export is allowed for review, but it must not be treated as execution approval.

## Strict Export Slice

Static Agent Spec export is allowed only through an explicit strict mode. The exporter must refuse to emit when any input has `lossless=false`.

Refusal requirements:

- return a non-zero exit code;
- emit diagnostics that name the agent, source, metadata-only sections, unsupported features, and warnings;
- preserve `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`;
- emit no mapped Agent Spec document.

Allowed export requirements:

- every input has `lossless=true`;
- output is static JSON/YAML only;
- output is still a review document, not runtime approval;
- no Agent Spec runtime dependency is installed or invoked.

## Next Implementation Slice

The strict fail-on-loss export mode is implemented. The next safe development loop should resume the MCP handoff path:

- define the static MCP runtime handoff package, or
- connect adapter aggregation evidence into readiness traces.

Do not install PyAgentSpec, WayFlow, LangGraph adapters, AutoGen adapters, CrewAI adapters, or any Agent Spec runtime dependency in this slice.
