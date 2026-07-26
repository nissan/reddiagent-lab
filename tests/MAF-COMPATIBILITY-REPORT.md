# MAF Compatibility Report

_Issue #388. Anchor: Microsoft Agent Framework `kind: Prompt` declarative compatibility._

## Scope

This report documents the first report-only MAF compatibility slice.

The slice adds a static ADL-v0.2-to-MAF mapping check for:

- `examples/v0.2/simple-agent.yaml`
- `examples/v0.2/tool-contract-agent.yaml`
- `examples/v0.2/payment-agent.yaml`
- `examples/v0.2/delegation-research-agent.yaml`

plus `examples/v0.2/path-agent.yaml` (prompt-export omission path), the four `examples/v0.2/runtime-*.yaml` documents (runtime/deployment/recovery metadata-only handling), `examples/invalid/adl-v0.2-string-instructions.yaml` (graceful structural failure), and synthetic malformed shapes (providers as mapping/list, tool entry as bare string) in the guard test.

It does not install `agent-framework`, Foundry services, MCP servers, payment rails, hosted services, or any MAF runtime. The pinned target (`agent-framework>=1.12,<2`, `ChatClientPromptAgentFactory`) is recorded as metadata only.

## Evidence

Command:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/maf_compatibility.py
```

Guard test:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_maf_compatibility.py
```

The compatibility reports are required to include:

- `target: maf`
- `supported`
- `lossless`
- `supportedRequirements`
- `unsupportedRequirements`
- `degradedRequirements`
- `metadataOnlyExtensions`
- `lossMetadata`
- `pinned` (`agent-framework>=1.12,<2`, `ChatClientPromptAgentFactory`)
- `runtimeExecutionAllowed: false`
- `networkAccess: false`
- `paymentAccess: false`
- `mcpInvocation: false`

## Current Findings

`simple-agent.yaml` is statically mappable to a MAF `kind: Prompt` review shape and emits a best-effort `mafPromptYaml` export, but it is not lossless: policies degrade to function-approval middleware (no budget/scope/rate semantics), eval gates degrade to Foundry-external evaluation, `structuredOutput: true` has no ADL schema to fill MAF's `outputSchema` slot (loss code `adl-has-no-output-schema`, tracked as issue #389), and memory and the runtime section stay metadata-only (`maf-no-declarative-memory-contract`, `maf-no-runtime-descriptor`).

`tool-contract-agent.yaml` shows the tool split: function tools map as supported static shapes and the MCP tool maps as supported via MAF's native MCP client (static declaration only, `mcpInvocation` stays false), while http and native tools degrade to code-first function wrappers. Its runtime section is metadata-only.

`payment-agent.yaml` and `delegation-research-agent.yaml` (spend and charge sides of paid delegation) are statically mappable for review, but x402, receipt, and reputation extensions are metadata-only and unsupported for execution — MAF has no x402/AP2 payment surface. Observability degrades to advisory OTel GenAI instrumentation, and their runtime, deployment, and recovery sections stay metadata-only (`maf-no-runtime-descriptor`, `maf-no-deployment-descriptor`, `maf-no-recovery-controls`).

The four `runtime-*.yaml` examples (hosted-container, local-python, platform-native, serverless-platform) all report their runtime, deployment, and recovery sections as metadata-only with the loss codes above and `lossless: false` — MAF `kind: Prompt` has no runtime, deployment, or recovery surface, so none of these settings survive an export. `harness.dataSources` (e.g. `memory-observability-agent.yaml`, `source-boundary-agent.yaml`) is likewise metadata-only (`maf-no-data-source-contract`).

`path-agent.yaml` omits `mafPromptYaml` with reason `instructions-path-ref-not-inlined` because MAF Prompt instructions are inline and the referenced file is not read during static review. A document with no model block (or no preferred provider) omits it with the distinct reason `no-model-provider-declared`; a declared-but-unmappable provider gets `no-maf-connector-for-preferred-provider`.

`examples/invalid/adl-v0.2-string-instructions.yaml` fails gracefully: the CLI exits `1` with a `supported: false` report listing structural errors, empty requirement buckets, and all boundary flags still false. Malformed shapes (providers as a list, `preferred` as a mapping, a tool entry as a bare string) produce the same graceful `supported: false` reports instead of tracebacks, and any unforeseen mapping failure is caught defensively and reported as a `mapping-failure:` structural error.

Default-run output is deterministic (two runs produce byte-identical reports).

## Boundary

This is Level 2 compatibility evidence only. It does not approve:

- MAF or Foundry runtime execution;
- external network access;
- MCP server resolution or invocation;
- credential access;
- live x402 payment;
- filesystem mutation outside the report/check path;
- provider adapter code generation.

The next safe MAF loop can harden the prompt export (e.g. a first-class `model.outputSchema` once issue #389 lands) without installing or invoking any MAF runtime.
