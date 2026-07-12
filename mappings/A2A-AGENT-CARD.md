# A2A Agent Card Mapping

_Issue #132. Static export target: A2A Agent Card v1.0._

## Role

A2A Agent Card is a compatibility/export target for ReddiAgent ADL. ADL remains the canonical source of truth.

The A2A v1.0 specification defines an Agent Card as a discovery manifest containing agent identity, supported interfaces, capabilities, skills, communication modes, and security requirements. ReddiAgent exports this only as a static review artifact until a separate runtime adapter is approved.

## Mapping Summary

| ADL field | A2A Agent Card field | Rule |
|---|---|---|
| `metadata.name` | `name` | Direct. |
| `metadata.description` | `description` | Direct, empty string if absent. |
| `extensions.a2a.supportedInterfaces` | `supportedInterfaces` | Direct when present; otherwise static `example.invalid` placeholder for report-only review. |
| `extensions.a2a.capabilities` | `capabilities` | Direct booleans/extensions when present; default all runtime capabilities false. |
| `model.requirements.structuredOutput` | `defaultOutputModes` | Adds `application/json` when structured output is required. |
| `harness.tools` | `skills` | Static descriptive skill entries only. No invocation. |
| `extensions.a2a.securitySchemes` | `securitySchemes` | Direct metadata when present. |
| `extensions.a2a.securityRequirements` | `securityRequirements` | Direct metadata when present. |
| `harness.instructions` | metadata-only section | Not an A2A execution guarantee. |
| `harness.policies` | metadata-only section | Must remain enforced by ReddiAgent until target enforcement exists. |
| `harness.evalGates` | metadata-only section | Must remain enforced by ReddiAgent until target evaluation exists. |
| `harness.memory` | metadata-only section | No external memory backend is called. |
| `extensions.x402` | metadata-only Reddi extension | No payment execution. |
| `extensions.receipts` | metadata-only Reddi extension | No receipt mutation. |
| `extensions.reputation` | metadata-only Reddi extension | No reputation mutation. |

## Report Contract

The report contract is implemented by `scripts/adl_to_a2a_agent_card.py` and guarded by `tests/test_a2a_agent_card_export.py`.

Every report and embedded Agent Card metadata block must keep these runtime boundaries false:

- `runtimeExecutionAllowed`
- `networkAccess`
- `paymentAccess`
- `mcpInvocation`

`supported=true` means a static Agent Card review mapping can be produced. It does not mean runtime execution is safe. `lossless=false` means at least one ReddiAgent section is metadata-only or unsupported by the static target.

Strict `--export-agent-card` mode refuses lossy ADL with exit code 3 plus diagnostics. This prevents silently dropping Reddi payment, receipt, reputation, source-boundary, MCP, policy, memory, or evaluation semantics.
