# Agent Spec Mapping

_Loops 604-628. Anchor: Open Agent Specification compatibility._

## Role

Agent Spec is a compatibility/export target for ReddiAgent ADL. It is not the canonical ReddiAgent schema.

## Mapping Summary

| ADL field | Agent Spec-compatible review field | Rule |
|---|---|---|
| `metadata.name` | component name | Direct. |
| `metadata.description` | component description | Direct. |
| `model.providers` | model provider preferences | Static metadata unless a runtime adapter is reviewed. |
| `model.requirements` | model requirements | Direct where possible. |
| `harness.instructions` | instructions | Inline/path references only. |
| `harness.tools` | tool definitions | Static shape only. No invocation. |
| `harness.policies` | metadata-only section | Must remain enforced by ReddiAgent until target enforcement exists. |
| `harness.evalGates` | metadata-only section | Must remain enforced by ReddiAgent until target evaluation exists. |
| `harness.memory` | metadata-only section | No external memory backend is called. |
| `extensions.x402` | metadata-only Reddi extension | No payment execution. |
| `extensions.receipts` | metadata-only Reddi extension | No receipt mutation. |
| `extensions.reputation` | metadata-only Reddi extension | No reputation mutation. |

## Report Contract

The report contract is implemented by `scripts/agent_spec_compatibility.py` and guarded by `tests/test_agent_spec_compatibility.py`.

Every report must keep these runtime boundaries false:

- `runtimeExecutionAllowed`
- `networkAccess`
- `paymentAccess`
- `mcpInvocation`

`supported=true` means a static review mapping can be produced. It does not mean runtime execution is safe. `lossless=false` means at least one ReddiAgent section is metadata-only or unsupported by the static target.
