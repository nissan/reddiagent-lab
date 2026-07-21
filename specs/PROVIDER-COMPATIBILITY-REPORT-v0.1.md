# Provider Compatibility Report v0.1

_Loop 28. Anchor issue: #30._

## Purpose

Before compiling an ADL file to a provider or runtime, produce a compatibility report.

## Report Shape

    target: openai-agents
    supported: true
    level: 2
    warnings: []
    unsupportedFeatures: []
    providerResolution:
      requestedTarget: openai
      orderedCandidates:
        - openai
      selectedProvider: openai
      selectedRole: preferred
      hostedProvider: true
    modelCapabilityRequirements:
      vocabularyVersion: adl-v0.2-model-requirements
      requested: {}
      supportedRequirements: []
      unsupportedRequirements: []
      degradedRequirements: []
      lossMetadata: []
    requiredSecrets:
      - OPENAI_API_KEY
    requiredHostedServices: []
    suggestedFallback: local-python

## Compatibility Levels

- Level 0: schema-valid.
- Level 1: local dry-run compatible.
- Level 2: provider adapter compatible.
- Level 3: payment/reputation dry-run compatible.
- Level 4: deployable with production safeguards.

## Required Checks

- provider identifiers use the ADL v0.2 canonical vocabulary.
- preferred/fallback provider resolution is reported deterministically.
- model requirements are split into supported, unsupported, degraded, and loss metadata.
- tool types supported.
- runtime target supported.
- secrets referenced, not embedded.
- payment extension enforceable or disabled.
- observability minimum available.

## CLI Selection

The report CLI is deterministic and report-only. It may filter by ADL path, `metadata.name`,
and target, but those selectors must not instantiate adapters or call providers.

Supported target selectors:

- `openai`
- `anthropic`
- `gemini`
- `ollama`
- `langgraph`
- `mcp-readonly`
- `local-python`

Output modes:

- `json`: stable snapshot/export format.
- `summary`: human-readable review summary.

`--output` writes the selected report to a local file. It is an export of the static report only,
not provider code generation or runtime activation.

## OpenAI Compatibility-Only Mode

The `openai` target emits `compatibilityMode: openai-adapter-compatibility-only`.
This is a static review artifact, not an OpenAI adapter invocation.

The OpenAI row includes:

- model profile mapping from `model.capability`, `model.providers`, and `model.requirements`;
- instruction mapping from `harness.instructions.inline`;
- function-tool declaration ids from non-MCP `harness.tools`;
- `metadataOnly` fields for Reddi policy, eval, memory, x402, receipt, reputation, and MCP semantics that a reviewed runtime adapter must enforce before execution;
- `unsupportedExecution` for MCP tool declarations because this report does not resolve or invoke MCP servers.

OpenAI rows may be `supported: true` only for static compatibility when no hard unsupported feature
is present. Real settlement and MCP execution remain hard unsupported features. Every OpenAI row
continues to report `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`,
and `mcpInvocation=false`.

## Anthropic MCP Compatibility-Only Mode

The `anthropic` target emits `compatibilityMode: anthropic-mcp-compatibility-only`.
This is a static review artifact, not an Anthropic API call or MCP client invocation.

The Anthropic row includes:

- model profile mapping from `model.capability`, `model.providers`, and `model.requirements`;
- system prompt mapping from `harness.instructions.inline`;
- Claude-style tool-use schema ids from non-MCP `harness.tools`;
- MCP declaration metadata from MCP tools, limited to `id`, `serverRef`, and `toolName`;
- `metadataOnly` fields for Reddi policy, eval, memory, data-source, x402, receipt, and reputation semantics that a reviewed runtime adapter must enforce before execution;
- `unsupportedExecution` for MCP tool declarations because this report does not resolve or invoke MCP servers.

Anthropic rows may be `supported: true` only for static compatibility when no hard unsupported
feature is present. Real settlement and MCP execution remain hard unsupported features. Every
Anthropic row continues to report `runtimeExecutionAllowed=false`, `networkAccess=false`,
`paymentAccess=false`, and `mcpInvocation=false`.

## Gemini Compatibility-Only Mode

The `gemini` target emits `compatibilityMode: gemini-provider-compatibility-only`.
This is a static review artifact, not a Gemini API call or Google runtime activation.

The Gemini row includes:

- model profile mapping from `model.capability`, `model.providers`, and `model.requirements`;
- system instruction mapping from `harness.instructions.inline`;
- function declaration ids from non-MCP `harness.tools`;
- structured-output capability from `model.requirements.structuredOutput`;
- explicit `grounding: not-configured` and `codeExecution: unsupported` diagnostics;
- `metadataOnly` fields for Reddi policy, eval, memory, data-source, x402, receipt, reputation,
  and MCP semantics that a reviewed runtime adapter must enforce before execution;
- `unsupportedExecution` for MCP tool declarations because this report does not resolve or invoke
  MCP servers.

Gemini rows may be `supported: true` only for static compatibility when no hard unsupported feature
is present. Real settlement and MCP execution remain hard unsupported features. Every Gemini row
continues to report `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`,
and `mcpInvocation=false`.

## Runtime Boundary

Provider compatibility reports remain static exports. They may report required
secrets and hosted services, but they must not read credentials, call hosted
providers, probe local model endpoints, resolve MCP servers, invoke tools, or
activate runtimes. Runtime execution remains blocked unless a later, explicit
approved prototype/devnet lane grants a narrower execution boundary.
