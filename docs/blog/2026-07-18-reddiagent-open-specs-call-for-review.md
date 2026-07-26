# Draft: ReddiAgent Open Specs Call for Review

_Issue #226. Parent epic: #206. Draft only; not externally published._

ReddiAgent is an open specification effort for describing portable agents before they are wired into a runtime, provider, wallet, MCP server, or deployment target.

The core idea is simple: an agent should be reviewable as a definition plus an operating harness. A builder should be able to say what the agent is, which model capabilities it needs, which tools and data sources it can use, which policies and eval gates must hold, and which payment, receipt, reputation, or protocol hooks are intended. A reviewer should then be able to see what is stable, what is only compatibility metadata, what is safe to run locally, and what still needs a separate prototype or beta gate.

The ReddiAgent repo now has enough of that spine to invite structured review.

## What Is Ready to Review

Start with the map:

- `docs/OPEN-SPECS-EXPLAINER.md` is the builder-facing guide to the full spec set.
- `docs/REDDIAGENT-VISION-ROADMAP.md` explains the product direction and staged path from review lab to prototypes.
- `docs/REDDIAGENT-ARCHITECTURE.md` explains the architecture and boundaries.
- `docs/PROTECTED-DOCS-PACKAGE.md` describes the future protected sharing bundle, without publishing it.
- `docs/INDEX.md` is the repository navigation index.

The canonical definition format is ADL. ADL v0.2 is canonical; v0.1 is retained for history:

- `specs/ADL-v0.2.md` (canonical)
- `specs/ADL-v0.2.schema.json` (canonical)
- `specs/ADL-v0.1.md` (superseded, retained for history)
- `specs/ADL-v0.1.schema.json` (superseded, retained for history)
- `specs/DOMAIN-MODEL-v0.1.md`
- `specs/VALIDATION-GUIDANCE-v0.1.md`

ADL covers the agent identity, model profile, harness, tools, data sources, memory, policy, eval gates, runtime intent, deployment intent, observability, recovery, and optional namespaced extensions.

The most useful examples are:

- `examples/simple-agent.yaml`
- `examples/tool-agent.yaml`
- `examples/mcp-readonly-agent.yaml`
- `examples/payment-agent.yaml`
- `examples/invalid/`

Together, they show the intended shape for a small local agent, a tool-using agent with source checks, an MCP declaration that does not invoke a live server, a payment/reputation definition that does not settle funds, and negative fixtures that prove validation fails closed.

## Why Prosumers and Builders Should Care

Most agent tooling starts with a runtime. That is useful when you already know where the agent will run, but it can hide the actual contract:

- Which model features are required?
- Which parts of the harness are safety-critical?
- Which tools can mutate state?
- Which sources are approved?
- Which eval gates are required rather than advisory?
- Which payment or reputation claims are just metadata?
- Which target exports lose important semantics?

ReddiAgent starts one layer earlier. It makes the agent definition and harness legible before execution. That helps prosumers ask better questions, helps builders compare runtime targets, and gives reviewers a paper trail before a prototype, beta, payment rail, or deployment is activated.

This matters most for agents that touch tools, payments, credentials, protocols, or user-visible decisions. The point is not to slow builders down. The point is to make the next step obvious: validate locally, inspect deterministic traces, compare provider mappings, then deliberately choose a bounded prototype path.

## What Is Stable, Experimental, Report-Only, and Future Work

The current docs use status words deliberately.

**Stable enough for review and references:** ADL v0.2 core fields, the domain model, validation guidance, examples, Level 0 validation, Level 1 deterministic local fixture evidence, conformance language, and the navigation spine.

**Experimental:** provider compatibility details, source-check trace shapes, MCP readiness evidence, static export parity details, beta readiness surfaces, and the exact shape of runtime handoff contracts. These are useful now, but prototypes may teach us to change them.

**Report-only:** provider compatibility reports, Agent Spec mappings, A2A Agent Card export, Agent Skills export, MCP runtime handoff package, RAP bridge checks, Vercel eve mapping, protected docs package planning, and starter-code preview manifests. These artifacts explain compatibility or readiness; they do not activate the target.

**Executable prototype track:** the next product direction is to move beyond deliberate report-only work where prototypes can teach more. The queued runtime track starts with a local executable ADL runtime prototype, then a provider-backed sandbox with budgets and eval traces, then guarded MCP and devnet payment handoff work. Each step needs issue-specific tests, guardrails, and audit evidence.

**Future work:** mainnet deployment or mainnet runs, unrestricted spend, silent lossy exports, production runtime operations, and unbounded external actions. Mainnet remains outside current approval.

## Try the Local Deterministic Examples

Use a local Python 3:

```bash
python3 scripts/validate_examples.py examples/tool-agent.yaml
python3 scripts/run_local_agent.py examples/tool-agent.yaml --execute-tools --fail-on-required-gate
python3 scripts/provider_compatibility.py examples/tool-agent.yaml
```

Those commands produce local deterministic evidence. They do not call provider APIs, resolve live MCP servers, read credentials, touch wallets, run devnet or mainnet transactions, deploy, publish, or activate external services.

For broader validation, run:

```bash
bash tests/smoke-validation.sh
```

The evidence reports under `tests/` are meant to be read by humans, not only by CI. In particular:

- `tests/LEVEL-0-CONFORMANCE-REPORT.md`
- `tests/LEVEL-1-CONFORMANCE-REPORT.md`
- `tests/PROVIDER-COMPATIBILITY-REPORT.md`
- `tests/AGENT-SPEC-COMPATIBILITY-REPORT.md`
- `tests/MCP-RUNTIME-HANDOFF-PACKAGE-REPORT.md`
- `tests/RAP-BRIDGE-REPORT.md`
- `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md`
- `tests/PROTECTED-DOCS-PACKAGE-REPORT.md`

## What Feedback We Want

We are looking for review from prosumers, agent builders, runtime and framework maintainers, paid MCP/x402/RAP builders, Vercel eve and Agent Spec users, A2A and Agent Skills users, and anyone who has had to explain agent safety boundaries to a non-specialist.

The most useful feedback is concrete:

- Which ADL fields are confusing or missing?
- Which examples fail to match a real builder workflow?
- Which compatibility reports hide too much target-specific loss?
- Which payment, receipt, reputation, or RAP fields need sharper boundaries?
- Which MCP handoff requirements are unrealistic or too weak?
- Which status labels could be mistaken for runtime approval?
- Which local prototype should be built first to prove or disprove the spec shape?

Please point to the exact file and section when possible.

## Review Intake Path

Use `docs/OPEN-SPEC-REVIEW-INTAKE.md` and `.github/ISSUE_TEMPLATE/open-spec-review.md` to turn feedback into structured review records with:

- reviewer role and target surface;
- linked spec, mapping, example, or evidence file;
- the problem or improvement request;
- suggested acceptance criteria;
- whether the feedback affects stable docs, experimental surfaces, report-only artifacts, executable prototypes, or future work.

The intake notes explain how feedback flows into issues and PRs, and how #220 prototype/beta feedback should be separated from docs-only corrections. Do not publish this post externally until the project maintainer approves the channel, copy, and timing.

## Boundary Statement

This draft is documentation only. It does not publish a blog, deploy docs, select or store a password, call provider APIs, invoke MCP servers, access credentials, touch payment rails, run devnet or mainnet transactions, mutate production infrastructure, or activate runtime services.

The next useful step is public-review intake, then bounded executable prototypes where they produce better evidence than another static report.
