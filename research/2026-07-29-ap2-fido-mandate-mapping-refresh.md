# AP2 / FIDO Mandate Mapping Refresh

_Issue #377 (epic #386). Static research report — no code, no live invocation._
_Sources checked 2026-07-28/29 AEST. Baselines: tests/AP2-X402-MANDATE-REPORT.md + scripts/ap2_x402_mandate_report.py (issue #133 mapping) and research/2026-07-26-agent-payments-landscape-and-backlog-alignment.md §"what's new" row + §3 (Whispers of Wealth boundary)._
_Confidence codes: **H** = primary source read directly; **M** = primary source partially readable or corroborated secondary; **L** = single secondary source or unverified convention._

**Correction notice up front**: two claims carried by the #377 reframe and the 2026-07-26 baseline need adjustment. (1) "Production-ready A2A x402 extension" — the phrase originates in Google's AP2 announcement; the extension's own spec is **v0.1** (extension URI `https://github.com/google-a2a/a2a-x402/v0.1`, read 2026-07-29, **H**) with reference implementations. Treat it as the most concrete artifact in the stack, not a finished standard. (2) "FIDO published the joint AP2 + Verifiable Intent trust-layer piece" — what FIDO published on 2026-04-28 is an **announcement of working groups and contributed inputs**; "Published Specifications: None yet" per the announcement itself ([fidoalliance.org](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/), read 2026-07-29, **H**). Both TWGs are watch-only (§3). Separately, this report supersedes the #133 fixture vocabulary: the prior mandate field set was placeholder, not AP2 claims (§1 deltas).

## 1. AP2 v0.2.0 mandate structure

Release facts: v0.2.0 shipped 2026-04-28 ("second release … focuses on providing Human Not Present flows", [github.com/google-agentic-commerce/AP2/releases](https://github.com/google-agentic-commerce/AP2/releases), read 2026-07-29, **H**) — the same day as the FIDO announcement, reading as a coordinated donation (**M** for coordination intent). v0.1.0 was 2025-09-16.

**The v0.2 spec and the reference SDK are two different surfaces, both live:**

**(a) Normative spec (Agent Authorization Framework + mandate pages, ap2-protocol.org, read 2026-07-29, H).** Two mandate families, each **open** (constraints set before finalization) or **closed** (a specific finalized transaction), as **SD-JWT VCs**:

- **Checkout Mandate** — `vct` `mandate.checkout.1` (closed) / `mandate.checkout.open.1` (open). Claims: `checkout_jwt` (base64url merchant-signed JWT of the checkout payload), `checkout_hash` (base64url hash of `checkout_jwt`, per `_sd_alg`, default SHA-256), optional `iat`/`exp`; `checkout_jwt`/`checkout_hash` are selectively disclosable. Open-mandate constraint types: `checkout.allowed_merchants`, `checkout.line_items` (maximal-flow quantity matching).
- **Payment Mandate** — `vct` `mandate.payment.1` / `mandate.payment.open.1`. Closed claims: `transaction_id` (hash of `checkout_jwt` — the checkout binding), `payee` (Merchant: `id`, `name`, `website`), `payment_amount` (`amount`, `currency`), `payment_instrument` (`id`, `type`, `description`), optional `pisp`, `execution_date`, `risk_data`, `iat`/`exp`. Open-mandate constraint types: `payment.agent_recurrence`, `payment.allowed_payees`, `payment.allowed_payment_instruments`, `payment.allowed_pisps`, `payment.amount_range`, `payment.budget` (total across recurrences), `payment.reference` (binds to an open Checkout Mandate via `conditional_transaction_id`), `payment.execution_date` (`not_before`/`not_after`).
- **Key binding**: `cnf` (JWK, RFC 7800) is "REQUIRED if the Mandate is still open" — the agent proves possession via a KB-JWT when closing/presenting after the user has left. Unknown constraint types "MUST be treated as failing evaluation" (fail-closed). **No revocation mechanism is specified on any mandate page read** (**H** for the absence).
- **Presentation**: OpenID4VP with a `_delegate_`-typed `transaction_data` entry carrying `format`, `delegate_payload` (mandate contents), optional `delegate_disclosures`. The verifier returns a **Mandate Receipt** (signed JWT: `iss`, `result` `success|error`, `reference` = base64url hash of the received mandate, optional `error`/`error_description`); the Payment Receipt adds `status`, `payment_id`, optional `psp_confirmation_id`, `network_confirmation_id`. The spec notes ISO mDoc (18013-5/-7) could substitute for SD-JWT VC (**H**).

**(b) Reference SDK (`code/sdk/python/ap2/models/mandate.py`, read via gh 2026-07-29, H)** still ships the v0.1-era trio: `IntentMandate` (`user_cart_confirmation_required`, `natural_language_description`, `merchants`, `skus`, `requires_refundability`, `intent_expiry`), `CartMandate` (`contents`: `CartContents{id, user_cart_confirmation_required, payment_request, cart_expiry, merchant_name}`, `merchant_authorization` JWT with `cart_hash`/`jti`), `PaymentMandate` (`payment_mandate_contents{payment_mandate_id, payment_details_id, payment_details_total, payment_response, merchant_agent, timestamp}`, `user_authorization` — docstring: "base64url-encoded verifiable presentation of a verifiable credential signing over the cart_mandate and payment_mandate hashes … an sd-jwt-vc"). So the SDK's Intent concept survives as prose intent + expiry; in the v0.2 credential model the intent role is played by the **open** Checkout/Payment mandates' constraint arrays.

**Deltas vs the #133 baseline (explicit):**

1. The fixture mandate field set `id/vcRef/issuer/subject/scope/expiresAt/auditRef` (MANDATE_FIELDS in scripts/ap2_x402_mandate_report.py) matches **neither** surface — it was a placeholder vocabulary. Real identification is by **hash** (`checkout_hash`, `transaction_id`, receipt `reference`), not an `id` claim; scope lives in typed `constraints`, not a prose `scope` string (**H**).
2. Fixture `PaymentMandate.settlementRail`, `.asset`, `.maxAmount`, `.revocationRef` do not exist in AP2: **AP2 carries no rail claim** (nearest is `payment_instrument.type`; rail/network is x402-side), amount ceilings are open-mandate constraints (`payment.amount_range`/`payment.budget`), and **no revocation path exists** (**H**).
3. Mandate topology changed: Intent/Cart/Payment trio (v0.1/SDK) → Checkout/Payment × open/closed (v0.2 spec), with Cart renamed Checkout and Intent folded into open-mandate constraints (**H**).
4. `expiresAt` is **optional** in AP2 (`exp` optional on both mandate types); the #133 checker treats it as required — correct for RAP policy, but it must be reported as a RAP-imposed tightening, not an AP2 requirement (**H**).

## 2. A2A x402 extension (mandates into settlement)

Source: `spec/v0.1/spec.md` in [github.com/google-agentic-commerce/a2a-x402](https://github.com/google-agentic-commerce/a2a-x402) (raw read 2026-07-29, **H**). A2A v1.0 under Linux Foundation governance is baseline-sourced (Mar 2026, **M** — not re-verified this sweep).

- **Activation**: header `X-A2A-Extensions: https://github.com/google-a2a/a2a-x402/v0.1`, echoed by the server. (Note the URI's `google-a2a` org vs the repo's `google-agentic-commerce` home — cite the URI as an opaque identifier, **H**.)
- **Metadata keys** on A2A task/message metadata: `x402.payment.status` (`payment-required` → `payment-submitted` → `payment-verified` → `payment-completed`, with `payment-rejected`/`payment-failed` branches), `x402.payment.required`, `x402.payment.payload`, `x402.payment.receipts` (**cumulative history array**), `x402.payment.error`.
- **Shapes**: `x402PaymentRequiredResponse{x402Version, accepts[]}`; `PaymentRequirements{scheme, network, asset, payTo, maxAmountRequired; optional resource, description, maxTimeoutSeconds, extra}`; `PaymentPayload{x402Version, network, scheme, payload}`; `x402SettleResponse{success, transaction, network, payer, optional errorReason}`. Error codes: `INSUFFICIENT_FUNDS`, `INVALID_SIGNATURE`, `EXPIRED_PAYMENT`, `DUPLICATE_NONCE`, `NETWORK_MISMATCH`, `INVALID_AMOUNT`, `SETTLEMENT_FAILED`.
- **How mandates ride**: the extension carries x402 payment evidence, not AP2 mandates as first-class objects — the client agent checks `PaymentRequirements` against the user's mandate and signs; mandate linkage to settlement is by the client's own binding (secondary corroboration: [typevar.dev a2a-x402 guide](https://typevar.dev/articles/google-agentic-commerce/a2a-x402), read 2026-07-29, **M**). There is **no mandate-hash field in the v0.1 shapes** — `PaymentPayload.payload` and `extra` are the only slots (**H** for the shapes; **M** for the practice). This is the gap RAP receipts already fill with `paymentEvidence.boundRequestId` + `delegatedAuthority.mandateId`.

## 3. FIDO agentic TWGs + Mastercard Verifiable Intent

**FIDO (watch-only)**: 2026-04-28 announcement formed the **Agentic Authentication TWG** (chairs CVS Health, Google, OpenAI; vice-chairs Amazon, Google, Okta) and expanded the **Payments TWG** (chairs Mastercard, Visa) to take Google's AP2 and Mastercard's Verifiable Intent as inputs. No specifications published; "work has commenced … will provide reports" ([fidoalliance.org](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/), read 2026-07-29, **H**; corroboration [pymnts.com](https://www.pymnts.com/artificial-intelligence-2/2026/google-and-mastercard-contribute-agentic-commerce-standards-to-fido-alliance/), **M**).

**Verifiable Intent (mappable today at credential-format level)**: open spec at [github.com/agent-intent/verifiable-intent](https://github.com/agent-intent/verifiable-intent/) (read 2026-07-29, **H**) — Draft v0.1, Apache-2.0, maintained by Mastercard; announced March 2026 (2026-03-05 per the #377 reframe; month corroborated by press, exact day not independently verified — **M**). Co-developed with Google; commitments from Fiserv, IBM, Checkout.com, Basis Theory, Getnet (**M**, press). Layered SD-JWT chain, RFC 7800 `cnf` binding each layer, "no novel cryptography":

- **L1** credential provider → user: identity claims, `pan_last_four`, `cnf.jwk` = user device key; ~1-year life.
- **L2** user → agent: checkout/payment constraints, `cnf.jwk` = agent key; 24h–30d.
- **L3** agent → network/merchant, **split L3a/L3b**: final values, `transaction_id`, `checkout_hash`; ~5-minute life. Selective disclosure is role-scoped: networks see L3a, merchants see L3b.
- **Modes**: Immediate (L1+L2, no `cnf` delegation — user reviews final values) vs Autonomous (L1+L2+L3, agent key bound). Constraint vocabulary distinguishes machine-enforceable (amount, payee, merchant) from descriptive fields. Note the shared vocabulary with AP2 (`checkout_hash`, `transaction_id`, `cnf`) — convergence is real, not just press framing (**H**).

## 4. ADL / RAP mapping tables

ADL sources: `extensions.x402.intents[].authority{principal, spender, maxAmount, currency, expiry, revocation}` + intent `purpose`/`scope`/`rails`/`policyRefs` (specs/ADL-v0.2.md "Extension And Payment Authority Contract", **H**); RAP: `REQUIRED_LAYER_FIELDS["delegatedAuthority"] = (mandateId, principal, spender, payee, purpose, rail, maxAmount, expiresAt, auditRef)` (scripts/rap_receipt_validator.py, **H**).

### (a) AP2 v0.2 mandate claims ↔ ADL x402 authority block

| ADL/RAP authority field | AP2 v0.2 source | Rule / gap | Conf. |
|---|---|---|---|
| `principal` | SD-JWT issuer chain (credential provider → user); no named principal claim in the mandate body | Partial: principal is established by issuance + `cnf` chain, not a claim; ingest as the mandate issuer identity. | H |
| `spender` | `cnf` (JWK) on an open mandate | **Type mismatch**: ADL expects a party identifier; AP2 gives a key. Rule: spender = holder of the KB key; record a key thumbprint (RFC 7638) as the spender ref. | H |
| `payee` | `payee{id,name,website}` (closed) / `payment.allowed_payees` (open) | Direct (closed); set-valued on open mandates — ADL authority has one payee slot, so open mandates map to intent scope, not authority. | H |
| `purpose` | — (nearest: `checkout.line_items`, SDK `natural_language_description`) | **No AP2 purpose claim.** Derive prose from constraints; lossy. | H |
| `rail` | — | **AP2 carries no rail.** Rail lives in x402 `PaymentRequirements.network`; `payment_instrument.type` is instrument, not rail. Cross-layer join required. | H |
| `maxAmount` | `payment.amount_range` / `payment.budget` (open); `payment_amount` (closed) | Open constraints are the true cap; closed `payment_amount` is the actual charge — cap-vs-price distinction again (Pay.sh report §3). Ingest caps from open, actuals from closed. | H |
| `expiresAt` | `exp` (optional) + `payment.execution_date` | Mapped but **optional in AP2**; RAP requiring it is a RAP tightening — report code, not AP2 error. | H |
| `revocation` | — | **No revocation path in AP2 v0.2.** ADL requires a revocation mode (`operator`/`policy-engine`/`human-review`); an AP2-backed intent can only satisfy it with an out-of-band RAP-side revocation policy. Gap both directions. | H |
| `auditRef` | Mandate Receipt `reference` / Payment Receipt `payment_id` | Direct — the verifier-signed receipt is AP2's native audit artifact. | H |
| `mandateId` | `checkout_hash` / `transaction_id` (hashes), SDK `payment_mandate_id` | v0.2 has **no id claim**; identify by hash (next table). | H |

### (b) AP2 mandate hash ↔ RAP receipt `delegatedAuthority` (validator ingestion)

| RAP field | Ingestion rule | Conf. |
|---|---|---|
| `mandateId` | base64url hash of the closed mandate, algorithm per `_sd_alg` (default SHA-256) — the same value the Mandate Receipt's `reference` carries, so RAP's id and AP2's audit trail agree by construction. For SDK-trio evidence: `payment_mandate_id`. | H |
| `auditRef` | The Mandate/Payment Receipt JWT (or its storage ref). Bind: receipt `reference` MUST equal `mandateId`; on Payment Receipts also retain `payment_id`/`psp_confirmation_id`. | H |
| SD-JWT+kb bundle (proposed evidence shape) | `<issuer-signed SD-JWT>~<disclosures…>~<KB-JWT>`. Shape-only checks for the report-only validator: three-segment structure present; `vct` ∈ {`mandate.checkout.1`, `mandate.checkout.open.1`, `mandate.payment.1`, `mandate.payment.open.1`}; `cnf` present iff open; unknown constraint types → fail-closed (mirrors AP2's own rule); **no signature verification** in report-only mode — that is a live-lane capability. | H for the AP2 facts; proposal is this report's |
| Cross-layer join | `delegatedAuthority.rail/payee/maxAmount` come from ADL intent + x402 `PaymentRequirements`, never from the AP2 mandate alone (rail/revocation gaps above). The `cannotSubstitute` rule holds: mandate evidence is authority evidence only, never payment/settlement evidence (consistent with scripts/rap_receipt_integrity_benchmark.py layer_requirements and the SATI report §5c). | H |

### (c) Verifiable Intent layers ↔ RAP receipt fields

| VI element | RAP receipt source | Rule / gap | Conf. |
|---|---|---|---|
| L1 identity claims + user `cnf.jwk` | `delegatedAuthority.principal` | Principal with an actual identity layer — richer than AP2's issuer-chain inference. | H |
| L2 constraints + agent `cnf.jwk` | `delegatedAuthority.spender/maxAmount/expiresAt` | Same key-thumbprint rule as (a); L2 lifetime (24h–30d) maps to `expiresAt`. | H |
| L3 `transaction_id`, `checkout_hash`, final values | `paymentEvidence.boundRequestId` + `serviceOutcome.requestHash` | Shared vocabulary with AP2 makes one ingestion rule serve both; L3's ~5-min life means RAP receipts outlive their evidence — store the hash, not the credential. | M |
| L3a/L3b role-split disclosure | `privacyAccounting` | Direct philosophical fit: RAP's commit-reveal (amounts stay in the receipt, events go public) is the receipt-side analogue of role-scoped disclosure. Cross-rail credibility path from the roadmap: a VI-verified card transaction and an x402-settled crypto transaction land in the same receipt schema. | M |
| Immediate vs Autonomous mode | `delegatedAuthority` presence/absence of spender key | Immediate mode (no `cnf` delegation) ≈ human-approved flow — maps to the `humanApproved` reputation signal, not to delegated authority. | M |

## 5. Recommendation block

1. **Update the #133 artifact pair** — `scripts/ap2_x402_mandate_report.py` + `tests/AP2-X402-MANDATE-REPORT.md` + both fixtures: add the v0.2 `vct` vocabulary (four values), the typed `constraints` arrays, hash-based identity (`checkout_hash`/`transaction_id`), and receipt `reference` binding; keep the SDK trio (`IntentMandate`/`CartMandate`/`PaymentMandate`) as a second accepted profile since the reference SDK still ships it; reclassify `expiresAt`-missing from "AP2 required field missing" to a RAP-tightening code; delete the invented `vcRef`/`settlementRail`/`revocationRef` mandate fields (rail/revocation must come from the ADL intent side per table (a)).
2. **Receipt validator ingestion rule**: add the SD-JWT+kb shape check from table (b) to `rap_receipt_validator.py`'s `delegatedAuthority` handling as an optional `mandateEvidence` sub-object (format tag `sd-jwt-vc+kb`, `vct`, `mandateHash`, `receiptReference`) — shape-only, fail-closed on unknown `vct`/constraint types, no signature verification in report-only mode.
3. **A2A x402 lane**: when the RAP bridge maps to A2A, mirror the `x402.payment.*` metadata keys and the six-state machine; carry `mandateId` in `PaymentRequirements.extra`/`PaymentPayload.payload` since v0.1 has no mandate slot — and log that as an upstream gap worth raising on the a2a-x402 repo.
4. **ADL v0.3 intake (#389)**: two candidates emerge — (i) recurrence vocabulary: AP2 `payment.agent_recurrence` + `payment.budget` (cap across recurrences) have no ADL analogue (`maxAmount` is per-intent); (ii) an optional `authority.mandateRef` pointer (format + hash) so an ADL intent can cite an external AP2/VI mandate without embedding it — pointers, not embedded credentials, consistent with the SATI report §6. Nothing else new; the `currency` enum gap is already logged from the Pay.sh sweep.
5. **Watch-only**: FIDO TWG outputs (no artifacts yet; re-check when FIDO "provides reports"); ISO mDoc as alternate mandate format; MPP's relationship to all of this. **Mappable today**: AP2 v0.2 mandate pages, a2a-x402 v0.1 spec, VI credential-format.md.

**Risks (explicit):**

- **Spec churn (H)**: AP2 restructured its mandate model once already (trio → open/closed pairs) within seven months, its SDK lags its own spec, and FIDO's standards process will rework both contributions; a2a-x402 is v0.1. Pin every mapping row to `vct` values and read dates, and expect a second refresh when the FIDO TWGs publish.
- **Scope boundary — Whispers of Wealth (H)**: per the baseline (arXiv 2601.22569), RAP receipts attest *authorized/paid/delivered/evaluated*, not *well-formed intent*. Mandate construction — whether the user's prompt was injected upstream of mandate signing — is out of scope for the validator, and the ingestion rule in (b) must say so: RAP verifies the mandate hash binding, never the mandate's wisdom.
- **Key-vs-identity mismatch (H)**: both AP2 and VI identify the spender by key (`cnf`), ADL by named party. The thumbprint rule works but breaks on key rotation; flag rotated-key mandates as new spenders until a registry-identity join (SATI report table (a)) exists.
- **No AP2 revocation (H)**: any ADL intent claiming an AP2-backed authority satisfies the required revocation mode only through RAP-side policy; validators must not report AP2 as providing one.

## Boundary

Research/report evidence only. No live invocation, payment, settlement, wallet or facilitator action, credential issuance, mandate creation or presentation, and no PR to any external repository occurred; web and gh reads were documentation-only. Fixture note: `scripts/protected_docs_package.py` pins only seven named `research/` entrypoint files (none dated after 2026-07-17), verified by grep this session — this new dated report is outside the allowlist and touches no fixtures; the #133 script/fixture updates recommended in §5 are future work, not performed here. Mainnet remains blocked behind official audit and explicit go-live approval.
