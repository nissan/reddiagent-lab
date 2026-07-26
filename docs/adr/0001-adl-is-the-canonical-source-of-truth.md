# ADR 0001: ADL Is the Canonical Source of Truth

## Status

Accepted.

## Context

ReddiAgent needs one durable definition layer that can outlive any single model provider, runtime, framework, export format, or protocol bridge. The current docs spine describes ReddiAgent as "model definition + harness definition + settlement/reputation extension," with ADL holding those concerns before they are projected into provider reports, strict exports, or runtime plans.

Relevant references:

- `docs/REDDIAGENT-VISION-ROADMAP.md`
- `docs/REDDIAGENT-ARCHITECTURE.md`
- `docs/ARCHITECTURE-THESIS.md`
- `specs/ADL-v0.2.md` (canonical; v0.1 retained for history)
- `specs/ADL-v0.2.schema.json`

## Decision

ADL is the canonical source of truth for ReddiAgent agent definitions.

Provider mappings, framework mappings, A2A Agent Cards, Agent Spec reports, Agent Skills packages, MCP handoff packages, Vercel eve exports, starter manifests, and RAP bridge artifacts are target projections from ADL. They must not become competing canonical definitions.

## Consequences

- Schema, examples, validation guidance, and builder-facing docs should evolve around ADL first.
- Exporters and compatibility reports must preserve ADL semantics or explicitly report loss.
- Silent loss of policy, source-boundary, memory, eval, MCP, payment, receipt, or reputation semantics is unacceptable.
- Future runtime work should load and validate ADL before resolving tools, credentials, providers, payment rails, or deployment targets.
