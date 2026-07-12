# Agent Definition Language v0.1

_Loop 6. Anchor issue: #6._

## Goal

ADL v0.1 is a portable document format for describing an agent as model needs plus harness behavior.

ADL is ReddiAgent's canonical source of truth. External manifest formats such as Open Agent Specification / Agent Spec are compatibility targets, not replacements. If a target cannot enforce ReddiAgent policy, payment, receipt, source-boundary, MCP, or reputation semantics, the adapter must report the loss before export or execution.

## Top-Level Shape

    apiVersion: reddiagent.dev/v0.1
    kind: Agent
    metadata:
      name: research-assistant
      description: Answers questions using approved sources
    model:
      capability: chat
      providers:
        preferred: openai
        fallbacks: [anthropic, gemini, ollama]
      requirements:
        toolCalling: true
        structuredOutput: true
    harness:
      instructions: ./prompts/system.md
      tools: []
      dataSources: []
      memory:
        mode: session
      policies: []
      evalGates: []
      runtime:
        target: local-python
    extensions: {}

## Required Sections

- apiVersion
- kind
- metadata
- model
- harness

## Model Section

Fields:

- capability
- providers.preferred
- providers.fallbacks
- requirements.toolCalling
- requirements.structuredOutput
- requirements.contextWindow
- requirements.modalities
- cost.latencyBudget
- cost.maxUsdPerTask

## Harness Section

Fields:

- instructions
- tools
- functions
- skills
- dataSources
- memory
- policies
- evalGates
- runtime
- deployment
- observability
- recovery

### dataSources

Each `harness.dataSources` item declares a reviewed source the harness may use or cite.

Required fields:

- `id`
- `type`
- `description`

Supported `type` values:

- `document`
- `file`
- `web`
- `api`
- `database`
- `vector-index`
- `mcp`
- `knowledge-base`

Optional fields:

- `sourceRef`
- `path`
- `url`
- `trust` (`approved`, `untrusted`, or `unknown`)

### memory

`harness.memory` must declare `mode`.

Supported `mode` values:

- `none`
- `session`
- `persistent`
- `external`

Supported fields:

- `mode`
- `retention`
- `scope` (`task`, `session`, `project`, `user`, `workspace`, or `external`)
- `storageRef`
- `privacyPolicy`

Persistent or external memory must declare both `retention` and `privacyPolicy` before runtime execution is considered safe.

## Extension Section

Extensions are namespaced. Recommended v0.1 namespaces: x402, reputation, identity, receipts.

## Validation Principles

- Missing required fields fail validation.
- Unknown extension namespaces warn, not fail, unless strict mode is enabled.
- Runtime-specific unsupported fields should produce compatibility errors.
- Secrets must be referenced by name, not embedded.
- External manifest exports must preserve Reddi-specific extensions as namespaced metadata or fail explicitly when preservation is unsafe.
