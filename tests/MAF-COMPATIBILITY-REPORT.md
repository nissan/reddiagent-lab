# MAF Compatibility Report

_Issue #388. Anchor: Microsoft Agent Framework `kind: Prompt` declarative compatibility._

## Scope

This report documents the first report-only MAF compatibility slice.

The slice adds a static ADL-v0.2-to-MAF mapping check for:

- `examples/v0.2/simple-agent.yaml`
- `examples/v0.2/tool-contract-agent.yaml`
- `examples/v0.2/payment-agent.yaml`
- `examples/v0.2/delegation-research-agent.yaml`

plus `examples/v0.2/path-agent.yaml` (prompt-export omission path) and `examples/invalid/adl-v0.2-string-instructions.yaml` (graceful structural failure) in the guard test.

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

`simple-agent.yaml` is statically mappable to a MAF `kind: Prompt` review shape and emits a best-effort `mafPromptYaml` export, but it is not lossless: policies degrade to function-approval middleware (no budget/scope/rate semantics), eval gates degrade to Foundry-external evaluation, `structuredOutput: true` has no ADL schema to fill MAF's `outputSchema` slot (loss code `adl-has-no-output-schema`, tracked as issue #389), and memory stays metadata-only.

`tool-contract-agent.yaml` shows the tool split: function tools map as supported static shapes and the MCP tool maps as supported via MAF's native MCP client (static declaration only, `mcpInvocation` stays false), while http and native tools degrade to code-first function wrappers.

`payment-agent.yaml` and `delegation-research-agent.yaml` (spend and charge sides of paid delegation) are statically mappable for review, but x402, receipt, and reputation extensions are metadata-only and unsupported for execution — MAF has no x402/AP2 payment surface. Observability degrades to advisory OTel GenAI instrumentation.

`path-agent.yaml` omits `mafPromptYaml` with reason `instructions-path-ref-not-inlined` because MAF Prompt instructions are inline and the referenced file is not read during static review.

`examples/invalid/adl-v0.2-string-instructions.yaml` fails gracefully: the CLI exits `1` with a `supported: false` report listing structural errors, empty requirement buckets, and all boundary flags still false.

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
