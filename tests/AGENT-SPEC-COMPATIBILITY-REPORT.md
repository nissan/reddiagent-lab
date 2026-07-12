# Agent Spec Compatibility Report

_Loops 604-653. Anchor: Open Agent Specification compatibility._

## Scope

This report documents the first report-only Agent Spec compatibility slice.

The slice adds a static ADL-to-Agent-Spec mapping check for:

- `examples/simple-agent.yaml`
- `examples/payment-agent.yaml`

It does not install PyAgentSpec, WayFlow, LangGraph adapters, AutoGen adapters, CrewAI adapters, MCP servers, payment rails, hosted services, or any Agent Spec runtime.

## Evidence

Command:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/agent_spec_compatibility.py examples/simple-agent.yaml examples/payment-agent.yaml
```

Guard test:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_agent_spec_compatibility.py
```

Strict export refusal check:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/agent_spec_compatibility.py --export-agent-spec examples/simple-agent.yaml examples/payment-agent.yaml
```

The strict export command exits `3` and emits diagnostics to stderr when any input is not lossless. It does not emit an Agent Spec mapped document for lossy ADL.

The compatibility reports are required to include:

- `target: agent-spec`
- `supported`
- `lossless`
- `metadataOnlyExtensions`
- `unsupportedFeatures`
- `runtimeExecutionAllowed: false`
- `networkAccess: false`
- `paymentAccess: false`
- `mcpInvocation: false`

## Current Findings

`simple-agent.yaml` is statically mappable to an Agent Spec-compatible review document, but it is not lossless because ReddiAgent harness policy, eval gate, and memory semantics remain metadata-only until a target runtime can enforce them.

`payment-agent.yaml` is statically mappable for review, but it is not lossless. The x402, receipt, and reputation extensions are preserved as metadata, and live payment execution plus hosted runtime execution remain unsupported.

`tests/fixtures/agent-spec-lossless-agent.yaml` proves the strict exporter can emit a mapped review document when no ReddiAgent semantics are metadata-only or unsupported. JSON and YAML export paths are covered by `tests/test_agent_spec_compatibility.py`.

## Boundary

This is Level 2 compatibility evidence only. It does not approve:

- Agent Spec runtime execution;
- external network access;
- MCP server resolution or invocation;
- credential access;
- live x402 payment;
- filesystem mutation outside the report/check path;
- provider adapter code generation.

The strict fail-on-loss export fixture is now implemented. The next safe loop can return to the MCP handoff path: define the static MCP runtime handoff package or connect adapter aggregation evidence into readiness traces, without resolving or invoking MCP servers.
