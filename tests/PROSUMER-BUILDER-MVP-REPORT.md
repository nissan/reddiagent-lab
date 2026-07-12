# Prosumer Builder MVP Skeleton Report

Generated for issue #136.

## Scope

- Static CLI skeleton: `scripts/prosumer_builder_plan.py`
- Inputs: `examples/simple-agent.yaml`, `examples/tool-agent.yaml`, `examples/payment-agent.yaml`
- Flow covered: choose job, model profile, optional tool, policy/eval gate, validate, dry-run, trace, export
- Export targets listed: Agent Spec, A2A Agent Card, Agent Skills / `SKILL.md`

## Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

The skeleton does not call model providers, live runtimes, MCP servers, wallets, facilitators, payment rails, or external services. It reads local ADL files, runs local schema validation, previews deterministic trace shape, and points to existing report-only export commands.

## Evidence

- `tests/test_prosumer_builder_plan.py` verifies the three MVP examples and one invalid fixture.
- Payment/x402 ADL is preserved as metadata-only/unsupported for execution.
- Tool fixtures remain deterministic local fixture commands only.
