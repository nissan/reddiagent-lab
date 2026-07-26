# Agent Team Delegation Examples

_Issue #384. Follows the Phase 1 curation in #383._

This repo now carries a working agent team and the first paid-delegation
service examples for Reddi Agent Protocol. Both come from the same source:
eight portable agent charters imported into `.claude/agents/`.

## The two roles the team plays

**1. Working subagents for this repo.** The charters in `.claude/agents/`
(archie, becky, belle, firefly, kit, oli, quinn, sara) are usable directly in
coding sessions here: archie for standards research, firefly for build
planning, kit for implementation, oli for review gates, sara for editorial
passes on specs and docs, quinn for synthesis, becky for cost intelligence,
belle for design/UX artifacts.

**2. First Reddi Agent Protocol working examples.** Three of the
service-shaped personas are also expressed as ADL v0.2 definitions — the
first agents intended to be discoverable and payable by *other agents* under
RAP:

| Example | Persona | Service | Charge intent |
|---|---|---|---|
| `examples/v0.2/delegation-research-agent.yaml` | archie | Source-backed research with citations and confidence levels | `charge-research-task`, 0.25 USDC cap |
| `examples/v0.2/delegation-pricing-agent.yaml` | becky | Sourced, confidence-graded cost/pricing report (advisory only) | `charge-pricing-report`, 0.15 USDC cap |
| `examples/v0.2/delegation-review-agent.yaml` | oli | Severity-graded review with a green/yellow/red verdict | `charge-review-verdict`, 0.10 USDC cap |

Each is a conformance **Level 3** document: `direction: charge` x402 intent on
the `x402-dry-run` rail only, full payment authority contract (operator
grants the service the right to charge; the delegating client is the
counterparty), policy-engine-enforced charge policy, human approval, receipt
binding, budget/receipt eval gates, and the full Level-3 observability event
set. The buyer side of the same transaction is modeled by
`examples/v0.2/payment-agent.yaml`.

## Discovery surface

`scripts/adl_to_a2a_agent_card.py` exports these definitions toward A2A Agent
Cards. The static mapping reports them `supported` but **not lossless**:
harness policies, eval gates, receipts, reputation, and x402 metadata survive
only as card metadata, and strict card export correctly refuses
(`a2a_agent_card_export_would_drop_reddi_semantics`) because payment-bearing
definitions would drop Reddi semantics. Live discovery listing and settlement
belong to the Reddi Agent Protocol repo, behind its own gates — nothing in
this repo registers, lists, or settles anything.

## Spec feedback these examples surfaced (ADL v0.3 candidates)

Authoring the seller side exposed real gaps — recorded here as open spec
feedback rather than smoothed over:

1. **Charge intents escape conformance enforcement.** The v0.2 conformance
   checker only enforces authority-matching, receipt-binding, and
   matching-payment-policy checks for `spend`/`refund` intents; a `charge`
   intent with no authority block would still achieve Level 3. These examples
   voluntarily satisfy the full contract, but the checker should enforce it.
2. **The schema makes seller-side rigor optional.** The conditional
   requirements on `purpose`/`scope`/`authority`/`requireReceipt`/
   `receiptRef`/`policyRefs` fire only for `spend|refund` — yet the seller
   side is where receipts matter most for the counterparty.
3. **Buyer-framed vocabulary.** `authority.spender` on the charge side holds
   the party being charged; `payment.intent.created` has no seller-side
   counterpart (`payment.intent.received`); `budget-check` reads as
   "don't overspend" where the seller's honest gate is "don't overcharge".
4. **No price-discovery field.** `maxAmount` is a cap, not a quoted price.
   A discovery card for a paid service needs "this service costs X per task";
   neither ADL v0.2 nor the A2A mapping can express it today.

## Boundaries

The `x402-dry-run` rail is the only rail any example declares. No wallet,
facilitator, payment rail, settlement, registry mutation, or live discovery
listing is performed by anything in this repo. Mainnet remains blocked behind
official audit and explicit go-live approval.
