# Microsoft Agent Framework (MAF) Mapping

_Issue #388. Anchor: MAF `kind: Prompt` declarative compatibility (agent-framework 1.12.x)._

## Role

MAF is a compatibility/export target for ReddiAgent ADL. It is not the canonical ReddiAgent schema.

Disambiguation: the target here is MAF's own declarative YAML (`kind: Prompt`, Copilot-Studio schema lineage, PowerFx `=Env.*` interpolation). It is **not** M365 Copilot declarative-agent manifests, **not** AGNTCY OASF, and **not** Open Agent Spec — the last of those is the target of `mappings/AGENT-SPEC.md`.

## Pinned Target

- Package: `agent-framework`, range `>=1.12,<2` (release cadence is ~10 days; one post-GA breaking change already recorded).
- Factory: `ChatClientPromptAgentFactory` — the provider-agnostic path, preferred over the Foundry-coupled `AzureAgentProvider` path.
- Connectors MAF ships: Foundry, AzureOpenAI, OpenAI, Anthropic, Bedrock, Gemini, Ollama. ADL v0.2 provider ids cover OpenAI, Anthropic, Gemini, and Ollama.

## Mapping Summary

| ADL field | MAF `kind: Prompt` target | Rule |
|---|---|---|
| `metadata.name` | `name` / `displayName` | Direct. |
| `metadata.description` | `description` | Direct. |
| `harness.instructions.inline` | `instructions` | Direct. |
| `harness.instructions.path` | `instructions` | Degraded: MAF instructions are inline; the referenced file is not read during static review. |
| `model.providers.preferred` | `model.connection.kind` | Static metadata; maps when a first-party MAF connector exists. `model.id` has no ADL source and defers to `=Env.*` interpolation. |
| `model.providers.fallbacks` | — | Degraded: `kind: Prompt` declares one model connection. |
| `model.capability` / `model.requirements` | model selection metadata | Static metadata only. |
| `model.requirements.structuredOutput` | `outputSchema` | Degraded: the slot exists in MAF, but ADL v0.2 only carries a boolean, so no schema can be exported (issue #389). |
| `harness.tools` (function) | function tool | Supported static shape only. No invocation. |
| `harness.tools` (mcp) | MCP tool | Supported statically; MAF has a native MCP client. No server is resolved or invoked. |
| `harness.tools` (http/native) | — | Degraded: no declarative equivalent; would need a code-first function wrapper. |
| `harness.policies` | function-approval middleware | Degraded: approval middleware gates calls but has no budget, scope, or rate semantics. Must remain enforced by ReddiAgent. |
| `harness.evalGates` | Foundry evaluation | Degraded: external and Azure-coupled; not completion contracts inside MAF. |
| `harness.observability` | OTel GenAI instrumentation | Degraded: advisory only; required-event/redaction/retention contracts are not enforced. |
| `harness.memory` | metadata-only section | No declarative memory contract in `kind: Prompt`. |
| `extensions.x402` | metadata-only Reddi extension | Unsupported for execution: MAF has no x402/AP2 payment surface. |
| `extensions.receipts` | metadata-only Reddi extension | Unsupported for execution: no receipt surface. |
| `extensions.reputation` | metadata-only Reddi extension | Unsupported for execution: no reputation surface. |

## Report Contract

The report contract is implemented by `scripts/maf_compatibility.py` and guarded by `tests/test_maf_compatibility.py`.

Every report carries `target: maf`, `supported`, `lossless`, the requirement buckets (`supportedRequirements`, `unsupportedRequirements`, `degradedRequirements`, `metadataOnlyExtensions`, `lossMetadata`), the `pinned` block above, and keeps these runtime boundaries false:

- `runtimeExecutionAllowed`
- `networkAccess`
- `paymentAccess`
- `mcpInvocation`

`supported=true` means a static review mapping can be produced. It does not mean runtime execution is safe. `lossless=false` means at least one ReddiAgent section is degraded, metadata-only, or unsupported in MAF.

`mafPromptYaml` is a best-effort static `kind: Prompt` export emitted only when the core quartet (name, description, inline instructions, mappable model connection) is lossless; otherwise the report carries `mafPromptYamlOmitted` with a reason. Degraded sections outside the core quartet (policies, eval gates, structured output) do not block the best-effort export — their loss stays recorded in the report.
