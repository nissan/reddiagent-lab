# ReddiAgent Architecture Thesis

_Created: 2026-05-21_

## Thesis

Most agent frameworks mix three concerns that should be separable:

1. The model that reasons or generates.
2. The harness that turns model calls into useful, stateful work.
3. The economic layer that lets agents pay, get paid, prove work, and build reputation.

ReddiAgent should separate these concerns so builders can define an agent once, then run it across different providers, frameworks, and payment rails where feasible.

## Boundary Model

    Agent
    - Model definition
    - Harness definition
    - Extensions
      - Payment
      - Reputation
      - Identity
      - Evidence / receipts

## Model Definition

The model definition should describe what the agent needs, not which provider must supply it.

Candidate fields:

- capability class: chat, reasoning, code, vision, audio, embedding, reranking.
- context window.
- tool/function calling support.
- structured output support.
- streaming support.
- latency/cost envelope.
- safety/moderation requirements.
- allowed providers/models.
- fallback policy.

## Harness Definition

The harness definition is the main design surface. It should describe:

- instructions and prompt layers.
- tool/function contracts.
- skills and reusable capabilities.
- memory and persistence.
- data sources and retrieval.
- runtime state.
- execution loop.
- policies and permissions.
- eval gates and stop conditions.
- deployment targets.
- observability and logs.
- recovery and retry behavior.

## Payment/Reputation Extension

Payment should be expressed as a harness capability:

- payment intents.
- budget policies.
- settlement rail preferences.
- supported x402 facilitators.
- receipts.
- refund/dispute metadata.
- reputation signals.

This lets ReddiAgent work with Reddi Agent Protocol without assuming every agent must settle on Solana. RAP can start with Solana payment and reputation, while the ReddiAgent abstraction remains rail-neutral across Solana, Base, Stripe, and future x402-compatible rails.

## Research Question

For every framework or platform we study, map:

- what it treats as the model boundary.
- what it treats as the harness boundary.
- what is explicit versus implicit.
- where it creates lock-in.
- what a prosumer has to learn.
- what ReddiAgent should abstract, adopt, or avoid.

