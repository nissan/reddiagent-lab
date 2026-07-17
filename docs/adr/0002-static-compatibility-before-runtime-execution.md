# ADR 0002: Static Compatibility Before Runtime Execution

## Status

Accepted.

## Context

ReddiAgent is useful only if builders can understand portability and safety tradeoffs before activating live systems. The repo already has deterministic checks, fixtures, reports, and smoke validation for provider compatibility, Agent Spec, A2A Agent Card, Agent Skills, MCP handoff, RAP bridge, starter manifests, and Vercel eve compatibility.

Relevant references:

- `docs/REDDIAGENT-ARCHITECTURE.md`
- `docs/REDDIAGENT-VISION-ROADMAP.md`
- `tests/PROVIDER-COMPATIBILITY-REPORT.md`
- `tests/MCP-RUNTIME-HANDOFF-PACKAGE-REPORT.md`
- `tests/RAP-BRIDGE-REPORT.md`
- `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md`
- `tests/smoke-validation.sh`

## Decision

Compatibility targets start as static/report-only reviews before runtime execution.

Reports may evaluate fit, gaps, warnings, export loss, unsupported features, and readiness evidence. They must not call providers, resolve MCP servers, invoke tools, access wallets, read credentials, deploy infrastructure, or mutate external state unless a later issue explicitly approves and tests a live boundary.

## Consequences

- New targets should begin with fixtures, static reports, and deterministic tests.
- Runtime activation is a separate product gate, not an incidental result of an exporter or docs task.
- Reports should include explicit boundary flags such as `runtimeExecutionAllowed=false`, `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false` where relevant.
- Builders get reviewable evidence before they are asked to trust an integration.
