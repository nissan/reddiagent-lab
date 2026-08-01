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
| Issuer registry | Closed local authority input | Registry version/digest, issuer id, exact Ed25519 public key, one closed role, allowed tier set, validity interval, and revocation authority; unknown roles or role/tier pairs refuse the assertion |
| Publisher assertion | Provenance, never authority | Stable publisher issuer id/key, exact listing-subject digest, signed publisher preimage, issued/expiry times; can assert `listed` only and cannot imply owner, reviewer, reputation, or payment authority |
| Owner binding record | Re-verifiable pin-bound identity evidence | Complete canonical #424 binding object and signature, binding digest, canonical agent id, ADL digest, Buzz agent key, owner key, lifecycle sequence/state/times, rotation predecessor when present, and revocation target; a digest-only summary is insufficient |
| Tier assertion | One independently signed evidence claim | Assertion id/digest, tier enum, issuer id and registry role, exact listing-subject digest, `asOf`, `expiresAt`, ordered evidence refs/digests, downgrade rule, revocation authority/reference, and Ed25519 signature; no tier inheritance |
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

### Exact bytes, digests, and signatures

All strings must already be Unicode NFC; the validator rejects rather than
normalizes other forms. JSON numbers are forbidden in signed objects (integer
values use decimal strings); duplicate member names are rejected while parsing.
JCS below means the RFC 8785 UTF-8 bytes with no BOM and no trailing newline.
Stored JSON artifact bytes are exactly `JCS(value) + LF`. Raw artifact hashes
cover the complete file bytes, including any final
newline already present. No implementation may normalize report, manifest, or
package bytes before hashing.

| Value | Frozen preimage |
|---|---|
| `adlDigest`, `reportDigest`, `manifestDigest`, `packageDigest` | SHA-256 over the exact referenced local file bytes |
| `listingSubjectDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:listing-subject:v1`, one NUL byte, then JCS of `listingSubject` with only `listingSubjectDigest` omitted |
| `ownerBindingDigest` | SHA-256 over ASCII `reddiagent:buzz:owner-binding:v1`, one NUL byte, then JCS of the complete #424 owner-binding record with only `ownerBindingDigest` and `signature` omitted |
| `issuerRegistryDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:issuer-registry:v1`, one NUL byte, then JCS of the registry with only `issuerRegistryDigest` omitted |
| `tierAssertionDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:tier-assertion:v1`, one NUL byte, then JCS of the assertion with only `tierAssertionDigest` and `signature` omitted |
| `revocationDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:revocation:v1`, one NUL byte, then JCS of the revocation with only `revocationDigest` and `signature` omitted |
| `envelopeDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:envelope:v1`, one NUL byte, then JCS of the complete envelope with only `envelopeDigest`, derived `evaluation`, and all publisher signatures omitted |

The only G1 signature suite is Ed25519. Public keys are 32 lowercase-hex bytes;
signatures are unpadded base64url 64-byte values. A publisher signature signs
ASCII `reddiagent:buzz-curation:publisher:v1`, NUL, the 32 raw bytes decoded
from `envelopeDigest`, NUL, and the 32 raw bytes decoded from
`listingSubjectDigest`. A tier assertion signs ASCII
`reddiagent:buzz-curation:tier-assertion:v1`, NUL, and the 32 raw bytes decoded
from `tierAssertionDigest`; a revocation signs ASCII
`reddiagent:buzz-curation:revocation:v1`, NUL, and the raw bytes decoded from
`revocationDigest`.
The validator recomputes each digest, verifies each signature against the exact
key pinned in the issuer registry, and rejects alternative encodings, suites,
domains, excluded fields, or byte normalization. Publisher signatures bind the
whole unsigned envelope; tier and revocation signatures remain independently
portable but exact-subject bound.

The package is the exact #425 package artifact; its manifest and exporter report
are separate raw-byte inputs. The listing subject carries all three digests and
the canonical ADL digest. The validator also recomputes the manifest's declared
package/report/ADL links, so substituting any one artifact refuses the subject.

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

Issuer authority is a closed mapping: `publisher` may assert `listed` only;
`adl-validator` may assert `validated` only; `human-reviewer` may assert
`reviewed` only; `rap-receipt-authority` may assert `receipt-backed` only; and
`rap-payment-authority` may assert `payment-enabled` only. Each issuer registry
entry contains exactly one role and its exact allowed tier. The registry itself
is pinned by digest in the envelope and owner-reviewed as local input. Unknown
roles, multiple roles, role/tier mismatch, invalid/expired issuer entries, or a
signature under a different key produce `BUZZ_CURATION_ISSUER_UNAUTHORIZED`
and fail only that assertion unless the publisher/listing subject is affected.

Every revocation is a signed object containing a unique id, exact target type
and target digest, issuer id, authority role, monotonically increasing decimal
sequence, `effectiveAt`, reason code, and evidence digest. Only the original
assertion issuer or the registry entry's named revocation authority may revoke
an assertion; only the owner-binding lifecycle authority may revoke/rotate the
owner binding; only the publisher's named revocation authority may revoke the
listing subject. Revocations are ordered by `effectiveAt`, then numeric
sequence, then revocation id. A valid revocation effective at or before the
evaluation time wins over every positive assertion regardless of later file
order; same-sequence conflicts, unauthorized revocations, or contradictory
targets hold the subject and emit an explicit diagnostic.

