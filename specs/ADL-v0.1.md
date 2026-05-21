# Agent Definition Language v0.1

_Loop 6. Anchor issue: #6._

## Goal

ADL v0.1 is a portable document format for describing an agent as model needs plus harness behavior.

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

## Extension Section

Extensions are namespaced. Recommended v0.1 namespaces: x402, reputation, identity, receipts.

## Validation Principles

- Missing required fields fail validation.
- Unknown extension namespaces warn, not fail, unless strict mode is enabled.
- Runtime-specific unsupported fields should produce compatibility errors.
- Secrets must be referenced by name, not embedded.

