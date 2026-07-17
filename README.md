# ReddiAgent Lab

ReddiAgent Lab is the research and design workspace for helping prosumers understand, define, build, run, and improve AI agents.

For a human-readable project entrypoint, start with `docs/REDDIAGENT-VISION-ROADMAP.md`. For the high-level system view, read `docs/REDDIAGENT-ARCHITECTURE.md`. For a builder/reviewer guide to the open specs, use `docs/OPEN-SPECS-EXPLAINER.md`. For structured review intake, use `docs/OPEN-SPEC-REVIEW-INTAKE.md` and `.github/ISSUE_TEMPLATE/open-spec-review.md`. For the draft public-review blog post, use `docs/blog/2026-07-18-reddiagent-open-specs-call-for-review.md`. For durable architectural decisions, use the ADR register at `docs/adr/0000-adr-index.md`. For the protected publishable docs package plan, use `docs/PROTECTED-DOCS-PACKAGE.md`.

It is adjacent to Reddi Agent Protocol, but intentionally separate:

- ReddiAgent Lab studies the agent construction layer: model abstraction, harness definition, tools, skills, data, deployment, evaluation, and builder education.
- Reddi Agent Protocol focuses on payment, reputation, settlement, and protocol-level economic coordination, starting with Solana and reddi-x402.

## Core Thesis

An agent can be modeled as:

    Agent = model definition + harness definition + settlement/reputation extension

The model definition should make OpenAI, Anthropic, Gemini, Ollama, hosted open models, and future model providers interchangeable at the capability and constraint layer.

The harness definition should describe the operating system around the model: tools, functions, skills, memory, data sources, policies, eval gates, deployment points, auth, observability, recovery behavior, and payment/reputation hooks.

## Initial Workstreams

1. Framework research: LangChain, LlamaIndex, AWS Strands Agents, CrewAI, AutoGen, Semantic Kernel, and emergent agent frameworks.
2. Platform-native research: OpenAI, Anthropic/Claude, Google Gemini, and the patterns each platform promotes for agent construction.
3. Homebrew/open-source research: Ollama, OpenOnion, OpenClaw, Hermes Agent, pi.dev, solve.it/Answer.AI, regular Python tool-calling, and other notable tools.
4. Agent Definition Language: a portable schema for model and harness definitions.
5. Builder journey: a prosumer learning path from agent idea to local prototype, hosted deployment, evaluation, and monetization.
6. x402/RAP bridge: payment intents, settlement rails, receipts, identity, reputation, and policy constraints as optional harness capabilities.

## Repo Operating Model

- GitHub issues are the source of truth for planned work.
- STATUS.md is the local OpenClaw resume file.
- Research notes live in research/.
- Design/spec artifacts live in docs/, specs/, and spdd/prompt/.
- Keep RAP-specific implementation in the RAP repo unless the work belongs to the agent definition/harness abstraction.

## Local Validation

Validate the current examples:

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py

Validation failures default to builder-facing guidance. Use --format raw for schema-debug output or --format json for future UI/CI integration.
