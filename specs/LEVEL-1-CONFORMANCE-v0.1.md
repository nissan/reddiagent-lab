# Level 1 Conformance v0.1

_Loop 52. Anchor issue: #53._

## Definition

Level 1 means an ADL file is:

- Level 0 schema-valid.
- compatible with local-python dry-run.
- able to produce deterministic trace events.
- able to summarize model, runtime, tool, policy, eval, and payment-enabled state.

## Current Scope

Level 1 applies to:

- examples/simple-agent.yaml
- examples/tool-agent.yaml

Payment-capable agents remain Level 0 plus payment dry-run receipt until real policy and receipt enforcement exists.

## Required Command

    python3 tests/test_level1.py

