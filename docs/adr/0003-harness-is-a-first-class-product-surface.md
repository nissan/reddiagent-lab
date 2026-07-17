# ADR 0003: Harness Is a First-Class Product Surface

## Status

Accepted.

## Context

Agent frameworks often collapse the model, tools, memory, policies, traces, deployment, and payment hooks into runtime code. ReddiAgent treats the operating environment around the model as the part a builder needs to inspect most carefully.

Relevant references:

- `docs/ARCHITECTURE-THESIS.md`
- `docs/REDDIAGENT-VISION-ROADMAP.md`
- `docs/PROSUMER-MVP.md`
- `docs/BUILDER-JOURNEY.md`
- `specs/HARNESS-LIFECYCLE-v0.1.md`
- `specs/SECURITY-PERMISSIONS-v0.1.md`
- `specs/EVAL-GATES-v0.1.md`
- `specs/OBSERVABILITY-v0.1.md`

## Decision

The harness is a first-class product and review surface, not hidden implementation detail.

ReddiAgent should expose tools, functions, skills, data sources, memory, policies, eval gates, traces, runtime intent, deployment descriptors, observability, recovery behavior, and payment or reputation hooks as reviewable ADL and docs surfaces.

## Consequences

- Builder UX should help people reason about harness behavior before choosing a provider or runtime.
- Validation should produce guidance about harness completeness, source boundaries, memory retention, eval gates, and unsupported runtime behavior.
- Future generated starter code should be derived from a reviewed harness definition, not from provider-specific assumptions.
- Runtime readiness evidence should cover the full harness lifecycle, not only model invocation.
