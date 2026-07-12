# Loops 629-653 Retrospective: Agent Spec Fail-on-Loss Export

## Scope

Continue the Agent Spec compatibility path after loops 604-628 by adding strict export behavior that refuses to emit if ReddiAgent semantics would be dropped.

## Shipped

- Added `--export-agent-spec` to `scripts/agent_spec_compatibility.py`.
- Added `--output-format json|yaml`.
- Export now emits mapped Agent Spec-compatible review documents only when every input is `lossless=true`.
- Lossy inputs exit `3` with diagnostics and emit no mapped document.
- Added `tests/fixtures/agent-spec-lossless-agent.yaml` to prove the success path.
- Expanded `tests/test_agent_spec_compatibility.py` to cover:
  - report-only compatibility;
  - strict refusal for `simple-agent.yaml` and `payment-agent.yaml`;
  - JSON export for a lossless fixture;
  - YAML export for a lossless fixture.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_agent_spec_compatibility.py
bash tests/smoke-validation.sh
```

Both passed.

Manual refusal check:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/agent_spec_compatibility.py --export-agent-spec examples/simple-agent.yaml examples/payment-agent.yaml
```

Returned exit code `3` and reported metadata-only/unsupported diagnostics.

## Boundary

No Agent Spec runtime execution, adapter installation, external network access, MCP invocation, credential access, or live x402 payment behavior was added.

## Adjustment

The previous Agent Spec next action is complete. The next safe loop should return to the MCP handoff path: define the static MCP runtime handoff package or connect adapter aggregation evidence into readiness traces. MCP servers still must not be resolved or invoked.
