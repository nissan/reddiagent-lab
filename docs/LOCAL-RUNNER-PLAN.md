# Local Python Runner Plan

_Loop 24. Anchor issue: #26._

## Goal

Build the smallest runner that makes ReddiAgent concrete for prosumers without committing to one hosted provider.

## First Target

Run or dry-run:

- examples/simple-agent.yaml
- examples/tool-agent.yaml

Payment-agent remains dry-run only until receipt and policy enforcement stabilize.

## Runner Stages

1. Load ADL YAML.
2. Validate against specs/ADL-v0.1.schema.json.
3. Print resolved model profile.
4. Print harness instructions.
5. Register declared tools.
6. Check policies.
7. Simulate one task.
8. Emit run summary.

## Non-Goals

- No real model calls in the first runner.
- No external tool execution.
- No real payment.
- No secret loading.

## Why Dry-Run First

Dry-run exposes the harness contract safely: the builder sees model requirements, policies, tools, eval gates, and expected trace events before spending money or invoking external systems.

