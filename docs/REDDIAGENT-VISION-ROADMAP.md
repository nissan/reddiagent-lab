# ReddiAgent Vision and Roadmap

_Issue #209. Parent epic: #206._

## First-Pass Summary

ReddiAgent is a portable agent definition and harness literacy layer for prosumers and technical builders. It helps a builder describe an agent as a model profile plus an operating harness, then review which local, provider, framework, and protocol targets can support that definition without losing safety-critical semantics.

The product bet is that useful agents should not start as vendor-specific scripts. A builder should be able to define the job, model needs, tools, data, memory, policies, eval gates, traces, payment intent, receipts, and reputation metadata once, then understand what can run locally, what can export to platform formats, and what must remain report-only until stronger guardrails exist.

## Who It Serves

- **Prosumers** who want to build useful agents without learning every provider's mental model first.
- **Technical product owners** who need a clear review path before runtime, payment, or deployment activation.
- **Protocol builders** who need a bridge from agent harness behavior into Reddi Agent Protocol payment, evidence, and reputation flows.
- **Agent framework users** who want portability reports before committing to one runtime or ecosystem.

## Product Thesis

ReddiAgent separates three concerns that agent frameworks often blend together:

1. **Model definition:** the capability envelope the agent needs, such as tool calling, structured output, latency, cost, context, and allowed providers.
2. **Harness definition:** the operating environment around the model, including tools, functions, skills, memory, data sources, policies, eval gates, traces, deployment descriptors, auth, observability, and recovery behavior.
3. **Payment and reputation extension:** optional x402/RAP-aligned metadata for payment intent, budget policy, receipts, reputation signals, identity, and authority constraints.

That separation lets ADL stay canonical while compatibility reports, strict exports, and starter manifests explain how much of the definition can move to targets such as Agent Spec, A2A Agent Card, Agent Skills packages, OpenAI, Anthropic, Gemini, Ollama, LangGraph, LlamaIndex, AWS Strands, Vercel eve, and future RAP-facing systems.

## Current Spine

The current repo is strongest as a static validation and review lab:

- **Canonical definition:** `specs/ADL-v0.1.md` and `specs/ADL-v0.1.schema.json`.
- **Builder path:** `docs/PROSUMER-MVP.md`, `docs/BUILDER-JOURNEY.md`, and the local validation UI fixture.
- **Static examples:** `examples/simple-agent.yaml`, `examples/tool-agent.yaml`, `examples/mcp-readonly-agent.yaml`, `examples/payment-agent.yaml`, and invalid fixtures.
- **Validation and traces:** `scripts/validate_examples.py`, `scripts/run_local_agent.py`, Level 0/Level 1 conformance reports, trace snapshots, and smoke validation.
- **Compatibility and exports:** report-only or strict-lossless surfaces for Agent Spec, A2A Agent Card, Agent Skills, provider compatibility, RAP bridge, MCP runtime handoff, payment receipts, starter manifests, and Vercel eve compatibility.
- **Safety posture:** static/report-only checks default to fail-closed behavior for secrets, live external actions, payments, MCP invocation, provider calls, deployment, and runtime activation.

## Roadmap Swimlanes

### 1. Definition and Conformance

Keep ADL v0.1 as the source of truth. Continue tightening schema, validation guidance, examples, error UX, conformance reports, source-boundary checks, data-source contracts, memory contracts, eval gates, and trace semantics before expanding runtime behavior.

### 2. Prosumer Builder

Turn the current CLI and static HTML fixtures into a guided builder path: choose an agent job, pick a model profile, add optional tools/data/memory, attach policies and eval gates, validate ADL, dry-run locally, inspect traces, and export review artifacts. The first product surface is a trustworthy builder and reviewer, not a marketplace.

### 3. Compatibility Targets

Keep ADL canonical while building target-specific reports and strict exports where they are lossless. Current targets include provider compatibility, Agent Spec, A2A Agent Card, Agent Skills packages, MCP runtime handoff, RAP bridge, starter manifests, and Vercel eve. Metadata-only and unsupported semantics must stay visible to builders instead of being silently dropped.

### 4. Runtime Readiness

Move from deterministic local dry-runs toward real execution only after readiness bundles, negative fixtures, fail-closed gates, and review evidence prove that external actions are bounded. Live provider calls, MCP resolution/invocation, credential use, runtime activation, and deployment are separate gates, not incidental side effects of docs or export work.

### 5. Payment, Receipts, and RAP Bridge

Model payment intent, AP2-like authority constraints, x402 evidence, receipts, and reputation as optional harness metadata first. Live settlement, wallet/facilitator access, unrestricted spend, and mainnet runs remain outside the current docs spine. The near-term RAP path is a dry-run bridge that makes protocol adoption reviewable before authorizing real payment execution.

### 6. Publishable Docs Hub

Issue #206 turns the repo's accumulated technical work into a protected, human-readable docs hub. This issue creates the vision/roadmap entrypoint. Follow-on issues add the architecture diagram/explainer, ADR register, and protected publishable docs site package.

## Current Sequencing

1. **Vision and roadmap spine:** this document, linked from the repo navigation surfaces.
2. **Architecture diagram and explainer:** `docs/REDDIAGENT-ARCHITECTURE.md` gives the high-level view of ADL, harness, compatibility reports, runtime boundaries, and RAP bridge.
3. **ADR register:** `docs/adr/0000-adr-index.md` records initial decisions covering ADL canonicality, report-only compatibility, static guardrails, and payment/runtime boundaries.
4. **Protected docs package:** a publishable site bundle prepared for review, but not publicly deployed until Nissan approves location and access controls.
5. **Post-docs implementation queue:** resume issue-backed ReddiAgent/RAP backlog work based on `docs/IMPLEMENTATION-BACKLOG.md`, `docs/ROADMAP.md`, and `docs/NEXT-10-IMPLEMENTATION-ISSUES.md`.

## Deliberately Out of Scope Until Guardrails Change

- Public docs publication or deployment without Nissan approval for location and access.
- Mainnet deployment or mainnet runs.
- Live wallet, facilitator, payment rail, settlement, or unrestricted spend.
- Live MCP server resolution/invocation outside an explicitly approved lane.
- Provider/model/API calls outside an explicitly approved lane.
- Credential lookup, storage, or mutation unless a queued task truly requires it and the action is reported.
- Starter-code file generation that writes runnable projects before static manifest and template gates are ready.
- Dependency installs, dev servers, or framework runtime activation as a side effect of docs work.
- Silent lossy export of ReddiAgent policy, payment, receipt, reputation, source-boundary, memory, or eval semantics.

## Reading Path

Start with this spine, then move outward:

- `docs/PRODUCT-PRINCIPLES.md` for product rules.
- `docs/POSITIONING-MEMO.md` for short positioning.
- `docs/REDDIAGENT-ARCHITECTURE.md` for the high-level system diagram and explainer.
- `docs/adr/0000-adr-index.md` for durable architectural decisions and rationale.
- `docs/ARCHITECTURE-THESIS.md` for the model/harness/economic-layer separation.
- `specs/ADL-v0.1.md` for the canonical definition language.
- `docs/PROSUMER-MVP.md` and `docs/BUILDER-JOURNEY.md` for the builder flow.
- `docs/ROADMAP.md`, `docs/IMPLEMENTATION-BACKLOG.md`, and `docs/NEXT-10-IMPLEMENTATION-ISSUES.md` for implementation sequencing.
- `tests/*-REPORT.md` files for deterministic evidence behind each compatibility or readiness surface.
