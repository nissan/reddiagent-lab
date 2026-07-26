# Microsoft Agent Framework (MAF) Mapping

_Issue #388. Anchor: MAF `kind: Prompt` declarative compatibility (agent-framework 1.12.x)._

## Role

MAF is a compatibility/export target for ReddiAgent ADL. It is not the canonical ReddiAgent schema.

Disambiguation: the target here is MAF's own declarative YAML (`kind: Prompt`, Copilot-Studio schema lineage, PowerFx `=Env.*` interpolation). It is **not** M365 Copilot declarative-agent manifests, **not** AGNTCY OASF, and **not** Open Agent Spec — the last of those is the target of `mappings/AGENT-SPEC.md`.

## Pinned Target

- Package: `agent-framework`, range `>=1.12,<2` (release cadence is ~10 days; one post-GA breaking change already recorded).
- Factory: `ChatClientPromptAgentFactory` — the provider-agnostic path, preferred over the Foundry-coupled `AzureAgentProvider` path.
- Connectors MAF ships: Foundry, AzureOpenAI, OpenAI, Anthropic, Bedrock, Gemini, Ollama. ADL v0.2 provider ids cover OpenAI, Anthropic, Gemini, and Ollama. Connector `kind` values use MAF's own capitalization (`OpenAI`, `Anthropic`, `Gemini`, `Ollama`), not ADL's lowercase provider ids — the mapping table in `scripts/maf_compatibility.py` is the canonical spelling source.

## Mapping Summary

| ADL field | MAF `kind: Prompt` target | Rule |
|---|---|---|
| `metadata.name` | `name` / `displayName` | Direct. |
| `metadata.description` | `description` | Direct. |
| `harness.instructions.inline` | `instructions` | Direct. |
| `harness.instructions.path` | `instructions` | Degraded: MAF instructions are inline; the referenced file is not read during static review. |
| `model.providers.preferred` | `model.connection.kind` | Static metadata; maps when a first-party MAF connector exists. `model.id` has no ADL source and defers to `=Env.*` interpolation. The export uses `=Env.REDDIAGENT_MODEL_ID` and `=Env.REDDIAGENT_MODEL_ENDPOINT`; these names are global — two agents with different providers share the same pair, and per-agent env naming is a consumer decision. |
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
| `harness.runtime` | metadata-only section | No runtime descriptor in `kind: Prompt`; loss code `maf-no-runtime-descriptor`. |
| `harness.deployment` | metadata-only section | No deployment descriptor in `kind: Prompt`; loss code `maf-no-deployment-descriptor`. |
| `harness.recovery` | metadata-only section | No recovery controls in `kind: Prompt`; loss code `maf-no-recovery-controls`. |
| `harness.dataSources` | metadata-only section | No data-source contract (trust, citation, source checks) in `kind: Prompt`; loss code `maf-no-data-source-contract`. |
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

`supported=true` means a static review mapping can be produced. It does not mean runtime execution is safe, and it does not imply ADL v0.2 conformance — conformance is checked separately by `scripts/adl_v02_conformance.py`. `lossless=false` means at least one ReddiAgent section is degraded, metadata-only, or unsupported in MAF.

Extension keys are surfaced by presence, not truthiness: `x402: {}` or `x402: null` still declares the extension and is listed as metadata-only rather than silently vanishing.

`mafPromptYaml` is a best-effort static `kind: Prompt` export emitted only when the core quartet (name, description, inline instructions, mappable model connection) is lossless; otherwise the report carries `mafPromptYamlOmitted` with a reason: `instructions-path-ref-not-inlined`, `no-model-provider-declared` (no model block or no preferred provider), `no-maf-connector-for-preferred-provider` (declared but unmappable), or `structural-errors`. Degraded sections outside the core quartet (policies, eval gates, structured output) do not block the best-effort export — their loss stays recorded in the report.
