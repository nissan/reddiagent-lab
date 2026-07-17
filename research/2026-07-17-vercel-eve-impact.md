# Vercel eve Impact Research

_Date: 2026-07-17 AEST_
_Scope: static research and compatibility analysis only; no eve runtime install, dev server, model call, MCP invocation, deployment, credential access, payment access, or paid call._

## Executive Summary

Vercel's `eve` is not primarily a neutral Markdown interchange format. It is a filesystem-first TypeScript runtime and compiler for durable production agents. An eve agent is authored as an `agent/` directory: always-on instructions in Markdown or TypeScript, tools in TypeScript, skills in Markdown/`SKILL.md`, connections to MCP/OpenAPI services, channels, schedules, subagents, sandbox configuration, hooks, evals, and runtime model config.

The practical impact on ReddiAgent is positive but bounded:

- Treat eve as a new static/export compatibility target, similar to Agent Spec, A2A Agent Card, Agent Skills, and LangGraph report-only mappings.
- Do not replace ADL. ADL remains the canonical ReddiAgent source of truth because it carries policy, source-boundary, x402/payment, receipts, reputation, readiness, and fail-closed export semantics that eve does not encode as portable schema.
- The strongest near-term upgrade is an `ADL -> eve project layout` static report/export plan that emits review-only file manifests and compatibility diagnostics.
- The strongest conceptual borrowing is eve's filesystem-first directory layout, especially path-derived identities, `instructions.md`, on-demand `skills/`, `tools/*.ts`, `connections/*.ts`, `schedules/*.md|ts`, and `/eve/v1/info`-style inspectability.
- Runtime adoption should stay blocked until a separate approval. eve's value is tied to Vercel Functions, Workflows, Sandbox, Connect, AI Gateway/model providers, and platform billing/limits.

## Crawl Method

The crawl used:

- Web search for public eve launch, docs, KB, changelog, templates, independent reviews, and known issue reports.
- A local clone of `https://github.com/vercel/eve` at commit `f7c69b1a2ad044a6ba89db7bb6241c469d3ef101` from 2026-07-16.
- Local inspection of the cloned `docs/` tree, README, package metadata, compiler manifest code, `/eve/v1/info` response schema, and core public API docs.
- NPM metadata check: `eve@0.24.6` is the current published package as of 2026-07-17 09:20 AEST context, published 2026-07-16T19:52:40Z.

Depth interpretation:

- Depth 0: Vercel launch page/blog and GitHub repo.
- Depth 1: linked docs pages, Agent Stack pages, pricing/limits, changelog, KB guides, templates.
- Depth 2: docs cross-links for project layout, instructions, skills, tools, connections, schedules, subagents, sandbox, security model, execution/durability, evals, dynamic capabilities, remote agents, channels, client API.
- Depth 3: implementation surfaces behind those docs, especially compiled manifest, agent info response, runtime schema, package exports, and selected independent reviews/issue reports for operational risk.

## Primary Sources Reviewed

- Vercel launch blog, 2026-06-17: `https://vercel.com/blog/introducing-eve`
- Vercel eve product page: `https://vercel.com/eve`
- Vercel Agent Stack blog: `https://vercel.com/blog/agent-stack`
- Vercel eve pricing and limits docs: `https://vercel.com/docs/eve/pricing`
- Vercel changelog for Agent Runs in MCP/CLI, 2026-07-03: `https://vercel.com/changelog/eve-agent-runs-vercel-mcp-cli`
- Vercel KB Slack starter: `https://vercel.com/kb/guide/eve-slack-agent-starter`
- Vercel KB skills guide: `https://vercel.com/kb/guide/how-to-add-eve-skills`
- GitHub repo: `https://github.com/vercel/eve`
- Local cloned docs from `vercel/eve`: `docs/introduction.mdx`, `docs/reference/project-layout.md`, `docs/instructions.mdx`, `docs/skills.mdx`, `docs/tools/overview.mdx`, `docs/agent-config.md`, `docs/connections/mcp.mdx`, `docs/connections/openapi.mdx`, `docs/schedules.mdx`, `docs/subagents.mdx`, `docs/sandbox.mdx`, `docs/concepts/default-harness.md`, `docs/concepts/security-model.md`, `docs/concepts/execution-model-and-durability.md`, `docs/evals/overview.mdx`, `docs/concepts/context-control.md`, `docs/guides/dynamic-capabilities.md`, `docs/guides/remote-agents.md`, `docs/channels/overview.mdx`, `docs/guides/client/overview.mdx`, `docs/reference/typescript-api.md`
- Independent review for portability risk: `https://zackproser.com/blog/is-vercel-eve-worth-it-agent-framework-review`

## What eve Actually Is

eve's core abstraction is "agent as directory":

