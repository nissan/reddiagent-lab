# RAP Bridge v0.1

_Added: 2026-07-08. Anchor: x402/MCP micropayments integration layer._

## Goal

Make a ReddiAgent definition that follows common x402 paid MCP service patterns easy to upgrade into Reddi Agent Protocol without rewriting the agent or weakening ReddiAgent's safety boundaries.

The bridge is an integration layer, not a runtime. It describes how ADL payment, authority, receipt, and reputation metadata can be preserved for a later RAP-capable implementation.

## Non-Goals

This spec does not authorize:

- MCP server resolution or invocation;
- wallet access;
- facilitator calls;
- live x402 settlement;
- Solana/Base/Stripe or other payment rail execution;
- credential lookup;
- runtime agent activation.

## Compatibility Model

The bridge treats the video-described x402/MCP flow as a source pattern:

1. An agent or app requests an MCP-backed HTTP service.
2. The service returns an HTTP 402 challenge with accepted payment terms.
3. The client signs or prepares payment proof.
4. The service/facilitator verifies or settles payment.
5. The service returns output plus payment response metadata.

ReddiAgent should preserve this shape as reviewable metadata first, then allow RAP to own protocol execution later.

## Layer Responsibilities

| Layer | Responsibility |
|---|---|
| ADL core | Agent identity, model needs, harness policy, tools, data sources, eval gates, traces |
| `extensions.x402` | Payment intent, accepted rails/assets, spend/charge limits, proof/response vocabulary |
| `extensions.authority` | AP2-like mandate metadata: who may spend, for what, how much, until when, and how it can be revoked or audited |
| `extensions.receipts` | Work-plus-payment evidence required before completion or reputation signals |
| `extensions.reputation` | Signals derived from verified work, evals, receipts, policy compliance, and dispute/refund outcome |
| RAP bridge | Static mapping from ReddiAgent metadata into RAP-ready payment, receipt, authority, and reputation fields |
| Reddi Agent Protocol | Future protocol-level settlement, verification, receipts, and reputation semantics |

## Required Bridge Fields

An ADL file should be considered RAP-ready only when the bridge can identify:

- payment direction: `spend`, `charge`, or `both`;
- payment rail preferences, including `solana`, `base`, `stripe`, or `other-x402`;
- max amount, currency/asset, and per-task budget;
- payee or service identity when known;
- payer or agent identity when known;
- accepted payment options if supplied by an x402 challenge;
- facilitator identity or policy if declared;
- authorization/mandate scope;
- authorization expiry and revocation/audit hooks;
- request and response hashes;
- payment response or settlement reference;
- service-result status;
- required eval gate status;
- receipt emission policy;
- reputation signals allowed after receipt verification.

## x402 Object Vocabulary

The bridge should preserve these x402 objects without treating them as live settlement:

- `PaymentRequired`: resource URL/description, accepted options, amount, asset, network, payTo, timeout.
- `PaymentSignature`: selected terms, payer authorization, signature/proof reference.
- `PaymentResponse`: success status, transaction/reference, network, payer.

If any object contains live server URLs, credentials, wallet material, embedded facilitator endpoints, executable commands, or unrestricted spend authority, the bridge must report it as not-ready.

## RAP Upgrade Path

The intended builder path is:

1. Define the agent in ADL with MCP service declarations and payment intent.
2. Validate x402 metadata and static MCP readiness locally.
3. Add AP2-like authority/mandate constraints for spend-capable behavior.
4. Emit dry-run receipts that bind payment metadata to delivered work and eval results.
5. Export a RAP bridge report showing what is ready, metadata-only, unsupported, or unsafe.
6. Later, once RAP execution is approved outside this lab guardrail, use the report as the handoff package for a RAP-capable implementation.

## Readiness Checks

A RAP bridge report should include:

- `bridgeReady`: true only when required fields are present and no live-execution fields are embedded;
- `metadataOnly`: fields preserved for future RAP use but not enforceable by ReddiAgent alone;
- `unsupported`: fields that cannot be represented safely;
- `unsafe`: fields that would imply live execution, credentials, wallet access, or unconstrained spending;
- `runtimeExecutionAllowed=false`;
- `networkAccess=false`;
- `mcpInvocation=false`;
- `paymentAccess=false`.

## Failure Semantics

The bridge must not treat payment success as task success.

Receipts and reputation require both:

- payment status or payment proof status; and
- service-result status plus required eval gate status.

This protects against cases where payment is verified or settled but the paid service fails to return useful output.

## Current Safe Next Slice

The next implementation slice should be static and deterministic:

- add one RAP bridge fixture for an x402-paid MCP service declaration;
- add one negative fixture with live wallet/facilitator/server fields;
- add a report-only checker that validates bridge readiness and preserves x402/AP2/receipt/reputation metadata;
- keep all outputs review artifacts only.

No live MCP, wallet, facilitator, payment rail, or RAP runtime path should be added in this slice.
