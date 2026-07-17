# ReddiAgent Open Specs Explainer

_Issue #225. Parent epic: #206._

This guide explains how to read the ReddiAgent open specs as a prosumer, builder, reviewer, or protocol integrator. It is written for protected-docs and public-review audiences: start here when you want the map before opening every spec, mapping, report, and fixture.

ReddiAgent treats an agent as a portable definition plus an operating harness, with optional payment, receipt, reputation, and RAP bridge metadata. The specs are meant to answer three practical questions:

1. What did the builder say the agent should be allowed to do?
2. Which local, provider, framework, protocol, or export target can preserve that meaning?
3. What evidence proves the target is safe enough to stay report-only, run locally, become an executable prototype, or move toward beta?

## How to Read the Spec Set

Use the specs in this order:

1. Read `specs/DOMAIN-MODEL-v0.1.md` for the nouns: agent definition, model, harness, tool, data source, memory, policy, eval gate, trace, receipt, reputation, and deployment descriptor.
2. Read `specs/ADL-v0.1.md` and `specs/ADL-v0.1.schema.json` for the canonical shape. ADL is the source of truth; provider files and exports are target views.
3. Open one example from `examples/`: `simple-agent.yaml`, `tool-agent.yaml`, `mcp-readonly-agent.yaml`, or `payment-agent.yaml`.
4. Run or inspect validation through `scripts/validate_examples.py` and `specs/VALIDATION-GUIDANCE-v0.1.md`.
5. Follow the harness, eval, trace, conformance, provider, MCP, and payment specs only for the surface you are reviewing.
6. Check the matching `tests/*-REPORT.md` evidence file before treating any surface as ready.