```text
agent/
  agent.ts
  instructions.md
  tools/
  skills/
  connections/
  channels/
  schedules/
  subagents/
  sandbox/
  hooks/
  lib/
```

Important mechanics:

- Identity comes from filesystem paths, not explicit `name` fields. For example, `agent/tools/get_weather.ts` becomes tool `get_weather`; `agent/connections/linear.ts` becomes connection `linear`; `agent/subagents/researcher/agent.ts` becomes subagent `researcher`.
- `instructions.md` is the always-on system prompt. `instructions.ts` or an `instructions/` directory can compose prompt fragments at build time or resolve dynamic fragments at runtime.
- `skills/` are on-demand procedures, aligned with the broader Agent Skills `SKILL.md` model. Loading a skill adds instructions to context; it does not add an execution surface.
- `tools/*.ts` are typed executable actions with schemas and optional approval gates. Tools execute in the app runtime, not inside the sandbox, and can read environment variables.
- `connections/*.ts` connect to remote MCP or OpenAPI services. The model discovers them through a framework-owned `connection_search` surface; connection tools are qualified as `<connection>__<tool>`.
- `channels/` adapt inbound/outbound surfaces such as HTTP, Slack, Discord, Teams, Telegram, Twilio, GitHub, Linear, or custom routes.
- `schedules/` define root-only cron-triggered work as Markdown prompts or TypeScript handlers.
- `subagents/` can be root-agent copies or declared specialists with isolated tools, skills, connections, state, and sandbox.
- The sandbox is a separate execution context for shell/file tools and authored workspace files. It supports Vercel Sandbox, Docker, microsandbox, just-bash, or custom backends.
- Durable execution is based on Workflow SDK/Vercel Workflow. Sessions can pause for approvals, OAuth, subagents, or human input and resume from checkpoints.
- Evals are authored in `evals/*.eval.ts`, driving a real eve server/client protocol with deterministic or judge-backed assertions.
- `/eve/v1/info` exposes a structured agent inspection response with model, tools, connections, instructions, skills, channels, schedules, subagents, sandbox, diagnostics, workflow, and workspace metadata.

## Cross-LLM Compatibility Reality Check

The user's intuition is partly right: eve is cross-model in the practical provider-routing sense, but not a pure cross-LLM agent-definition standard.

What is portable:

- Markdown instructions.
- Markdown/`SKILL.md` skills.
- Tool schemas where they are plain JSON Schema/Standard Schema/Zod-derived.
- MCP/OpenAPI connection declarations at a conceptual level.
- Channel-independent agent behavior inside eve.
- Model selection through Vercel AI Gateway ids or AI SDK language models.

What is not neutral:

- Runtime semantics are eve-specific: durable workflow checkpoints, parked continuations, event streams, subagent protocol, built-in tools, sandbox behavior, approvals, dynamic capability resolution, eval runner, and channel adapters.
- Tool implementation is TypeScript and imports eve APIs.
- Model routing defaults through Vercel AI Gateway unless a provider-authored AI SDK model is used.
- Production durability, observability, sandbox, Connect OAuth, and pricing are tied to Vercel products when deployed on Vercel.
- The compiled manifest and `/eve/v1/info` shape are inspectable, but they are not advertised as a general interchange standard.

Conclusion: eve should be modeled as a framework/export target, not as a replacement for ReddiAgent ADL or Agent Spec compatibility.

## ADL to eve Mapping

