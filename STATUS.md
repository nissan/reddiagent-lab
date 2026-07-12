# STATUS: ReddiAgent Lab
_Last updated: 2026-07-12 10:51 AEST by Loki_

## RESUME FROM HERE

- **Next action:** Wait for Oli QA on draft PR #138 (`feat/rap-bridge-report-137`, head `1d0cd17cda54400fcfc3f159cb68702aadc11593`) for issue #137, then either fix blockers or, if QA passes, mark ready/merge only after normal OAD policy checks. Do not advance to #133 while PR #138 is open.
- **Waiting on:** Nissan to accept the admin collaborator invite if GitHub requires acceptance. Nissan may later choose whether the repo should remain under reddinft or move to an org/user namespace.
- **Last discussed:** Nissan asked on 2026-07-12 to set a 30-minute development/review/approval loop like `openclaw-workspace`, targeting the ReddiAgent/RAP backlog. Draft PR #138 is open and parent verification was posted with no paid/model calls; runtime execution remains blocked.

## Current Phase

**Phase:** Phase 0 - Project setup and research framing  
**Status:** Active  
**Target date:** Initial research pack and ADL v0.1 draft by 2026-05-28.

## Key Files

- Project plan: docs/ULTRA-PLAN.md
- Architecture thesis: docs/ARCHITECTURE-THESIS.md
- Research taxonomy: research/RESEARCH-TAXONOMY.md
- x402/MCP micropayments research note: research/2026-07-08-x402-mcp-micropayments.md
- Initial SPDD/OAD contract: spdd/prompt/0001-project-kickoff.md
- Loop protocol: docs/LOOP-PROTOCOL.md
- Retrospective template: retrospectives/TEMPLATE.md
- Loop 0 retrospective: retrospectives/2026-05-21-loop-0-project-setup.md
- Source map: research/SOURCE-MAP.md
- Framework matrix: research/FRAMEWORK-MATRIX.md
- Platform matrix: research/PLATFORM-MATRIX.md
- Homebrew/open-source matrix: research/HOMEBREW-OPEN-SOURCE-MATRIX.md
- Domain model: specs/DOMAIN-MODEL-v0.1.md
- ADL v0.1: specs/ADL-v0.1.md
- Payment/reputation extension: specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md
- RAP bridge: specs/RAP-BRIDGE-v0.1.md
- Validation guidance: specs/VALIDATION-GUIDANCE-v0.1.md
- Builder journey: docs/BUILDER-JOURNEY.md
- Simple example: examples/simple-agent.yaml
- Tool example: examples/tool-agent.yaml
- MCP read-only example: examples/mcp-readonly-agent.yaml
- Payment example: examples/payment-agent.yaml
- Invalid examples: examples/invalid/
- Provider mapping: specs/PROVIDER-MAPPING-v0.1.md
- Harness lifecycle: specs/HARNESS-LIFECYCLE-v0.1.md
- Eval gates: specs/EVAL-GATES-v0.1.md
- Runtime/deployment: specs/RUNTIME-DEPLOYMENT-v0.1.md
- Security/permissions: specs/SECURITY-PERMISSIONS-v0.1.md
- Observability: specs/OBSERVABILITY-v0.1.md
- Conformance: specs/CONFORMANCE-v0.1.md
- Glossary: docs/GLOSSARY.md
- Roadmap: docs/ROADMAP.md
- Agent Spec compatibility: specs/AGENT-SPEC-COMPATIBILITY-v0.1.md
- Agent Spec mapping: mappings/AGENT-SPEC.md
- Agent Spec compatibility script: scripts/agent_spec_compatibility.py
- Agent Spec compatibility report: tests/AGENT-SPEC-COMPATIBILITY-REPORT.md
- Agent Spec compatibility test: tests/test_agent_spec_compatibility.py
- Agent Spec lossless export fixture: tests/fixtures/agent-spec-lossless-agent.yaml
- Loop 1 retrospective: retrospectives/2026-05-21-loop-1-source-map.md
- Loops 2-8 retrospective: retrospectives/2026-05-21-loops-2-8-foundation.md
- Loops 9-21 retrospective: retrospectives/2026-05-21-loops-9-21-sprint.md
- GitHub: https://github.com/reddinft/reddiagent-lab
- Issues: https://github.com/reddinft/reddiagent-lab/issues
- Issue #1 planning/source map: https://github.com/reddinft/reddiagent-lab/issues/1
- Issue #2 framework research: https://github.com/reddinft/reddiagent-lab/issues/2
- Issue #3 platform research: https://github.com/reddinft/reddiagent-lab/issues/3
- Issue #4 homebrew/open-source research: https://github.com/reddinft/reddiagent-lab/issues/4
- Issue #5 domain model: https://github.com/reddinft/reddiagent-lab/issues/5
- Issue #6 ADL v0.1: https://github.com/reddinft/reddiagent-lab/issues/6
- Issue #7 payment/reputation extension: https://github.com/reddinft/reddiagent-lab/issues/7
- Issue #8 builder journey: https://github.com/reddinft/reddiagent-lab/issues/8
- Issue #9 loop protocol: https://github.com/reddinft/reddiagent-lab/issues/9
- Issue #23 next loop / ADL JSON Schema: https://github.com/reddinft/reddiagent-lab/issues/23
- Issue #25 Level 0 report: https://github.com/reddinft/reddiagent-lab/issues/25
- Issue #26 local runner plan: https://github.com/reddinft/reddiagent-lab/issues/26
- Issue #27 local runner skeleton: https://github.com/reddinft/reddiagent-lab/issues/27
- Issue #28 tool registry: https://github.com/reddinft/reddiagent-lab/issues/28
- Issue #29 smoke validation: https://github.com/reddinft/reddiagent-lab/issues/29
- Issue #30 compatibility report: https://github.com/reddinft/reddiagent-lab/issues/30
- Issue #31-#36 target mappings: https://github.com/reddinft/reddiagent-lab/issues/31
- Issue #37 MCP mapping: https://github.com/reddinft/reddiagent-lab/issues/37
- Issue #38 x402 dry-run receipt: https://github.com/reddinft/reddiagent-lab/issues/38
- Issue #39 reputation signals: https://github.com/reddinft/reddiagent-lab/issues/39
- Issue #40-#41 tutorials: https://github.com/reddinft/reddiagent-lab/issues/40
- Issue #42 repository index: https://github.com/reddinft/reddiagent-lab/issues/42
- Issue #43 sprint synthesis: https://github.com/reddinft/reddiagent-lab/issues/43
- Issue #44 next loop / Level 1 traces: https://github.com/reddinft/reddiagent-lab/issues/44
- Issue #73 next loop / snapshots: https://github.com/reddinft/reddiagent-lab/issues/73
- Issue #110 next loop / validation error formatter: https://github.com/reddinft/reddiagent-lab/issues/110
- Issue #131 next loop / local tool registry execution fixture: https://github.com/reddinft/reddiagent-lab/issues/131
- Issue #132 static ADL to A2A Agent Card export: https://github.com/reddinft/reddiagent-lab/issues/132
- Issue #133 AP2/x402 mandate mapping: https://github.com/reddinft/reddiagent-lab/issues/133
- Issue #134 agentskills.io skill package alignment: https://github.com/reddinft/reddiagent-lab/issues/134
- Issue #135 static MCP runtime handoff package: https://github.com/reddinft/reddiagent-lab/issues/135
- Issue #136 Prosumer Builder MVP skeleton: https://github.com/reddinft/reddiagent-lab/issues/136
- Issue #137 x402/MCP-to-RAP bridge report: https://github.com/reddinft/reddiagent-lab/issues/137
- Loops 104-128 retrospective: retrospectives/2026-05-23-loops-104-128-tool-fixture.md
- Loops 129-153 retrospective: retrospectives/2026-05-23-loops-129-153-denied-tools.md
- Loops 154-178 retrospective: retrospectives/2026-05-23-loops-154-178-denial-guidance.md
- Loops 179-203 retrospective: retrospectives/2026-05-23-loops-179-203-source-check.md
- Loops 204-228 retrospective: retrospectives/2026-05-23-loops-204-228-negative-source-check.md
- Loops 229-253 retrospective: retrospectives/2026-05-23-loops-229-253-source-guidance.md
- Loops 254-278 retrospective: retrospectives/2026-05-23-loops-254-278-completion-semantics.md
- Loops 279-303 retrospective: retrospectives/2026-05-24-loops-279-303-conformance-report.md
- Loops 304-328 retrospective: retrospectives/2026-05-24-loops-304-328-fail-on-required-gate.md
- Loops 329-353 retrospective: retrospectives/2026-05-24-loops-329-353-cli-usage-matrix.md
- Loops 354-378 retrospective: retrospectives/2026-05-24-loops-354-378-readiness-bundle.md
- Loops 379-403 retrospective: retrospectives/2026-05-24-loops-379-403-mcp-adapter-shape.md
- Loops 404-428 retrospective: retrospectives/2026-05-24-loops-404-428-mcp-source-check.md
- Loops 429-453 retrospective: retrospectives/2026-05-24-loops-429-453-mcp-server-resolution.md
- Loops 454-478 retrospective: retrospectives/2026-05-24-loops-454-478-mcp-capability-policy.md
- Loops 479-503 retrospective: retrospectives/2026-05-24-loops-479-503-mcp-readiness-evidence.md
- Loops 504-528 retrospective: retrospectives/2026-05-24-loops-504-528-mcp-release-checklist.md
- Loops 529-553 retrospective: retrospectives/2026-05-27-loops-529-553-mcp-adapter-contract.md
- Loops 554-578 retrospective: retrospectives/2026-05-27-loops-554-578-mcp-adapter-error-semantics.md
- Loops 579-603 retrospective: retrospectives/2026-05-30-loops-579-603-mcp-adapter-aggregation.md
- Loops 604-628 retrospective: retrospectives/2026-05-31-loops-604-628-agent-spec-compatibility.md
- Loops 629-653 retrospective: retrospectives/2026-06-08-loops-629-653-agent-spec-fail-on-loss-export.md
- Tool execution fixture report: tests/TOOL-EXECUTION-FIXTURE-REPORT.md
- CLI usage matrix: tests/CLI-USAGE-MATRIX.md
- Local runner readiness bundle: docs/LOCAL-RUNNER-READINESS-BUNDLE.md
- MCP readiness release checklist: docs/MCP-READINESS-RELEASE-CHECKLIST.md
- MCP adapter shape report: tests/MCP-ADAPTER-SHAPE-REPORT.md
- MCP adapter contract report: tests/MCP-ADAPTER-CONTRACT-REPORT.md
- MCP adapter error semantics report: tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md
- MCP adapter aggregation report: tests/MCP-ADAPTER-AGGREGATION-REPORT.md
- MCP adapter source-check report: tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md
- MCP server resolution report: tests/MCP-SERVER-RESOLUTION-REPORT.md
- MCP capability policy report: tests/MCP-CAPABILITY-POLICY-REPORT.md
- MCP readiness evidence report: tests/MCP-READINESS-EVIDENCE-REPORT.md
- Agent Spec compatibility report: tests/AGENT-SPEC-COMPATIBILITY-REPORT.md
- MCP adapter readiness script: scripts/adapter_readiness.py
- MCP adapter contract script: scripts/mcp_adapter_contract_check.py
- MCP adapter error semantics script: scripts/mcp_adapter_error_semantics_check.py
- MCP adapter aggregation script: scripts/mcp_adapter_aggregation_check.py
- MCP adapter source-check script: scripts/mcp_adapter_source_check.py
- MCP server resolution script: scripts/mcp_server_resolution_check.py
- MCP capability policy script: scripts/mcp_capability_policy_check.py
- MCP readiness evidence script: scripts/mcp_readiness_evidence_check.py
- Agent Spec compatibility script: scripts/agent_spec_compatibility.py