Every G1 install-review handoff has operational `paymentMode=none`. The positive
informational payment fixture contains a valid, independently signed
`payment-enabled` assertion from a pinned `rap-payment-authority` for the exact
subject, so the evaluator may report that evidence tier as current while the
handoff still says `paymentMode=none`, `paymentExecutionAllowed=false`, and
`walletAttachmentAllowed=false`. It proves that evidence about eligibility is
not payment authorization and performs no payment/network/runtime action. A
second fixture includes receipt-backed evidence without that assertion and
proves payment remains disabled. Another includes a payment-looking Buzz event
or owner signature and emits a blocking misleading-authority diagnostic rather
than a tier.

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
code. Assertion output is ordered by the fixed tier order above and then
assertion id; `currentTiers` uses that fixed tier order and is the set union of
current independently valid assertions. There is no majority, score, or
transitive aggregation.

Decision evaluation is total and uses the first matching row:

| Precedence | Condition | Decision |
|---|---|---|
| 1 | Schema parse/closure failure; duplicate object member or semantic id; core subject/report/manifest/package/envelope digest mismatch; invalid required publisher signature; tier/payment inference; false receipt/reputation claim; executable install/runtime/payment authority; or other tampering | `refused` |
| 2 | Public branding/distribution requested before #424 attribution clearance | `hold` with `BUZZ_CURATION_ATTRIBUTION_HOLD` (never install-authority refusal) |
| 3 | Listing, publisher, owner binding, or issuer registry is expired/revoked/ambiguous; revocation sequence conflicts; required current owner binding cannot be re-verified; or no current `listed` assertion remains | `hold` |
| 4 | Core subject is valid/current and `listed` remains current, but one or more non-core tier assertions is expired, revoked, unauthorized, stale, or invalid | `downgraded` |
| 5 | Core subject and owner binding are valid/current, `listed` is current, every supplied assertion is current and authorized, and no earlier condition applies | `eligible-for-static-review` |

All lower-precedence diagnostics are still emitted. Expiry is effective when
`expiresAt <= evaluationTime`; revocation is effective when `effectiveAt <=
evaluationTime`. Future `asOf`, missing time zones, or unequal representations
of the same instant are invalid. This table determines the same result for any
permutation of assertions, evidence references, or revocations.

### Static review and handoff

The rendered surface starts with one summary region containing the overall
decision, evaluation time, subject status, and any expiry/revocation/hold in
text before tier detail. Every tier name has adjacent textual status, issuer,
`asOf`, expiry, and revocation status in the same table row/card and does not
rely on color, icons, hover, or title attributes. It separates issuer-scoped
claims, shows all #425 losses and boundary denials, and presents exactly four
informational choices: canonical ADL, another adapter, payment-disabled Buzz,
and later separately authorized RAP request-only mode. The Buzz choice produces a static handoff
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
| `tests/fixtures/buzz-curation-*.json` | Valid, informational payment-enabled, downgrade, expired, revoked, tampered, misleading, payment-inference, receipt-only, and install-authority cases |
| `tests/BUZZ-CURATION-REVIEW.html` | Deterministic static review evidence generated from the valid fixture |
| `tests/BUZZ-CURATION-EVIDENCE.md` | Human-readable contract/fixture summary generated from the same evaluation |
| `tests/smoke-validation.sh` | Focused deterministic curation validation and snapshot checks |

No Buzz repository/source, runtime configuration, wallet/payment surface, or
public marketplace/deployment file is modified.

## O — Operations / Ordered Tasks

1. Merge and accept this #426 plan/spec PR before implementation.
2. Define the closed schema and deterministic digest/evaluation rules first.
3. Implement the closed issuer registry, exact preimages/signatures, independent
   assertion evaluation, revocation/expiry precedence, stable all-applicable
   diagnostics, and fail-closed cross-object bindings.
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
  bearing fields, mutable pins, malformed digests/times, and caller-supplied
  verification state. JSON parsing rejects duplicate member names; semantic
  validation rejects duplicate ids across assertions, evidence, incidents,
  reviews, and revocations because JSON Schema alone cannot enforce that
  cross-array uniqueness.
- [ ] Every assertion is exact-subject, issuer-role, scope, time, evidence, and
  revocation bound; no assertion implies another tier.
- [ ] Receipt-backed without independent payment authority remains
  `paymentMode=none`; the informational positive payment-enabled fixture also
  remains operationally `paymentMode=none`; Buzz/Nostr/owner/review evidence
  never enables payment.
- [ ] Expired/revoked assertions show precise status and deterministic
  downgrade/hold/refusal; tampered or ambiguous core subjects refuse.
- [ ] Complete #425 losses, decision, tier statuses, evaluation/expiry/
  revocation data, four choices, attribution hold, and exact false boundary
  flags appear in JSON, Markdown, HTML, and handoff output. Tests extract the
  machine-readable HTML data block and Markdown evidence table and compare each
  value to evaluated JSON and handoff values, then snapshot exact bytes.
- [ ] Install handoff always requires a later explicit owner decision and has
  `admitted=false`, `installed=false`, and `started=false`; no executable
  install/start/update URI or command is emitted.
- [ ] Static HTML declares `lang="en"`, has one non-empty unique page title and
  one `main`, logical heading order with no skipped level, a first summary
  region containing decision/evaluation/status and active holds, tier tables
  with `caption`, scoped column/row headers, adjacent textual status/date/
  expiry/revocation, exactly four named choices, descriptive unique link names,
  visible keyboard focus, no color-only meaning, no external assets/scripts/
  network requests, and escaped untrusted text. Tests parse the HTML and assert
  each condition rather than relying on visual inspection.
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
| 2026-08-01 | Oli/Sara exact-head BLOCK: byte/signature/issuer/revocation/aggregation and objective content/accessibility contracts incomplete | Froze preimages and signature suite; added closed issuer authority, re-verifiable owner record, signed revocation ordering, total precedence, informational payment-positive fixture, attribution hold, and objective cross-surface/accessibility criteria | Still deferred; this bounded step updates the plan only |
