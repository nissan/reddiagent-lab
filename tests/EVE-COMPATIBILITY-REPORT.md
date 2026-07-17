# Vercel eve Compatibility Report

_Issue: #202_

This report is generated from the deterministic checker in `scripts/eve_compatibility.py` and the pinned fixture at `tests/fixtures/eve-compatibility-report.json`.

## Coverage

- `examples/simple-agent.yaml`
- `examples/tool-agent.yaml`
- `examples/mcp-readonly-agent.yaml`
- `examples/payment-agent.yaml`
- `examples/invalid/missing-instructions.yaml`

## Static Boundary

- Runtime execution: blocked
- Network access: blocked
- Payment access: blocked
- MCP invocation: blocked
- Deployment: blocked

## Findings

- Simple and tool examples map to eve-style `agent/instructions.md`, `agent/agent.ts`, `agent/tools/*.ts`, and `evals/*.eval.ts` manifest slots.
- MCP declarations map only to metadata-only `agent/connections/*.ts` slots; no MCP server is resolved or invoked.
- x402, receipts, reputation, non-local runtime targets, policies, memory, and eval gates remain ReddiAgent-owned semantics and are preserved as metadata-only or unsupported runtime features.
- Invalid ADL fails closed with validation diagnostics.

No eve install/run, runnable project generation, dev server, provider/model call, MCP invocation/resolution, credential access, payment/wallet/facilitator/settlement access, deployment, publishing, or paid/model call is performed.
