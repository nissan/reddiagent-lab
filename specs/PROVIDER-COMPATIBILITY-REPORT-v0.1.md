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

- model requirements supported.
- tool types supported.
- runtime target supported.
- secrets referenced, not embedded.
- payment extension enforceable or disabled.
- observability minimum available.

