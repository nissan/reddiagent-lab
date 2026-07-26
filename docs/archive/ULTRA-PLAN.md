# ReddiAgent Lab Ultra Plan

_Created: 2026-05-21_

## Mission

Build the research base, conceptual model, and early specification for ReddiAgent: a portable way to define AI agents as interchangeable models plus executable harnesses, with optional payment and reputation capabilities that can bridge into Reddi Agent Protocol.

## Strategic Outcome

ReddiAgent should help a prosumer answer four questions:

1. What kind of agent am I building?
2. Which model/provider can run it?
3. What harness does it need to operate safely and usefully?
4. How can it pay, get paid, prove work, and build reputation?

## Working Definition

    ReddiAgent = Agent Definition Language + Harness Definition + Payment/Reputation Extension

The Agent Definition Language abstracts model choice. The harness definition captures the operating environment. The payment/reputation extension lets the harness express x402-compatible economic behavior without hard-coding a single rail.

## Phase 0 - Project Setup

Goal: Create the durable workspace and operating loop.

Deliverables:

- Private GitHub repo.
- Initial README.md, STATUS.md, research taxonomy, architecture thesis, and SPDD/OAD kickoff artifact.
- GitHub issue backlog for the first research and design milestones.
- Loop protocol and retrospective template.

Acceptance:

- Repo exists and is private.
- Initial issues exist.
- Local repo is clean after first push.
- docs/LOOP-PROTOCOL.md defines how loops close and update the plan.

## Operating Loop

Work proceeds in short loops anchored to one GitHub issue.

Each loop must:

1. Define objective, artifacts, acceptance checks, assumptions, and risks.
2. Produce the smallest useful research, spec, or prototype artifact.
3. Run a verification gate appropriate to the artifact.
4. Write a retrospective under retrospectives/.
5. Update STATUS.md and any changed plan/spec files before the next loop.

Canonical loop protocol: docs/LOOP-PROTOCOL.md

## Phase 1 - Landscape Research

Goal: Build a structured comparison of how popular frameworks and platforms construct agents.

Research targets:

- Frameworks: LangChain, LlamaIndex, AWS Strands Agents, CrewAI, AutoGen, Semantic Kernel, and newly discovered serious contenders.
- Portability specifications: Open Agent Specification / Agent Spec, Open Agent Format, and other serious manifest standards that can act as import/export targets.
- Platforms: OpenAI, Anthropic/Claude, Google Gemini, AWS Bedrock, and relevant hosted agent products.
- Homebrew/open-source: Ollama, OpenOnion, OpenClaw, Hermes Agent, pi.dev, solve.it/Answer.AI, Python tool-calling patterns.

Comparison dimensions:

- Model abstraction.
- Tool/function interface.
- Memory and data-source model.
- Planning/execution loop.
- State and persistence.
- Deployment/runtime model.
- Observability and debugging.
- Evaluation and guardrails.
- Multi-agent coordination.
- Payments, auth, identity, and reputation hooks.
- Prosumer learning curve.
- Lock-in and portability risks.
- Lossless vs metadata-only mapping for ReddiAgent policy, payment, receipt, source-boundary, and reputation extensions.

Deliverables:

- research/FRAMEWORK-MATRIX.md
- research/PLATFORM-MATRIX.md
- research/HOMEBREW-OPEN-SOURCE-MATRIX.md
- research/FINDINGS.md

## Phase 2 - ReddiAgent Concept Model

Goal: Convert the research into a small, defensible domain model.

Core entities:

- Agent
- ModelProfile
- Harness
- Tool
- Function
- Skill
- DataSource
- Memory
- Policy
- EvalGate
- Runtime
- DeploymentTarget
- PaymentRail
- Receipt
- ReputationSignal
- Identity

Deliverables:

- docs/ARCHITECTURE-THESIS.md
- specs/DOMAIN-MODEL-v0.1.md
- Mermaid diagrams for model/harness/payment boundaries.

## Phase 3 - Agent Definition Language v0.1

Goal: Draft a portable schema that can describe useful agents without binding to one provider.

The schema should describe:

- Model requirements and allowed providers.
- Prompt/instruction layers.
- Tool/function contracts.
- Skill packs.
- Memory/data access.
- Runtime/deployment requirements.
- Evaluation gates.
- Auth and permissions.
- Payment intents and supported rails.
- Receipts and reputation metadata.

Deliverables:

- specs/ADL-v0.1.md
- specs/ADL-v0.1.schema.json
- examples with simple, tool-using, payment-capable, and multi-provider agents.

## Phase 4 - Prosumer Builder Journey

Goal: Turn the abstraction into an educational path.

Journey stages:

- Choose a useful agent job.
- Pick a model strategy.
- Add tools/functions.
- Add data and memory.
- Add policies and evals.
- Run locally.
- Deploy.
- Add payment/reputation.
- Monitor and improve.

Deliverables:

- docs/BUILDER-JOURNEY.md
- examples/tutorial-01-simple-agent.md
- examples/tutorial-02-tool-agent.md
- examples/tutorial-03-paid-agent.md

## Phase 5 - RAP Bridge

Goal: Define how ReddiAgent harnesses can express payment and reputation while RAP handles protocol-level execution.

Design requirements:

- Payment capability is optional.
- Payment intent is rail-neutral.
- Settlement adapters can include Solana, Base, Stripe, other chains, and other x402-compatible rails.
- Receipts should preserve evidence useful for reputation.
- Reputation should attach to agent identity and harness behavior, not only model output.
- x402 paid MCP service patterns should be modeled as an integration layer so builders can start with x402-compatible MCP payment metadata and later adopt Reddi Agent Protocol without rewriting their ADL.
- AP2-like authority/mandate metadata should be kept separate from x402 payment evidence: x402 describes payment proof/response, while authority describes who may spend, under what constraints, and how that authority can be revoked or audited.

Deliverables:

- specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md
- specs/RAP-BRIDGE-v0.1.md

## Phase 6 - Prototype Decision

Goal: Decide what to build first after the research/spec phase.

Candidate prototypes:

- CLI that validates a ReddiAgent definition.
- Generator that emits OpenAI/Anthropic/Gemini/LangChain/LlamaIndex starter code from one ADL file.
- Compatibility reporter and later exporter for Agent Spec JSON/YAML.
- Harness runner for local Python tool-calling agents.
- x402 payment-capable demo agent with rail-neutral config.
- x402/MCP-to-RAP bridge report that shows how a paid MCP service declaration can graduate into RAP.

Recommendation:

After the current spec slice, build the x402/MCP-to-RAP bridge report first. It turns the payment/MCP pattern into a concrete adoption path for Reddi Agent Protocol while staying static and non-runtime.

Then continue with validator/generator work. The bridge proves the economic integration story without binding ReddiAgent to a single runtime or executing payments.

## Open Questions

- Should ReddiAgent be a user-facing product name, developer spec name, or internal lab name?
- How much should ADL resemble existing specs such as OpenAPI, MCP manifests, LangChain templates, or OpenAI tool schemas?
- Should ADL-to-Agent-Spec export be best-effort metadata preservation or a strict fail-on-loss mode by default?
- Which runtime should be the first canonical output target?
- Should payment/reputation metadata be embedded in the core schema or shipped as an extension namespace?
- What minimum x402/AP2/receipt fields make a paid MCP service declaration RAP-ready without authorizing live settlement?
- What minimum workflow makes a prosumer feel successful in under one hour?
