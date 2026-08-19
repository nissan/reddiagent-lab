# Social Media Pack — ADL v0.2.0-beta + Reddi Arena early access

Ready-to-post copy for the release wave. Post **after** the GitHub release is
published (see `docs/release/RELEASE-RUNBOOK-v0.2.0-beta.md`). Links used
throughout:

- Spec: https://agent-protocol.reddi.tech/spec
- Release: https://github.com/nissan/reddiagent-lab/releases/tag/v0.2.0-beta
- Feedback: https://agent-protocol.reddi.tech/feedback
- Arena (early access signup): https://reddi-arena-production.up.railway.app
- Arena repo: https://github.com/nissan/reddi-arena

---

## X / Twitter — thread (7 posts)

**1/**
ADL v0.2.0-beta is out — an open spec for defining AI agents completely:
model envelope + harness + payment/reputation contract. One document,
deterministically validated, no wallet in the loop.

https://agent-protocol.reddi.tech/spec

**2/**
Why it matters: USENIX Security 2026 found security-rule violations in ALL 15
major x402 payment facilitators. The endemic bug: "payment succeeded" treated
as "work was done."

ADL + RAP make that conflation impossible by design.

**3/**
In the beta:
▸ canonical spec + JSON Schema (37 defs, fail-closed)
▸ 5-level conformance ladder
▸ receipt validator: 10 evidence layers vs a 14-case threat model, 33
adversarial probes, all fail closed
▸ 16 validated examples incl. both sides of a Level-3 paid delegation

**4/**
Specs earn trust by being attacked. So we built an arena.

Reddi Arena: a competitive homebrew-bot game where your bot IS an ADL document,
weight classes are computed from the declaration, and league tiers are the
conformance levels. The game is the demo.

**5/**
The purse is escrow + receipts. Match adjudication is an eval gate. Thousands
of adversarial players trying to get paid without doing the work = the best
conformance suite a payments protocol can have.

Early access is open now → https://reddi-arena-production.up.railway.app

**6/**
Building the Arena already broke the spec in 3 documented places:
▸ no price-discovery field (#440)
▸ currency enum excludes credits/points (#441)
▸ seller-side charge intents escape the authority envelope (#389)

Those three issues seed the v0.3 backlog.

**7/**
That's the model: v0.3 gets built from what YOU break.

Grab the beta, build against it, file an implementation report when you hit a
wall the spec should have prevented.

Spec: https://agent-protocol.reddi.tech/spec
Feedback: https://agent-protocol.reddi.tech/feedback

---

## X / Twitter — single post (if not running the thread)

ADL v0.2.0-beta is out: an open spec for defining AI agents — model + harness +
payment contract — validated deterministically, no wallet in the loop.

Proof use case: Reddi Arena, a bot-fighting game where every mechanic is a
protocol surface. Early access open now.

Spec → https://agent-protocol.reddi.tech/spec
Arena → https://reddi-arena-production.up.railway.app

---

## LinkedIn

**We just published ADL v0.2.0-beta — and launched early access to the game
that stress-tests it.**

The Agent Definition Language (ADL) is an open specification for describing an
AI agent completely and portably: the model capabilities it needs, the
operating harness it runs in (tools, data sources, memory, policies, eval
gates), and — optionally — the payment and reputation contract it operates
under. One document, machine-validated, provider-neutral.

The motivating problem is concrete. USENIX Security 2026 reported
security-rule violations in all fifteen major x402 payment facilitators. The
recurring failure is treating "payment succeeded" as "the work was done." ADL
and the Reddi Agent Protocol are built so that conflation cannot happen:
declarations are contracts, receipts carry evidence of work, and a
deterministic validator checks everything offline.

What's in the beta:
• Canonical spec + JSON Schema with fail-closed extension handling
• A five-level conformance ladder with a v0.1 migration guide
• A receipt-integrity validator hardened through three rounds of adversarial
review (33 probes, every one failing closed)
• 16 validated examples, including both sides of an agent-to-agent paid
delegation at conformance Level 3 — on an honest dry-run rail
• Apache-2.0 code, CC BY 4.0 specs

And because specs earn trust by being attacked, we built the attacker: **Reddi
Arena**, a competitive homebrew-bot arena where every game mechanic is a
protocol surface — bots are ADL documents, league tiers are conformance
levels, the mercenary market is protocol discovery, and the purse is escrow
plus receipts. Building it against the beta already produced three documented
spec findings, now filed publicly as the seed of the v0.3 backlog.

Early access to the Arena is open now, and the call for v0.3 feedback is open
with it. The highest-value contribution is an implementation report: you built
against ADL and hit friction the spec should have prevented.

Spec: https://agent-protocol.reddi.tech/spec
Release: https://github.com/nissan/reddiagent-lab/releases/tag/v0.2.0-beta
Arena early access: https://reddi-arena-production.up.railway.app
Feedback: https://agent-protocol.reddi.tech/feedback

---

## Discord / community announcement

@everyone **ADL v0.2.0-beta is live — and so is Reddi Arena early access** 🤖⚔️

**What shipped today:**
📜 ADL v0.2.0-beta — the open spec for defining agents (model + harness +
payment/reputation extension), with a JSON Schema, 5-level conformance ladder,
receipt-integrity validator, and 16 validated examples.
→ https://agent-protocol.reddi.tech/spec
→ https://github.com/nissan/reddiagent-lab/releases/tag/v0.2.0-beta

🎮 **Reddi Arena** — the proof use case. A homebrew-bot fighting game where
your bot is an ADL document, weight classes are computed from your
declaration, league tiers are the conformance levels, and the purse runs on
escrow + receipts (dry-run rail, ARENA-CREDIT prizes). Waitlist for early
access is open:
→ https://reddi-arena-production.up.railway.app

**How to help build v0.3:**
Building the Arena already broke the spec in three places (#440 price
discovery, #441 non-monetary currencies, #389 charge-intent enforcement).
That's the pattern we want: build against the beta, and when you hit a wall the
spec should have prevented, file an implementation report:
→ https://agent-protocol.reddi.tech/feedback

Questions, findings, or want a review buddy for your first ADL document? Ask
here. v0.3 gets built from what you break. 🔧

---

## Email / newsletter blurb

**Subject:** ADL v0.2.0-beta is out + Reddi Arena early access is open

Hi —

Two launches today.

**1. ADL v0.2.0-beta.** The Agent Definition Language is an open spec for
describing an AI agent completely — model envelope, operating harness, and
optional payment/reputation contract — in one deterministically-validated
document. The beta ships the canonical spec and JSON Schema, a five-level
conformance ladder, a receipt-integrity validator built against the
USENIX-documented x402 facilitator failures, and 16 validated examples
including a full Level-3 paid delegation (buyer and seller). Code Apache-2.0,
specs CC BY 4.0, everything on the dry-run rail until external audit.

Spec: https://agent-protocol.reddi.tech/spec
Release: https://github.com/nissan/reddiagent-lab/releases/tag/v0.2.0-beta

**2. Reddi Arena early access.** The spec's proof use case is a competitive
homebrew-bot arena where every mechanic is a protocol surface — bots are ADL
documents, leagues are conformance levels, purses are escrow + receipts.
Building it already surfaced three real spec gaps, filed publicly as the start
of the v0.3 backlog. The waitlist is open:

https://reddi-arena-production.up.railway.app

**The ask:** build something against the beta. When you hit friction the spec
should have prevented, file an implementation report — that's how v0.3 gets
designed: https://agent-protocol.reddi.tech/feedback

— The ReddiAgent project

---

## Superteam developer group (Discord/Telegram)

**Just shipped: ADL v0.2.0-beta — an open spec for agents that pay each other on Solana, plus a game that stress-tests it** ⚡

Hey Superteam fam 👋 — the milestone we've been building toward under our grant is now public.

**The problem we're attacking:** USENIX Security 2026 found security-rule violations in *all fifteen* major x402 payment facilitators. The recurring bug is treating "payment succeeded" as "the work was done." When agents start hiring agents, that conflation is how treasuries get drained by work that never happened.

**What we released:** the Agent Definition Language (ADL) v0.2.0-beta — an open spec (Apache-2.0 code, CC BY 4.0 specs) that describes an agent as one machine-validated document: model envelope + operating harness + an optional payment/reputation contract. Alongside it:

▸ a receipt-integrity validator enforcing 10 evidence layers against a 14-case threat model (replay, wrong-payee, paid-but-denied, authority misuse) — 33 adversarial probes, all failing closed
▸ a 5-level conformance ladder + 16 validated examples, including both sides of an agent-to-agent paid delegation at Level 3
▸ everything deterministic and offline — no wallet in the validation loop; live settlement stays gated behind external audit

The protocol side runs on Solana: four programs on devnet (registry, escrow, commit-reveal reputation, attestation) with the escrow/receipt flow the spec's payment extension maps onto.

**And because specs earn trust by being attacked, we built the attacker** 🤖⚔️ — **Reddi Arena**, a competitive homebrew-bot game where your bot *is* an ADL document, weight classes are computed from your declaration, league tiers are the conformance levels, and the purse is escrow + receipts on the dry-run rail. Adversarial players trying to get paid without doing the work are the conformance suite. Early access waitlist is open: https://reddi-arena-production.up.railway.app

**The ask:** build against the beta and break it. Building the Arena already put three real spec gaps on the v0.3 backlog (no price-discovery field #440, no non-monetary currency units #441, seller-side `charge` intents escaping the authority envelope #389). If you hit a wall the spec should have prevented, that implementation report is a v0.3 design input.

🧪 Try it in 5 min: `curl -LO https://agent-protocol.reddi.tech/downloads/adl-v0.2.0-beta.zip` → unzip → `python3 scripts/adl_v02_conformance.py examples/v0.2/payment-agent.yaml`

📜 Spec: https://agent-protocol.reddi.tech/spec
🚀 Release: https://github.com/nissan/reddiagent-lab/releases/tag/v0.2.0-beta
🗣️ Feedback: https://agent-protocol.reddi.tech/feedback

Happy to answer questions here — and if anyone wants a review buddy for their first ADL doc, ping me. 🫡
