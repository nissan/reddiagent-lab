# REASONS-LITE — Evidence-tiered marketplace envelope and optional Buzz projection

_Status: draft | Owner: Loki on behalf of Nissan | Project: reddiagent-lab | Issue: [#426](https://github.com/reddinft/reddiagent-lab/issues/426) | Normative inputs: `specs/BUZZ-ADAPTER-CONTRACT-v0.1.md`, `spdd/prompt/0425-buzz-exporter.md`, ADR 0005_

SPDD-LITE is required because curation claims cross identity, provenance,
privacy, install handoff, payment/reputation authority, revocation, and future
public-distribution boundaries. This file is the implementation update plan.
Implementation must update it in the same PR if the schema, state machine,
files, evidence rules, or safeguards materially diverge.

## R — Requirements / Definition of Done

Define and implement a deterministic, Reddi-owned curation envelope for an
optional Buzz static projection. The envelope consumes the exact #425 report
and package evidence without making Buzz canonical or turning a listing,
publisher, owner proof, review, event, audit chain, or tier into payment,
receipt, service-acceptance, or reputation authority.

**DoD checklist:**

- [ ] Publish a versioned JSON Schema covering listing/version/publisher,
  canonical ADL URI/version/digests/source commit, exporter report/package
  digests, exact Buzz upstream/fork/adapter pins, owner binding, permissions,
  projection losses, payment mode, tier assertions, reviews, incidents,
  revocation, provenance, and evaluation time.
- [ ] Implement one deterministic local validator/state evaluator with stable
  `BUZZ_CURATION_*` diagnostics and canonical JSON evidence.
- [ ] Support exactly five independent evidence tiers: `listed`, `validated`,
  `reviewed`, `receipt-backed`, and `payment-enabled`. Each assertion names its
  issuer, subject digest, `asOf`, `expiresAt`, evidence references, downgrade
  rule, and revocation reference.
- [ ] Never infer a higher tier from a lower tier. In particular,
  `payment-enabled` is independently asserted and cannot be inferred from
  listing presence, validation, review, receipts, reputation, Buzz/Nostr
  identity or events, or an owner signature.
- [ ] Show explicit choices: retain canonical ADL, use another adapter, prepare
  a payment-disabled Buzz package, and reserve RAP request-only mode for a
  separately authorized later phase.
- [ ] Emit an optional, static install-review handoff only. It cannot admit,
  install, start, update, enable tools, attach credentials/wallets/RPC, grant
  spend, contact a relay/provider, or mutate runtime state.
- [ ] Fail closed or visibly downgrade expired, revoked, tampered, stale,
  misleading, ambiguous, or pin-mismatched listings and tier assertions.
- [ ] Produce deterministic positive, expiry, revocation, tamper, misleading-
  claim, independent-payment-tier, and no-auto-install fixtures plus a static
  accessible review rendering.
- [ ] Pass focused schema/state-machine/rendering tests, snapshot determinism,
  `git diff --check`, full deterministic smoke, exact-head Oli QA, and Sara
  content/accessibility review before merge.

Out of scope: public marketplace deployment; ratings or paid listings; on-chain
publication; automatic update/install; Buzz source/install/runtime/relay/agent;
provider or credential access; tool/MCP invocation; wallet, RPC, payment,
settlement, refund, or delegated spend; public distribution; deployment;
localnet, devnet, or mainnet; upstream contact; and work on #427 or later.

## E — Entities / Handoff Objects

| Entity / object | Purpose | Required fields / invariants |
|---|---|---|
| Curation envelope | Deterministic listing evidence root | Format/version, listing id/version, subject digest, publisher, canonical ADL, exact target pins, exporter evidence, tier assertions, losses, permissions, incidents, revocation, provenance, evaluation time, decision, diagnostics, digest |
| Listing subject | Exact immutable thing being curated | Canonical ADL URI/API version/source digest/schema digest/source commit when repository-backed; report/package/manifest digests; upstream/fork/adapter 40-hex pins; #424 contract version |
| Publisher assertion | Provenance, never authority | Stable issuer id/key, signed subject digest, signature scheme/domain, issued/expiry times; cannot imply owner, reviewer, reputation, or payment authority |
| Owner binding summary | Pin-bound identity context | Exact verified #424 binding digest, Buzz/owner keys, lifecycle state and evaluation time; active/current only for install-review eligibility |
| Tier assertion | One independent evidence claim | Tier enum, issuer and issuer role, subject digest, `asOf`, `expiresAt`, ordered evidence refs/digests, status, downgrade/revocation references; no tier inheritance |
| Review record | Scoped human review evidence | Reviewer id/role, exact subject digest and scope, reviewed time, expiry, decision, findings refs; cannot certify unreviewed fields |
| Incident/revocation record | Immediate downgrade/withdrawal input | Record id, affected subject/assertion, reason code, effective time, evidence digest, issuer; deterministic precedence over stale positive claims |
| Permission/loss disclosure | Owner review surface | Complete #425 boundary flags, ordered loss rows/diagnostics, explicit `paymentMode=none`, install/runtime/network/tool/wallet/spend denials |
| Install-review handoff | Static input for later #428 review | Envelope/report/package digests, exact pins, warnings, choices, required owner-decision state; `admitted=false`, `installed=false`, `started=false`, every capability false |
| Rendered review | Accessible deterministic evidence | Same decision/tier/loss/expiry/revocation data as JSON, no hidden authority claim, no action that performs installation |

The envelope is a signed-evidence aggregator, not a trust oracle. Validation
proves only that the included evidence is well-formed, current, scoped, and
cryptographically/digest bound. It does not prove publisher honesty, service
quality, payment status, settlement, acceptance, or reputation beyond the
named external evidence and issuer scope.

## A — Approach / Key Decisions

### Envelope and evaluation contract

Add a local CLI with separate validate and deterministic render modes:

```text
python3 scripts/buzz_curation.py validate --envelope <json> \
  --evaluation-time <pinned-utc> --json
python3 scripts/buzz_curation.py render --envelope <json> \
  --evaluation-time <pinned-utc> --output <empty-dir>
```

The CLI accepts only explicit local files and a caller-pinned RFC 3339 UTC
evaluation instant. It must not fetch identities, commits, reviews, receipts,
reputation, revocations, or packages; read ambient credentials; discover mutable
branches; contact GitHub/Buzz/Nostr/RAP; or start/install anything. The
validator recomputes every owned digest and verifies all cross-object subject
bindings rather than trusting caller-provided `verified`, `current`, or tier
booleans.

Published JSON uses UTF-8 RFC 8785/JCS, lowercase-hex SHA-256, a final newline,
explicit digest-preimage exclusions, deterministic diagnostic ordering, and no
host paths, mtimes, process ids, temporary paths, usernames, environment data,
or unpinned current time. Render mode writes through a temporary sibling and
atomically renames only after successful validation; refusal leaves no partial
review artifact.

### Independent evidence tiers

Tier names describe evidence kinds, not an automatic ladder:

| Tier | Minimum scoped evidence | Must not imply |
|---|---|---|
| `listed` | Publisher-bound immutable listing subject | Validation, review, quality, reputation, payment |
| `validated` | Exact-subject ADL/schema and #425 report validation evidence | Owner approval, runtime safety, review, reputation, payment |
| `reviewed` | Current scoped reviewer decision over the exact subject | Receipt truth, service acceptance, reputation, payment |
| `receipt-backed` | External RAP receipt/evaluation references whose issuer and status are explicitly scoped | Payment enablement, settlement inferred from Buzz, blanket reputation |
| `payment-enabled` | Separate current RAP-authority assertion for the exact subject and mode | Wallet attachment, spend delegation, payment execution, or G1/G2 authorization |

All assertions are evaluated independently. The output includes a set of
current tiers plus per-assertion status, never a single ordinal `highestTier`.
Unknown issuer roles, unsupported signature suites, absent evidence, subject
mismatch, future `asOf`, `expiresAt <= evaluationTime`, revocation at or before
evaluation, or ambiguity fail that assertion closed. An expired/revoked review
may visibly downgrade `reviewed` while a still-current `listed` assertion
remains, but no failed assertion is silently discarded.

For G1 fixtures and install-review handoff, `paymentMode` is exactly `none` and
`payment-enabled` is absent. A negative fixture includes receipt-backed evidence
without payment evidence and proves payment remains disabled. Another includes
a payment-looking Buzz event/owner signature and emits a blocking misleading-
authority diagnostic rather than a tier.

### Decision and diagnostic rules

The evaluator returns one of `eligible-for-static-review`, `downgraded`,
`hold`, or `refused`. Stable diagnostics include at minimum:

- `BUZZ_CURATION_SCHEMA_INVALID`
- `BUZZ_CURATION_SUBJECT_MISMATCH`
- `BUZZ_CURATION_PIN_MISMATCH`
- `BUZZ_CURATION_EVIDENCE_STALE`
- `BUZZ_CURATION_ASSERTION_EXPIRED`
- `BUZZ_CURATION_ASSERTION_REVOKED`
- `BUZZ_CURATION_ISSUER_UNAUTHORIZED`
- `BUZZ_CURATION_TIER_INFERENCE_REFUSED`
- `BUZZ_CURATION_PAYMENT_INFERENCE_REFUSED`
- `BUZZ_CURATION_IDENTITY_INVALID`
- `BUZZ_CURATION_LOSS_DISCLOSURE_INCOMPLETE`
- `BUZZ_CURATION_INSTALL_AUTHORITY_REFUSED`
- `BUZZ_CURATION_MISLEADING_CLAIM_REFUSED`
- `BUZZ_CURATION_ATTRIBUTION_HOLD`

Diagnostics are all-applicable and ordered by JSON pointer, severity rank, then
code. Schema/digest/pin/identity ambiguity, hidden loss, tier/payment inference,
runtime/install authority, false receipt/reputation claims, and tampering are
blocking. Ordinary expiry/revocation yields an explicit downgrade only when a
separately valid lower assertion remains and the revoked subject itself is not
the listing/package/publisher/owner binding; otherwise it holds or refuses.

### Static review and handoff

The rendered surface exposes evidence date/expiry/revocation prominently,
separates issuer-scoped claims, shows all #425 losses and boundary denials, and
offers informational choices only. The Buzz choice produces a static handoff
record with exact digests/pins and `ownerDecisionRequired=true`; it is not a
button or command that installs. Canonical ADL remains linked as the source
required for regeneration, and the page states Buzz is an optional lossy
projection while RAP remains authoritative.

The handoff has exact false flags for admission, installation, startup,
external network/relay/provider, ambient credentials, tool/MCP invocation,
wallet/RPC/payment/delegated spend, public distribution/branding, and
deployment. Any input asking the generator to flip one emits
`BUZZ_CURATION_INSTALL_AUTHORITY_REFUSED` and produces no handoff/render output.

Rejected alternatives: ordinal badges; transitive tier inheritance; treating a
publisher or owner signature as review/payment authority; deriving reputation
from listing/events; live revocation lookup in G1; an install link that mutates
state; mutable/latest pins; and copying marketplace state back into ADL.

## S — Structure / Files Touched

| Surface | Planned change |
|---|---|
| `spdd/prompt/0426-buzz-marketplace-envelope.md` | This accepted implementation plan and prompt/code sync log |
| `specs/BUZZ-CURATION-ENVELOPE-v0.1.schema.json` | Versioned deterministic envelope schema |
| `scripts/buzz_curation.py` | Local validate/evaluate/render CLI and canonical evidence helpers |
| `tests/test_buzz_curation.py` | Schema, state, tier independence, digest, expiry/revocation, refusal, determinism, accessibility/content assertions |
| `tests/fixtures/buzz-curation-*.json` | Valid, downgrade, expired, revoked, tampered, misleading, payment-inference, receipt-only, and install-authority cases |
| `tests/BUZZ-CURATION-REVIEW.html` | Deterministic static review evidence generated from the valid fixture |
| `tests/BUZZ-CURATION-EVIDENCE.md` | Human-readable contract/fixture summary generated from the same evaluation |
| `tests/smoke-validation.sh` | Focused deterministic curation validation and snapshot checks |

No Buzz repository/source, runtime configuration, wallet/payment surface, or
public marketplace/deployment file is modified.

## O — Operations / Ordered Tasks

1. Merge and accept this #426 plan/spec PR before implementation.
2. Define the closed schema and deterministic digest/evaluation rules first.
3. Implement independent assertion evaluation, revocation/expiry precedence,
   stable all-applicable diagnostics, and fail-closed cross-object bindings.
4. Add positive and compound negative fixtures proving no tier/payment/install
   inference, explicit downgrade/hold/refusal, and exact repeated JSON bytes.
5. Add the static install-review handoff and accessible renderer only after the
   validator is complete; prove failures leave no partial output.
6. Run focused checks and full smoke. Update this plan for material divergence
   and request exact-head Oli and Sara reviews.
7. Merge only after local checks, GitHub Actions, review/request/thread
   freshness, Oli PASS, and Sara PASS are green.

## N — Norms

- ADL is canonical; every Buzz package, listing, and handoff is optional,
  one-way, replaceable evidence.
- Evidence tiers are issuer-scoped independent assertions, not trust scores.
- RAP keeps mandate, rail, receipt, dispute/refund, accounting-acceptance, and
  reputation authority; curation may reference but cannot recreate it.
- Static metadata and owner review never become runtime permission, install
  authority, provider configuration, credential access, wallet attachment, or
  delegated spend.
- Expiry, revocation, tampering, and misleading claims remain prominent; never
  hide them to preserve a badge or listing.
- Keep G1 local/static/deterministic. #428 remains gated until #426 and #427 are
  closed green; #429+ remains unauthorized.

## S — Safeguards / Acceptance Checklist

- [ ] Schema is closed at every object boundary and rejects unknown authority-
  bearing fields, duplicate ids, mutable pins, malformed digests/times, and
  caller-supplied verification state.
- [ ] Every assertion is exact-subject, issuer-role, scope, time, evidence, and
  revocation bound; no assertion implies another tier.
- [ ] Receipt-backed without independent payment authority remains
  `paymentMode=none`; Buzz/Nostr/owner/review evidence never enables payment.
- [ ] Expired/revoked assertions show precise status and deterministic
  downgrade/hold/refusal; tampered or ambiguous core subjects refuse.
- [ ] Complete #425 losses and exact false boundary flags appear in JSON,
  Markdown, HTML, and handoff output with cross-surface equality tests.
- [ ] Install handoff always requires a later explicit owner decision and has
  `admitted=false`, `installed=false`, and `started=false`; no executable
  install/start/update URI or command is emitted.
- [ ] Static HTML has one page title and `main`, logical heading order, labels
  and textual statuses that do not rely on color, visible keyboard focus, no
  external assets/scripts/network requests, and escaped untrusted text.
- [ ] Attribution/branding flags remain false and public distribution is held
  under #424 until separately reviewed.
- [ ] Two clean runs from identical explicit files and evaluation time produce
  identical JSON/Markdown/HTML bytes and digests.
- [ ] Planned validation commands:

  ```text
  python3 tests/test_buzz_curation.py
  python3 -m py_compile scripts/buzz_curation.py tests/test_buzz_curation.py
  git diff --check origin/main...HEAD
  PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
  ```

- [ ] Exact-head Oli review covers schema closure, subject/digest binding, tier
  independence, expiry/revocation, misleading authority, no partial output,
  and every denied G1 boundary.
- [ ] Exact-head Sara review covers tier/payment/receipt/reputation wording,
  expiry/revocation prominence, choices, accessibility, and attribution hold.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-08-01 | Initial #426 implementation plan; no curation implementation | Created | Deferred until this plan is accepted |
