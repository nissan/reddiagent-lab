# Pitch Demo Refresh

Issue: #277

## Goal

Refresh the public ReddiAgent demo so it sells the story before it exposes the evidence.
The page and video should be persona-led, calmer, and easier to pitch while staying truthful
about the current boundary: static/local/dry-run evidence only.

## Positioning

ReddiAgent is the pre-runtime review layer for agent systems.

Define the agent once in ADL, validate the harness, inspect what export targets preserve,
review pinned evidence, and block unsafe claims before providers, MCP, payments,
infrastructure, or mainnet are touched.

## Primary Personas

### Technical founders and builders

Pain: The demo usually starts after a runtime exists, when permissions and loss are already
hard to review.

Promise: Start from a reviewable ADL contract. Validate the agent and understand export
readiness before writing target-specific code.

CTA: Try ADL validation.

### Agent framework maintainers

Pain: Framework exports often hide semantic loss behind generated files.

Promise: Treat each framework and provider surface as a compatibility target. Make loss,
metadata-only paths, and blocked generation explicit.

CTA: Inspect the builder report.

### Protocol reviewers and early partners

Pain: Payment, MCP, reputation, runtime, and infrastructure claims are risky when they are
shown before evidence and rollback posture are visible.

Promise: Review pinned evidence, boundary flags, dry-run transcripts, rollback cues, and
fail-closed cases before activation.

CTA: Open beta review.

## Page Structure

1. Hero: story-led value proposition, embedded walkthrough, quiet trust strip.
2. Persona cards: builder, maintainer, reviewer.
3. Story steps: describe, validate, compare, review.
4. Proof index: builder report, ADL validation UI, beta review UI, verification reports.
5. Safety boundary: explicit no-runtime/no-provider/no-MCP/no-payment/no-mainnet list.

## Video Story Arc

Framework: Problem -> Persona -> Proof -> Boundary -> CTA.

1. Open with the problem: most agent demos start too late.
2. Introduce Maya, a builder preparing a partner demo.
3. Show her writing one ADL instead of hand-rolling vendor-specific scripts.
4. Validate the ADL and catch missing harness fields before generation.
5. Compare export targets and see which semantics survive.
6. Switch to the reviewer perspective: pinned evidence, rollback, fail-closed denials.
7. Close with the honest claim: not live execution, but proof that unsafe claims are blocked
   before runtime.

## Voiceover Draft

Most agent demos start too late.

They show something running before anyone can inspect what the agent was allowed to do,
what the target preserved, or what should have been blocked.

Meet Maya. She is preparing an agent for a partner review. Before she talks about runtime,
payments, MCP, or deployment, she needs one thing: a contract everyone can inspect.

That contract is ADL.

In ReddiAgent, the agent starts as a declarative definition: model needs, tools, data,
policies, eval gates, traces, runtime intent, and optional payment or reputation metadata.

Maya validates the ADL first. If a required harness field is missing, the demo stops with a
specific fix instead of generating unsafe code.

Then she checks export readiness. Agent Spec, A2A Agent Card, Agent Skills, provider
reports, RAP bridge metadata, and Vercel eve are treated as targets. ReddiAgent shows what
is report-ready, what is metadata-only, and what is blocked before generation.

Now the reviewer has a surface too. The beta review UI ties the candidate to pinned evidence,
boundary flags, dry-run transcripts, rollback cues, and fail-closed denial cases.

So the claim is deliberately narrow.

This public demo does not activate a runtime, call providers, invoke MCP, settle payments,
start infrastructure, or touch mainnet.

It proves the safer first milestone: describe the agent, inspect the harness, review target
loss, and block unsafe claims before anything risky runs.

## Audio Options

Preferred draft path:

- `scripts/speak.py` executed directly, so its Kokoro virtualenv/shebang is used.
- Suggested voices: `sara` for warm storytelling, `loki` for founder/operator narration,
  `belle` for more polished British narration.
- Zero external spend once the local model is available.

Fallback path:

- macOS `say` enhanced voices such as `Samantha`, only when Kokoro fails.
- This is acceptable for internal drafts but too robotic for the public final.

Approval-gated polish:

- ElevenLabs or Deepgram can produce more human public narration, but they are cloud services
  and should be treated as explicit approval/spend lanes before use.

## Guardrails

Do not claim live runtime activation, Docker/Surfpool/Coolify start, hosted mutation,
credential access/storage, provider/model product calls, live MCP invocation, devnet/mainnet,
wallet/payment/facilitator/settlement access, package publishing, production gateway mutation,
or production readiness.
