# ReddiAgent ADL v0.2.0-beta — Release Notes

_This file is the canonical body for the GitHub release tagged `v0.2.0-beta`.
The existing draft release predates the repo-org correction and the Reddi Arena
proof deployment — replace the draft body with the text below before
publishing. All links point at `nissan/reddiagent-lab` (the draft's
`reddinft/…` links are wrong and 404)._

---

First public release of ReddiAgent Lab — the open spec home for **ADL, the
Agent Definition Language**: define an AI agent once (model envelope +
operating harness + optional payment/reputation extension) and validate it
deterministically.

## What's in this release

**The spec**
- [specs/ADL-v0.2.md](https://github.com/nissan/reddiagent-lab/blob/main/specs/ADL-v0.2.md) — canonical specification with a machine-checked field contract
- [specs/ADL-v0.2.schema.json](https://github.com/nissan/reddiagent-lab/blob/main/specs/ADL-v0.2.schema.json) — JSON Schema (37 defs, closed vocabularies, fail-closed extensions)
- 5-level conformance matrix; [migration guide from v0.1](https://github.com/nissan/reddiagent-lab/blob/main/docs/ADL-v0.1-to-v0.2-MIGRATION.md)
- Browsable spec + downloadable bundle: [agent-protocol.reddi.tech/spec](https://agent-protocol.reddi.tech/spec)

**Runnable proof — settlement is not success**
- `scripts/rap_receipt_validator.py`: receipt-integrity validator enforcing 10 evidence layers against a 14-case threat model (replay, wrong-payee, paid-but-denied, authority misuse), grounded in USENIX Security 2026 findings (arXiv:2607.19545) that all 15 major x402 facilitators violated basic security rules. Hardened through three rounds of adversarial review (33 probes, fail-closed on every axis: type, value-domain incl. NaN/Infinity, unknown enums, malformed JSON).
- `scripts/rap_receipt_integrity_benchmark.py`: the threat-model spec, cross-checked in CI so spec and implementation cannot drift.

**Working examples of agent-to-agent paid delegation**
- 16 validated examples including both sides of a paid delegation: a buyer (`payment-agent`) and three seller services (research / pricing / review) at conformance Level 3 — full payment authority contracts, receipts, reputation signals, dry-run rail only.
- 20+ negative fixtures a correct validator must reject.

**Tooling**
- Conformance checker, diagnostics, provider compatibility reports (OpenAI/Anthropic/Gemini/Ollama/LangGraph), A2A Agent Card export, 222-test deterministic suite.

## Proof in the wild: Reddi Arena

The spec is not just documents. **[Reddi Arena](https://github.com/nissan/reddi-arena)**
is a competitive homebrew-bot arena built as a working proof use case for ADL
v0.2 and the Reddi Agent Protocol — live at
[reddi-arena-production.up.railway.app](https://reddi-arena-production.up.railway.app),
and **accepting early-access waitlist signups now**.

Every game action is a protocol artifact: bots are ADL documents, weight classes
are computed from the machine-readable declaration, league tiers are the five
conformance levels, the mercenary power-up market is RAP discovery, and the
purse is escrow + receipts on the honest dry-run rail (prizes are
ARENA-CREDIT). An arena full of adversarial players trying to get paid without
doing the work is a direct, continuous test of the protocol's core claim:
**payment success is not work success.**

Building the Arena against this beta already produced real spec findings — see
below.

## Help us build v0.3 — call for feedback

Read [CONTRIBUTING.md](https://github.com/nissan/reddiagent-lab/blob/main/CONTRIBUTING.md).
The highest-value feedback is an **implementation report**: you tried to build
against ADL and hit friction. File it with the
[open-spec review template](https://github.com/nissan/reddiagent-lab/issues/new?template=open-spec-review.md)
or start from [agent-protocol.reddi.tech/feedback](https://agent-protocol.reddi.tech/feedback).

Known open gaps we want challenged — already filed from Reddi Arena's
implementation experience and now anchoring the v0.3 backlog:

- [#440](https://github.com/nissan/reddiagent-lab/issues/440) — **No price-discovery field**: `maxAmount` is a cap, not a quoted price; a marketplace card cannot say "costs 20 per task" in canonical ADL.
- [#441](https://github.com/nissan/reddiagent-lab/issues/441) — **Currency enum excludes non-monetary units** (points, credits, in-game currencies).
- [#389](https://github.com/nissan/reddiagent-lab/issues/389) — **Seller-side `charge` intents escape the authority envelope** (charge-side conformance enforcement + session caps), with ablation evidence attached.

If your implementation hits a wall the spec should have prevented, that report
is a v0.3 design input.

Licensing: Apache-2.0 (code), CC BY 4.0 (specs/docs). Live settlement and
mainnet remain gated behind external audit.