| ReddiAgent ADL | eve target | Fit | Notes |
|---|---|---:|---|
| `metadata.name` | package/app name or project directory | Partial | eve root name comes from `package.json` or app root. Need static manifest note. |
| `metadata.description` | root `defineAgent({ description })` mostly for subagents, metadata in generated docs | Partial | Root description is less central than subagent description. |
| `harness.instructions.inline` | `agent/instructions.md` | Strong | Direct Markdown target. |
| `harness.instructions.path` | `agent/instructions.md` or copied referenced file | Strong if bundled | Must preserve source reference if not bundled. |
| `model.providers.preferred` | `agent/agent.ts` `model` | Partial | Needs provider-id mapping to AI Gateway or direct AI SDK model. |
| `model.providers.fallbacks` | dynamic model resolver or AI Gateway routing metadata | Partial | eve has dynamic model selection, but not ADL's provider preference semantics exactly. |
| `model.requirements.toolCalling` | tool availability / model capability report | Partial | Static report can warn if selected model support is unknown. |
| `model.requirements.structuredOutput` | `outputSchema` and tool schemas | Partial | Good for task/subagent output, less universal for all conversation turns. |
| `model.requirements.contextWindow` | `modelContextWindowTokens` / catalog metadata | Partial | Can be emitted as config or compatibility warning. |
| `harness.tools/functions` | `agent/tools/<id>.ts` stubs | Strong for static manifest; runtime blocked | ReddiAgent can generate typed stub plans, not executable integration, without approval. |
| `harness.skills` | `agent/skills/<id>.md` or `agent/skills/<id>/SKILL.md` | Strong | eve explicitly aligns with Agent Skills progressive disclosure. |
| `harness.dataSources[type=mcp]` | `agent/connections/<id>.ts` MCP connection | Partial | Runtime invocation must remain blocked; allowlists/approval metadata can map. |
| `harness.dataSources[type=api]` | OpenAPI connection | Partial | Only if OpenAPI spec exists or is emitted inline. |
| `harness.memory.mode=session` | `defineState` / durable session state | Partial | eve state is session-scoped. Persistent/external memory needs external store. |
| `harness.policies[type=approval]` | tool/connection approval policy | Partial | Some approval gates map; ReddiAgent policy remains authoritative. |
| `harness.policies[type=network]` | sandbox network policy | Partial | Good conceptual match for sandbox egress; app-runtime network remains separate. |
| `harness.policies[type=payment]` | no direct standard target | Weak | Must stay metadata-only/fail-closed. |
| `harness.evalGates` | `evals/*.eval.ts` plan | Partial | eve evals can express tests, but Reddi source/payment gates are not automatic. |
| `harness.runtime.target` | eve runtime/deployment notes | Weak-to-partial | New enum value may be needed only as compatibility target, not runtime target yet. |
| `extensions.x402` | namespaced metadata only | Weak | No live payment behavior. |
| `extensions.receipts` | namespaced metadata only | Weak | Preserve, do not mutate. |
| `extensions.reputation` | namespaced metadata only | Weak | Preserve, do not mutate. |

## ReddiAgent Opportunities

1. Add a `mappings/EVE.md` static mapping document.
2. Add a report-only script, likely `scripts/eve_compatibility.py`, that reads ADL examples and emits:
   - discovered eve slots,
   - target file manifest,
   - supported/lossless flags,
   - metadata-only Reddi extensions,
   - unsupported runtime/payment/reputation/source-boundary features,
   - static guardrail flags: `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, `mcpInvocation=false`, `deploymentAllowed=false`.
3. Add fixtures for `simple-agent.yaml`, `tool-agent.yaml`, `mcp-readonly-agent.yaml`, `payment-agent.yaml`, and invalid examples.
4. Add strict export only after the report can prove losslessness. Initial strict export should probably refuse anything beyond simple instructions, tool schemas, basic skills, and non-live metadata.
5. Add an eve parity row to the existing static export target parity matrix backlog (#196) if/when the loop is explicitly restarted.
6. Reuse eve's `/eve/v1/info` idea for ReddiAgent: a stable local inspectable JSON bundle that reports available tools, skills, connections, policies, guardrails, dynamic/reserved surfaces, and blocked execution flags.
7. Upgrade Agent Skills alignment: eve's `skills/` support validates ReddiAgent's existing `AGENT-SKILL.md` direction. ReddiAgent should make packaged `SKILL.md` output a first-class bridge for eve compatibility.
8. Consider an "eve project skeleton dry-run manifest" but do not write runnable projects yet. The existing starter-code dry-run safety posture fits perfectly.

## Risks and Non-Goals

- eve is beta and moving quickly. Current package is `0.24.6`; API churn is likely before GA.
- Production use can spend money through Vercel Functions, Workflows, Sandbox, AI Gateway/model providers, and third-party APIs. Any runtime path requires explicit approval and budgeting.
- Vercel-native pieces are the point of the framework. Self-hosting exists at the docs level through `eve start`, Nitro, Workflow worlds, and custom sandbox backends, but portability cost is real.
- Generated TypeScript tools could become live side-effect surfaces if mistakenly treated as executable output. ReddiAgent exports must remain static/report-only until reviewed.
- MCP/OpenAPI connections in eve are live network surfaces. ReddiAgent should only emit metadata/manifests and fail closed on invocation.
- App-runtime tools can read `process.env`; sandbox isolation does not cover authored tool code. ReddiAgent's credential policy remains stricter.
- eve has cost controls and limits, but ReddiAgent's x402/payment/receipt/reputation semantics are not native eve features.

## Recommendation

Create a conservative ReddiAgent issue when backlog work is explicitly restarted:

> Add static Vercel eve compatibility mapping/report

Acceptance shape:

- `mappings/EVE.md`
- `scripts/eve_compatibility.py`
- `tests/EVE-COMPATIBILITY-REPORT.md`
- focused tests for simple/tool/MCP/payment fixtures
- all generated reports include static guardrail flags set false for runtime/network/payment/MCP/deployment
- strict export is out of scope unless all ReddiAgent semantics are lossless

This would materially improve ReddiAgent by making ADL visibly compatible with the newest filesystem-first production-agent framework, while preserving the core ReddiAgent stance: ADL owns safety and semantics; external frameworks are reviewed targets.
