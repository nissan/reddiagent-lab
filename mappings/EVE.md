# Vercel eve Static Compatibility Mapping

_Status: report-only target for issue #202. ADL remains canonical._

Vercel eve is treated as a filesystem-first target, not as a replacement for ReddiAgent ADL. This mapping describes a static review projection only. It does not install eve, scaffold a runnable project, start a dev server, resolve MCP servers, call providers, access credentials, access payment rails, deploy, or publish.

## Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `deploymentAllowed=false`

## Mapping

| ReddiAgent ADL | eve slot | Fit | Handling |
|---|---|---:|---|
| `metadata.name` | project root / package metadata | Partial | Used only for static `projectRoot` naming. |
| `metadata.description` | agent metadata | Partial | Preserved in report metadata. |
| `harness.instructions.inline` | `agent/instructions.md` | Strong | Static content plan only. |
| `harness.instructions.path` | `agent/instructions.md` | Strong if bundled | Source path is preserved in report metadata. |
| `model.providers.preferred` | `agent/agent.ts` model metadata | Partial | Reported as model metadata; no provider resolution or API call. |
| `model.providers.fallbacks` | model routing metadata | Partial | Preserved as metadata only. |
| `harness.tools[type=function]` | `agent/tools/<id>.ts` | Strong for manifest | Static stub plan only; no generated executable is written. |
| `harness.tools[type=mcp]` | `agent/connections/<id>.ts` | Partial | Metadata-only connection plan; no MCP server resolution or invocation. |
| `harness.skills` | `agent/skills/<id>/SKILL.md` | Strong | Static package direction; no runtime loading. |
| `harness.dataSources` | connections or metadata | Partial | Preserved as metadata-only unless a later reviewed exporter supports the source type. |
| `harness.memory` | session state metadata | Partial | Preserved as metadata-only; external or persistent stores are not accessed. |
| `harness.policies` | approval/sandbox metadata | Partial | ReddiAgent policy remains authoritative. |
| `harness.evalGates` | `evals/<id>.eval.ts` | Partial | Static eval plan only; no eve eval runner. |
| `harness.runtime.target` | runtime notes | Weak | Non-local runtime targets are unsupported for execution. |
| `extensions.x402` | namespaced metadata | Weak | Payment execution remains unsupported and fail-closed. |
| `extensions.receipts` | namespaced metadata | Weak | Receipt requirements are preserved, not enforced by eve. |
| `extensions.reputation` | namespaced metadata | Weak | Reputation emission is preserved, not executed. |

## Report Contract

`scripts/eve_compatibility.py` emits one report per ADL file with:

- target file manifest for eve-style project slots;
- model and instruction mapping metadata;
- metadata-only ReddiAgent sections;
- unsupported runtime/payment/MCP/reputation features;
- validation failures for invalid ADL inputs;
- static guardrail flags set false.

The checker intentionally returns a non-zero exit code when any input ADL is invalid, matching the repository's fail-closed fixture pattern.