## Key Decisions

- 2026-05-21: Create reddiagent-lab as a private GitHub-backed project separate from Reddi Agent Protocol to avoid mixing protocol settlement work with agent-construction research.
- 2026-05-21: Treat an agent as model definition plus harness definition plus settlement/reputation extension; model and harness abstractions are first-class outputs.
- 2026-05-21: GitHub issues are the task-tracking source of truth for this project; local STATUS.md remains OpenClaw's operational resume truth.
- 2026-05-21: x402/RAP integration belongs in ReddiAgent as an optional harness capability that can resolve to Solana, Base, Stripe, other chains, or any future x402-supported rail.
- 2026-05-21: Initial private GitHub repo created at reddinft/reddiagent-lab with eight seed issues and Nissan invited as admin collaborator.
- 2026-05-21: Work will proceed in issue-anchored loops; every loop closes with a retrospective, STATUS.md update, and plan/spec adjustments if assumptions changed.
- 2026-05-21: Research tiers set: deep dive, scan, watchlist. Deep dives start with LangChain/LangGraph, OpenAI Agents SDK, LlamaIndex, AWS Strands Agents, Anthropic, Gemini, OpenClaw, and regular Python tool-calling.
- 2026-05-21: Foundation pass decided the harness is the main product surface; the model is a replaceable dependency; payment/reputation remains an extension namespace until core ADL stabilizes.
- 2026-05-21: After 20-loop sprint, next implementation step is validator before runner; provider adapters start as compatibility reports; payment remains dry-run/intent-first until receipt and budget policy enforcement exist.
- 2026-05-21: ADL v0.1 now has JSON Schema validation and all three examples pass Level 0 conformance. Local dry-run runner works for simple/tool examples. Next step is Level 1 dry-run conformance with deterministic traces.
- 2026-05-21: simple-agent and tool-agent now satisfy Level 1 local dry-run conformance with deterministic traces. Provider compatibility and x402 receipts are still dry-run/report-only.
- 2026-05-22: Snapshot tests now cover simple/tool traces, provider compatibility, and payment dry-run receipt. Schema tightened policy/eval types. Next step is builder-facing validation error formatting.
- 2026-05-22: Validation now defaults to builder-facing guidance while raw schema output and JSON guidance remain available. The same guidance is used by local runner validation failures.
- 2026-05-22: Next implementation step is safe local tool execution via fixtures; do not add external network/tool execution or live payment behavior yet.
- 2026-05-23: Safe local tool execution fixture landed for `search_docs`. Execution is opt-in with `--execute-tools`, uses only project-owned deterministic fixtures, requires fixture calls to reference declared tools, emits `tool.executed`, and reports `networkAccess=false` and `paymentAccess=false`. Real external tools, MCP, HTTP, shell, credentials, messaging, and live payments remain blocked.
- 2026-05-23: Denied tool fixture coverage landed. `--allow-denied-tools` reports undeclared and unsupported local fixture calls as `status=denied` with `tool.denied` trace events; strict mode still fails with exit code 2. Unsafe examples are schema-valid runtime-denied fixtures under `examples/unsafe/`.
- 2026-05-23: Builder-facing denied-tool guidance landed. Strict denied calls now render `DENIED` guidance with problem, safety rationale, repair snippet, and spec reference; allowed denial-reporting mode embeds the same guidance in denied result JSON. Relative ADL paths are handled correctly in runtime error rendering.
- 2026-05-23: Positive source-check fixture coverage landed. Successful local fixture outputs now get `sourceChecks` and `source.checked`; `search_docs` passes only when returned title and URL match the approved in-repo source list. Next proof should cover failing source-check output.
- 2026-05-23: Negative source-check fixture coverage landed. `unsafe_source_docs` executes successfully as a deterministic local fixture but returns an unapproved title/URL, causing `sourceChecks.status=fail` and a `source.checked` failure trace event. Source trust remains independent from fixture execution success.
- 2026-05-23: Builder-facing source-check guidance landed. Failed source checks now include repair guidance with problem, safety rationale, fix, minimal approved-output snippet, and `specs/DATA-SOURCE-CONTRACT-v0.1.md` reference. Passing source checks and `source.checked` trace events remain compact.
- 2026-05-24: Source-check completion semantics landed. Local dry-run reports now distinguish runner transport success from required gate completion via `completion.transportStatus`, `completion.requiredGateStatus`, `completion.status`, and `sourceCheckSummary.requiredFailureCount`; failed required gates now make `task.dry_run_completed.status=fail`.
- 2026-05-24: Level 1 conformance now includes local fixture gate completion evidence. `tests/test_level1.py` asserts approved source pass, unapproved source fail, and allowed denied-tool fail semantics; the Level 1 report documents the same evidence.
- 2026-05-24: `--fail-on-required-gate` landed for local-python dry-runs. Default behavior remains report-first with exit code 0 on successful transport; automation can opt into exit code 3 when required gates fail while still receiving JSON diagnostics on stdout.
- 2026-05-24: CLI usage matrix landed and is covered by smoke validation. Local-python runner outcomes are now distinct and tested: validation failure exits 1, strict runtime denial exits 2, report-mode denied/source failures exit 0 with `completion.status=fail`, and required-gate automation failure exits 3 with JSON diagnostics preserved.
- 2026-05-24: Local runner readiness bundle landed. `docs/LOCAL-RUNNER-READINESS-BUNDLE.md` is now the evidence checklist before any real external tool path, MCP execution, network access, shell execution, credential access, messaging, filesystem mutation, or live payment behavior is considered; `tests/test_readiness_bundle.py` guards it in smoke validation.
- 2026-05-24: Read-only MCP adapter shape landed. `examples/mcp-readonly-agent.yaml` passes adapter readiness, `examples/unsafe/mcp-live-server-fixture.yaml` fails embedded `serverUrl`/`command`/`env`, and `scripts/adapter_readiness.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server resolution or invocation is implemented.
- 2026-05-24: Deterministic MCP adapter output source checks landed. `tests/fixtures/mcp-approved-output.json` passes `approved-source-output`; `tests/fixtures/mcp-unapproved-output.json` fails with source-check guidance; `scripts/mcp_adapter_source_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. MCP output is not trusted by adapter type.
- 2026-05-24: Static MCP server-resolution checks landed. `tests/fixtures/mcp-server-registry-approved.json` passes; `tests/fixtures/mcp-server-registry-empty.json` fails missing `serverRef`; `tests/fixtures/mcp-server-registry-live.json` fails live resolution fields; `scripts/mcp_server_resolution_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server is resolved or invoked.
- 2026-05-24: Static MCP capability-policy checks landed. `tests/fixtures/mcp-capability-policy-approved.json` passes; `tests/fixtures/mcp-capability-policy-empty.json` fails missing policy; `tests/fixtures/mcp-capability-policy-overbroad.json` fails `network.fetch`/`payment.spend` and live access flags; `scripts/mcp_capability_policy_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`.
- 2026-05-24: Static MCP readiness trace/evidence checks landed. `tests/fixtures/mcp-readiness-evidence-pass.json` passes; `tests/fixtures/mcp-readiness-evidence-fail.json` fails missing server-resolution evidence, live-access claims, and mismatched completion status; `scripts/mcp_readiness_evidence_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server is resolved or invoked.
- 2026-05-24: Static MCP readiness release checklist landed. `docs/MCP-READINESS-RELEASE-CHECKLIST.md` aggregates adapter shape, source checks, static server registry, capability policy, readiness evidence, smoke validation, and explicit non-goals; `tests/test_mcp_readiness_release.py` guards required references and boundary language. No MCP server is resolved or invoked.
- 2026-05-27: Static MCP adapter contract checks landed. `tests/fixtures/mcp-adapter-contract-approved.json` passes; `tests/fixtures/mcp-adapter-contract-malformed.json` fails empty identity, embedded live URL, access claims, and missing output URL; `scripts/mcp_adapter_contract_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server is resolved or invoked.
- 2026-05-27: Static MCP adapter error semantics landed. `tests/fixtures/mcp-adapter-error-approved.json` passes; `tests/fixtures/mcp-adapter-error-leaky.json` fails success-like status, output payload leakage, live server fields, invocation claims, raw stack leakage, unreviewed error code, and ambiguous retryability; `scripts/mcp_adapter_error_semantics_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server is resolved or invoked.
- 2026-05-30: Static MCP adapter aggregation landed. `tests/fixtures/mcp-adapter-aggregation-approved.json` passes; `tests/fixtures/mcp-adapter-aggregation-leaky.json` fails live aggregation mode, access claims, duplicate result IDs, pass/error mixing, raw runtime leakage, and mismatched aggregate completion counts; `scripts/mcp_adapter_aggregation_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`. No MCP server is resolved or invoked.
- 2026-05-31: Agent Spec integration recommendation added to current development plan. ADL remains the canonical source of truth; Open Agent Specification / Agent Spec is now a Level 2 report-only compatibility target. First slice should document static mapping, generate compatibility reports for simple/payment examples, and preserve Reddi policy/payment/receipt/reputation/source-boundary/MCP semantics as namespaced metadata or explicit unsupported warnings. No Agent Spec runtime or adapter execution is approved.
- 2026-05-31: Agent Spec report-only compatibility slice landed. `scripts/agent_spec_compatibility.py` maps `examples/simple-agent.yaml` and `examples/payment-agent.yaml` into static Agent Spec-compatible review documents, distinguishes `supported` from `lossless`, preserves Reddi sections as metadata-only, and hard-codes `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`. Guard test and smoke validation pass. No Agent Spec runtime or adapter execution is approved.
- 2026-06-08: Strict Agent Spec fail-on-loss export landed. `scripts/agent_spec_compatibility.py --export-agent-spec` refuses lossy ADL with exit code 3 and diagnostics, emits JSON/YAML mapped review documents only for lossless inputs, and keeps `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`. No Agent Spec runtime or adapter execution is approved.
- 2026-07-08: Ingested Peter Robinson's "AI Agent Micropayments for MCP Services using x402" video/slides as research. Decision: treat x402 as payment evidence and rail vocabulary, AP2/mandates as authority constraints, and ReddiAgent receipts/reputation as the work-plus-payment evidence layer. This is spec/export input only; no MCP server, facilitator, wallet, rail, or runtime invocation is approved.
- 2026-07-08: Added `specs/RAP-BRIDGE-v0.1.md` and wired the plan around an x402/MCP-to-RAP integration layer. Decision: ReddiAgent should make builders who implement x402 paid MCP metadata RAP-ready through static bridge reports, with x402 as payment evidence, AP2-like mandates as spend authority, and receipts/reputation as delivered-work evidence. No live RAP/MCP/payment execution is approved.
- 2026-07-08: Prioritized the static x402/MCP-to-RAP bridge report as the first build after the current spec slice. Validator/generator work remains important, but the bridge now leads the immediate post-spec roadmap because it creates the cleanest adoption path from video-style paid MCP implementations into Reddi Agent Protocol.
- 2026-07-12: Created issue #137 and scheduled a dedicated 30-minute ReddiAgent/RAP backlog lane loop. Queue is #137, then #133, #132, #135, #134, and #136 if still appropriate. The loop is OAD-gated, PR/review/approval based, and report-only/static by policy; no live MCP, runtime, wallet, facilitator, payment rail, settlement, credential, production gateway config, external-service mutation, or paid/model test call is approved.

## Blockers & Flags

- [ ] Nissan admin collaborator invite is pending acceptance if GitHub requires it.
- [ ] Confirm final GitHub namespace if reddinft/reddiagent-lab should later move under nissan or another org.
- [ ] Decide whether to add a separate Notion/Plane layer; current user direction is GitHub-first.

## Agent Notes

- Keep RAP terminology precise: product name is Reddi Agent Protocol; user package is reddi-x402.
- Do not turn this repo into a RAP implementation repo. Its primary deliverable is a research-backed agent definition/harness abstraction and prosumer builder journey.
