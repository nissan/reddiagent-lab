# Local Runner Plugin Interface Report

_Anchor issue: #148._

## Scope

This report covers the static local runner plugin interface declaration checker.

The checker does not load, import, install, invoke, resolve, or execute plugins. It only inspects JSON declarations and returns a deterministic readiness report.

## Fixtures

- `tests/fixtures/local-runner-plugin-ready.json`
- `tests/fixtures/local-runner-plugin-unsafe.json`

## Required Boundary

Every report preserves:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `externalExecutionAllowed=false`
- `pluginLoaded=false`
- `pluginInvoked=false`

## Evidence

The ready fixture passes because it declares a deterministic local fixture shape with explicit false capabilities and no side effects.

The unsafe fixture fails closed because it declares external HTTP mode, shell-command metadata, live URL fields, env/API-key-like metadata, enabled network/shell/credential/payment/MCP/filesystem capabilities, enabled execution boundaries, non-deterministic fixture behavior, and payment/wallet fields.

## Decision

Local runner plugins can be described as static reviewed declarations before any future runtime work is scoped. The existing `--execute-tools` behavior remains unchanged and continues to use deterministic project-owned local fixtures only.
