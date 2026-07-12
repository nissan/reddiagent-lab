# A2A Agent Card Export Report

_Issue #132. Generated evidence target: `scripts/adl_to_a2a_agent_card.py`._

## Static Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

This report is static and report-only. It does not activate an A2A runtime, resolve an A2A endpoint, invoke MCP, touch wallets, contact facilitators, execute payment rails, settle funds, or call external services.

## Source Target

The A2A v1.0 Agent Card is treated as a discovery/export target for ReddiAgent ADL. ADL remains canonical.

The checker maps:

- ADL identity to Agent Card `name` and `description`.
- Static report interfaces to `supportedInterfaces`.
- ADL model output requirements to `defaultOutputModes`.
- ADL tools to descriptive Agent Card `skills`.
- Optional `extensions.a2a.securitySchemes` and `extensions.a2a.securityRequirements` to Agent Card security metadata.
- Reddi-only semantics to Agent Card metadata with strict export refusal when those semantics would be lossy.

## Fixture Summary

| Fixture | Outcome | Evidence |
|---|---|---|
| `examples/simple-agent.yaml` | `supported=true`, `lossless=false` | Policies, eval gates, memory, and instructions are metadata-only. |
| `examples/payment-agent.yaml` | `supported=true`, `lossless=false` | x402, receipts, reputation, hosted runtime, policies, eval gates, instructions, and tools are metadata-only/unsupported for strict export. |
| `tests/fixtures/a2a-agent-card-lossless-agent.yaml` | strict export passes | Emits one static Agent Card with no metadata-only sections. |
| `tests/fixtures/a2a-agent-card-lossy-agent.yaml` | strict export exits `3` | Refuses to drop payment, receipt, reputation, policy, tool, eval, and hosted-runtime semantics. |

## Validation Evidence

Focused validation:

```text
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_a2a_agent_card_export.py
PASS A2A Agent Card export
```

Strict loss refusal:

```text
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/adl_to_a2a_agent_card.py --export-agent-card tests/fixtures/a2a-agent-card-lossy-agent.yaml
exit code: 3
error: a2a_agent_card_export_would_drop_reddi_semantics
```

Strict lossless export:

```text
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/adl_to_a2a_agent_card.py --export-agent-card --single tests/fixtures/a2a-agent-card-lossless-agent.yaml
exit code: 0
Agent Card: lossless-a2a-card-agent
```

Smoke validation includes `tests/test_a2a_agent_card_export.py`.
