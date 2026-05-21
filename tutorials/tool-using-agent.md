# Tutorial: Tool-Using Agent

_Loop 39/41. Anchor issues: #40, #41._

## Goal

Understand how ReddiAgent represents one typed tool and one source-check eval gate.

## File

    examples/tool-agent.yaml

## Dry-Run

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/run_local_agent.py examples/tool-agent.yaml

Expected summary includes:

- toolCount: 1
- policyCount: 1
- evalGateCount: 1
- paymentEnabled: false

## Tool Contract

The search_docs tool has:

- id
- type
- description
- inputSchema
- outputSchema

## Builder Lesson

Tools are not just functions. They are permissions, schemas, audit events, failure modes, and eval obligations.

