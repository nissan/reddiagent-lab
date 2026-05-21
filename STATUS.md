# STATUS: ReddiAgent Lab
_Last updated: 2026-05-22 01:43 AEST by Loki_

## RESUME FROM HERE

- **Next action:** Start issue #110 to build a validation error formatter that converts schema errors into builder-facing guidance, starting from examples/invalid/missing-instructions.yaml.
- **Waiting on:** Nissan to accept the admin collaborator invite if GitHub requires acceptance. Nissan may later choose whether the repo should remain under reddinft or move to an org/user namespace.
- **Last discussed:** Loops 64-83 completed persistent snapshots, snapshot tests, schema tightening, invalid-example validation, data/memory/skill/deployment contracts, positioning docs, and repo health check.

## Current Phase

**Phase:** Phase 0 - Project setup and research framing  
**Status:** Active  
**Target date:** Initial research pack and ADL v0.1 draft by 2026-05-28.

## Key Files

- Project plan: docs/ULTRA-PLAN.md
- Architecture thesis: docs/ARCHITECTURE-THESIS.md
- Research taxonomy: research/RESEARCH-TAXONOMY.md
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
- Builder journey: docs/BUILDER-JOURNEY.md
- Simple example: examples/simple-agent.yaml
- Tool example: examples/tool-agent.yaml
- Payment example: examples/payment-agent.yaml
- Provider mapping: specs/PROVIDER-MAPPING-v0.1.md
- Harness lifecycle: specs/HARNESS-LIFECYCLE-v0.1.md
- Eval gates: specs/EVAL-GATES-v0.1.md
- Runtime/deployment: specs/RUNTIME-DEPLOYMENT-v0.1.md
- Security/permissions: specs/SECURITY-PERMISSIONS-v0.1.md
- Observability: specs/OBSERVABILITY-v0.1.md
- Conformance: specs/CONFORMANCE-v0.1.md
- Glossary: docs/GLOSSARY.md
- Roadmap: docs/ROADMAP.md
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

## Blockers & Flags

- [ ] Nissan admin collaborator invite is pending acceptance if GitHub requires it.
- [ ] Confirm final GitHub namespace if reddinft/reddiagent-lab should later move under nissan or another org.
- [ ] Decide whether to add a separate Notion/Plane layer; current user direction is GitHub-first.

## Agent Notes

- Keep RAP terminology precise: product name is Reddi Agent Protocol; user package is reddi-x402.
- Do not turn this repo into a RAP implementation repo. Its primary deliverable is a research-backed agent definition/harness abstraction and prosumer builder journey.
