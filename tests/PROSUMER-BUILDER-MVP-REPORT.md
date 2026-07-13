# Prosumer Builder MVP Skeleton Report

Generated for issue #136 and refreshed for issues #144 and #188.

## Scope

- Static CLI skeleton: `scripts/prosumer_builder_plan.py`
- Inputs: `examples/simple-agent.yaml`, `examples/tool-agent.yaml`, `examples/payment-agent.yaml`
- Flow covered: choose job, model profile, optional tool, policy/eval gate, validate, dry-run, trace, export
- Export targets listed: Agent Spec, A2A Agent Card, Agent Skills / `SKILL.md`, starter manifest, provider compatibility, and RAP bridge
- Static UI export matrix covers readiness states:
  - `report-ready`
  - `metadata-only`
  - `blocked-before-generation`
  - `blocked-by-validation`
  - `not-applicable`
- Tool-example dry-run preview now mirrors current local trace shape:
  - `tool.executed`
  - `source.checked`
  - `task.dry_run_completed` with required-gate completion reason
- Tool-example preview includes local fixture execution summary and approved-source gate summary.

## Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

The skeleton does not call model providers, live runtimes, MCP servers, wallets, facilitators, payment rails, or external services. It reads local ADL files, runs local schema validation, previews deterministic trace shape, and points to existing report-only export commands plus their authoritative local test files.

## Evidence

- `tests/test_prosumer_builder_plan.py` verifies the three MVP examples and one invalid fixture.
- Payment/x402 ADL is preserved as metadata-only/unsupported for execution.
- Tool fixtures remain deterministic local fixture commands only.
- `examples/tool-agent.yaml` uses `--execute-tools --fail-on-required-gate` and previews `networkAccess=false` / `paymentAccess=false`.
- Invalid ADL examples keep dry-run and trace steps blocked.
- `staticUiExportMatrix` pins six report-only/export targets with command, strict export command where applicable, authoritative check, blockers, metadata-only sections, and boundary flags.