The fastest builder loop is:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py examples/tool-agent.yaml
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/run_local_agent.py examples/tool-agent.yaml --execute-tools --fail-on-required-gate
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/tool-agent.yaml
```

Those commands read local files and produce deterministic local evidence. They do not call provider APIs, resolve live MCP servers, touch credentials, activate payment rails, deploy, publish, or use mainnet.

## Status Vocabulary

The docs use these status words deliberately:

| Status | Meaning | Examples |
|---|---|---|
| Stable | Shape is canonical enough for examples, validation, tests, and downstream references. | ADL v0.1 core fields, domain model, validation guidance, conformance levels. |
| Experimental | Shape is documented and useful, but likely to change as prototypes teach us more. | Some provider compatibility fields, source-check traces, MCP readiness evidence, beta readiness surfaces. |
| Report-only | The repo can explain compatibility or readiness without invoking the live target. | Provider reports, Agent Spec/A2A/Agent Skills exports, MCP handoff package, RAP bridge checks, Vercel eve mapping. |
| Executable prototype | Local/devnet/prototype execution may be introduced when a queued issue has guardrails, tests, and evidence. | Local ADL runtime prototype, provider sandbox, guarded MCP/devnet handoff work in the #220 track. |
| Future work | The shape is intentionally parked until policy, safety, or product evidence improves. | Mainnet, unrestricted spend, production runtime operations, silent lossy exports. |

Mainnet deployment and mainnet runs remain not approved. Devnet and executable prototypes may be used only when the active issue requires them, with least privilege and audit evidence.

## Core Spec Map

### ADL and Schema

`specs/ADL-v0.1.md` defines the top-level agent document:

- `identity`: name, version, owners, and descriptive metadata.
- `model`: required model capabilities, provider preferences, constraints, cost/latency expectations, and structured-output needs.
- `harness`: instructions, tools, functions, skills, data sources, memory, policies, eval gates, runtime, deployment, observability, and recovery.
- `extensions`: namespaced metadata for payment, receipts, reputation, protocol bridges, and future targets.

`specs/ADL-v0.1.schema.json` is the machine-checkable contract. `specs/VALIDATION-GUIDANCE-v0.1.md` explains how validation errors should help a builder fix the definition instead of exposing raw schema noise.

Examples:

- `examples/simple-agent.yaml`: smallest useful definition.
- `examples/tool-agent.yaml`: local tool and source-check flow.
- `examples/mcp-readonly-agent.yaml`: MCP declaration without live invocation.
- `examples/payment-agent.yaml`: payment/reputation metadata without settlement.
- `examples/invalid/`: negative fixtures for validator behavior.

### Domain Model

`specs/DOMAIN-MODEL-v0.1.md` explains the relationships behind ADL. The important boundary rule is that the definition is not the same thing as execution. A spec can declare a model, tool, payment rail, or deployment target while the repo still keeps that target static, report-only, or gated.

Use the domain model when reviewing whether a new feature belongs in ADL core, a harness field, a namespaced extension, a compatibility mapping, or a runtime implementation.

### Harness Lifecycle

`specs/HARNESS-LIFECYCLE-v0.1.md` describes the future run sequence:

1. load ADL;
2. validate and resolve local references;
3. attach tools, data, memory, policies, and eval gates;
4. start traces;
5. run the model/tool loop;
6. evaluate gates;
7. emit receipts, reputation signals, and observability;
8. persist state and shut down or await the next task.

Today, most repo evidence is static or local. The executable prototype track should turn this lifecycle into runnable behavior only where tests, boundaries, and approvals are explicit.

### Eval Gates, Traces, and Source Checks

`specs/EVAL-GATES-v0.1.md` defines required and advisory checks. `specs/TRACE-EVENTS-v0.1.md` defines deterministic dry-run events. Together they let a reviewer ask: did the agent do the required local checks, did the trace prove it, and did failure stop the run when it should?

Related evidence:

- `tests/LEVEL-0-CONFORMANCE-REPORT.md`
- `tests/LEVEL-1-CONFORMANCE-REPORT.md`
- `tests/TRACE-SNAPSHOTS.md`
- `tests/COMPATIBILITY-SNAPSHOTS.md`
- `tests/TOOL-EXECUTION-FIXTURE-REPORT.md`

### Conformance

`specs/CONFORMANCE-v0.1.md` describes levels of readiness. Level 0 is schema and static definition quality. Level 1 adds deterministic local fixture behavior. Level 2 covers compatibility and export targets. Later levels should cover guarded live/prototype behavior only after the #220 runtime track adds enough evidence.

Conformance should be read as a gate, not a marketing label. A surface is ready only when its tests and reports match the claimed level.

## Payment, Reputation, and RAP Bridge

`specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md` keeps payment and reputation metadata optional. `specs/X402-DRY-RUN-RECEIPT-v0.1.md` defines dry-run x402 receipt evidence. `specs/RAP-BRIDGE-v0.1.md` explains how ReddiAgent metadata can later hand off to Reddi Agent Protocol.

Read these as a layered contract:

- ADL records payment intent, limits, authority constraints, receipt needs, and reputation signals.
- x402/AP2-style evidence can be represented as dry-run receipt and mandate metadata.
- RAP can later own settlement, identity, reputation, and protocol enforcement.

Current repo evidence remains report-only unless a queued prototype issue explicitly opens a bounded live/devnet lane. Mainnet remains future work requiring fresh approval.

Related evidence:

- `tests/PAYMENT-DRY-RUN-RECEIPT-REPORT.md`
- `tests/AP2-X402-MANDATE-REPORT.md`
- `tests/RAP-BRIDGE-REPORT.md`
- `tests/RAP-PROVIDER-HANDOFF-SUMMARIES-REPORT.md`

## Provider Mapping and Compatibility

`specs/PROVIDER-MAPPING-v0.1.md` explains how ADL model and harness semantics map to provider/framework targets. `specs/PROVIDER-COMPATIBILITY-REPORT-v0.1.md` describes the report output.

The key rule: compatibility reports answer "what would this mean for the target?" without making the target run. Unsupported or metadata-only semantics must stay visible.

Provider and framework mappings:

- `mappings/OPENAI.md`
- `mappings/ANTHROPIC.md`
- `mappings/GEMINI.md`
- `mappings/LANGGRAPH.md`
- `mappings/LLAMAINDEX.md`
- `mappings/STRANDS.md`
- `mappings/EVE.md`

Evidence:

- `tests/PROVIDER-COMPATIBILITY-REPORT.md`
- `tests/PROVIDER-COMPATIBILITY-CLI-FLAGS-REPORT.md`
- `tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md`
- `tests/OPENAI-COMPATIBILITY-MODE-REPORT.md`
- `tests/ANTHROPIC-MCP-COMPATIBILITY-MODE-REPORT.md`
- `tests/GEMINI-COMPATIBILITY-MODE-REPORT.md`
- `tests/OLLAMA-COMPATIBILITY-MODE-REPORT.md`
- `tests/LANGGRAPH-COMPATIBILITY-REPORT.md`

## Export and Handoff Targets

### Agent Spec

`mappings/AGENT-SPEC.md` and `specs/AGENT-SPEC-COMPATIBILITY-v0.1.md` show how ADL maps to Agent Spec. The current target is report-only/strict-export evidence; unsupported ReddiAgent semantics are not silently dropped.

Evidence: `tests/AGENT-SPEC-COMPATIBILITY-REPORT.md` and `tests/test_agent_spec_compatibility.py`.

### A2A Agent Card

`mappings/A2A-AGENT-CARD.md` maps identity, capabilities, skills, security, and supported interfaces into an A2A Agent Card review artifact.

Evidence: `tests/A2A-AGENT-CARD-EXPORT-REPORT.md` and `tests/test_a2a_agent_card_export.py`.

### Agent Skills

`mappings/AGENT-SKILL.md` and `specs/SKILL-PACKAGE-CONTRACT-v0.1.md` map an ADL definition toward an Agent Skills / `SKILL.md` package. Treat `allowed-tools` and other pre-approval hints as static review hints until runtime policy enforces them.

Evidence: `tests/AGENT-SKILL-EXPORT-REPORT.md` and `tests/test_agent_skill_export.py`.

### Vercel eve

`mappings/EVE.md` treats Vercel eve as a static compatibility target. The current repo does not deploy to eve or activate an eve runtime; it explains which ADL fields could inform an eve-facing artifact later.

Evidence: `tests/EVE-COMPATIBILITY-REPORT.md` and `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md`.

### Starter Manifests

Starter-code work is currently manifest-first and report-only. `tests/STARTER-CODE-PLAN-REPORT.md` explains planned file manifests, template contracts, and safety policy fixtures. Do not treat starter manifests as runnable project generation until a later issue explicitly changes that state.

### MCP Handoff

`specs/MCP-TOOL-MAPPING-v0.1.md`, `specs/MCP-RUNTIME-HANDOFF-PACKAGE.schema.json`, and `tests/MCP-RUNTIME-HANDOFF-PACKAGE-REPORT.md` define how MCP intent can be packaged for review without live server resolution or invocation.

Related evidence:

- `tests/MCP-ADAPTER-SHAPE-REPORT.md`
- `tests/MCP-ADAPTER-CONTRACT-REPORT.md`
- `tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md`
- `tests/MCP-ADAPTER-AGGREGATION-REPORT.md`
- `tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md`
- `tests/MCP-SERVER-RESOLUTION-REPORT.md`
- `tests/MCP-CAPABILITY-POLICY-REPORT.md`
- `tests/MCP-READINESS-EVIDENCE-REPORT.md`
- `docs/MCP-READINESS-RELEASE-CHECKLIST.md`

## Public-Review Questions

Reviewers should focus on these questions:

- Does ADL describe the agent clearly enough for a builder to validate and improve it?
- Are provider and framework losses explicit, or could a builder assume portability that does not exist?
- Are payment, receipt, reputation, and RAP bridge fields separated from live settlement?
- Do MCP and tool declarations fail closed before live invocation?
- Do eval gates and traces prove source checks and required-gate outcomes?
- Are stable, experimental, report-only, executable-prototype, and future-work states clear?
- Are devnet/prototype paths bounded, and is mainnet still excluded?

## Review Submission and Intake

Use `docs/OPEN-SPEC-REVIEW-INTAKE.md` and `.github/ISSUE_TEMPLATE/open-spec-review.md` to submit structured feedback. The template asks for reviewer role, target spec/mapping/example/evidence file, problem or improvement, suggested acceptance criteria, and a state classification: stable, experimental, report-only, executable prototype, or future work.

Docs-only corrections should stay tied to #206 and the exact file or section they improve. Feedback that asks for runnable behavior, provider-backed sandboxes, live MCP, devnet payment handoff, credentials, deployment, observability, or beta operations should be separated into the #220 prototype/beta track rather than mixed into documentation-only fixes. Mainnet requests remain future work until fresh explicit approval exists.

## Guardrails for This Guide

This guide is documentation only. It does not publish externally, deploy a docs site, select or store a password, call provider APIs, resolve or invoke live MCP servers, access credentials, touch wallets, run devnet/mainnet transactions, or activate runtime services.

External publication of this guide or the protected package still requires Nissan's approval for the location and access controls. Mainnet deployment and mainnet runs require fresh explicit approval.
