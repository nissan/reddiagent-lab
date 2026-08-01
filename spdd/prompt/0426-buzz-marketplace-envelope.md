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
| Listing subject | Exact immutable thing being curated | Canonical ADL URI/API version/source digest/schema digest/source commit when repository-backed; exact #425 report, persona, manifest, and artifact-set digests; upstream/fork/adapter 40-hex pins; #424 contract version |
| Role trust policy | External authority root input | Separate caller-pinned local file and digest containing one exact Ed25519 root key per closed role; the publisher, owner, listing, envelope, and issuer registry cannot add or replace roots |
| Issuer registry | Closed local assignment input | Registry version/digest plus independently root-signed assignment for each issuer id, exact Ed25519 key, one closed role/tier, validity interval, assignment sequence, and revocation key; an unsigned/self-signed entry grants no authority |
| Publisher assertion | Provenance, never authority | Stable publisher issuer id/key, exact listing-subject digest, signed publisher preimage, issued/expiry times; can assert `listed` only and cannot imply owner, reviewer, reputation, or payment authority |
| Owner binding record | Re-verifiable pin-bound identity evidence | Complete canonical #424 binding object and signature, binding digest, canonical agent id, ADL digest, Buzz agent key, owner key, lifecycle sequence/state/times, rotation predecessor when present, and revocation target; a digest-only summary is insufficient |
| Tier assertion | One independently signed evidence claim | Assertion id/digest, tier enum, issuer id and registry role, exact listing-subject digest, `asOf`, `expiresAt`, ordered evidence refs/digests, downgrade rule, revocation authority/reference, and Ed25519 signature; no tier inheritance |
| Review record | Scoped human review evidence | Reviewer id/role, exact subject digest and scope, reviewed time, expiry, decision, findings refs; cannot certify unreviewed fields |
| Incident/revocation record | Immediate downgrade/withdrawal input | Record id, supported target type and exact digest, reason code, effective time, scoped sequence, evidence digest, authorized signer; #424 owner lifecycle records remain separate canonical inputs |
| Permission/loss disclosure | Owner review surface | Complete #425 boundary flags, ordered loss rows/diagnostics, explicit `paymentMode=none`, install/runtime/network/tool/wallet/spend denials |
| Install-review handoff | Static input for later #428 review | Envelope/report/persona/manifest/artifact-set digests, exact pins, warnings, choices, required owner-decision state; `admitted=false`, `installed=false`, `started=false`, every capability false |
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
  --adl <canonical-adl> --report <compatibility-report.json> \
  --persona <persona.json> --manifest <manifest.json> \
  --identity-binding <424-binding.json> --role-trust-policy <roots.json> \
  --issuer-registry <assignments.json> \
  --evaluation-time <pinned-utc> --json
python3 scripts/buzz_curation.py render --envelope <json> \
  --adl <canonical-adl> --report <compatibility-report.json> \
  --persona <persona.json> --manifest <manifest.json> \
  --identity-binding <424-binding.json> --role-trust-policy <roots.json> \
  --issuer-registry <assignments.json> \
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
| `adlDigest`, `reportDigest`, `personaDigest`, `manifestDigest` | SHA-256 over each exact explicit local file's bytes |
| `artifactSetDigest` | SHA-256 over ASCII `reddiagent:buzz-export:artifact-set:v1`, one NUL byte, then JCS of exactly `{reportDigest,personaDigest,manifestDigest}`; this names the #425 three-file package without pretending a directory has portable raw bytes |
| `listingSubjectDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:listing-subject:v1`, one NUL byte, then JCS of `listingSubject` with only `listingSubjectDigest` omitted |
| `bindingDigest` | Consumed and recomputed unchanged by the exact #424/#425 verifier: domain `reddiagent-buzz-identity-binding-v1` and only the immutable fields defined in #424 section 5.1; #426 defines no owner-binding preimage |
| `roleTrustPolicyDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:role-trust-policy:v1`, one NUL byte, then JCS of the externally supplied policy with only `roleTrustPolicyDigest` omitted |
| `issuerRegistryDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:issuer-registry:v1`, one NUL byte, then JCS of the registry with only `issuerRegistryDigest` omitted |
| `issuerAssignmentDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:issuer-assignment:v1`, one NUL byte, then JCS of the assignment with only `issuerAssignmentDigest` and `rootSignature` omitted |
| `tierAssertionDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:tier-assertion:v1`, one NUL byte, then JCS of the assertion with only `tierAssertionDigest` and `signature` omitted |
| `revocationDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:revocation:v1`, one NUL byte, then JCS of the revocation with only `revocationDigest` and `signature` omitted |
| `envelopeDigest` | SHA-256 over ASCII `reddiagent:buzz-curation:envelope:v1`, one NUL byte, then JCS of the complete envelope with only `envelopeDigest`, derived `evaluation`, and all publisher signatures omitted |

The only G1 signature suite is Ed25519. Public keys are 32 lowercase-hex bytes;
signatures are unpadded base64url 64-byte values. A publisher signature signs
ASCII `reddiagent:buzz-curation:publisher:v1`, NUL, the 32 raw bytes decoded
from `envelopeDigest`, NUL, and the 32 raw bytes decoded from
`listingSubjectDigest`. A tier assertion signs ASCII
`reddiagent:buzz-curation:tier-assertion:v1`, NUL, and the 32 raw bytes decoded
from `tierAssertionDigest`. Each issuer assignment is signed by the exact
role-specific root over ASCII `reddiagent:buzz-curation:issuer-assignment:v1`,
NUL, and the 32 raw bytes decoded from `issuerAssignmentDigest`; a revocation signs ASCII
`reddiagent:buzz-curation:revocation:v1`, NUL, and the raw bytes decoded from
`revocationDigest`.
The validator recomputes each digest, first authenticates every registry
assignment against the exact role root in the separately pinned trust policy,
then verifies assertion signatures against the assigned issuer key. It rejects
alternative encodings, suites, domains, excluded fields, byte normalization,
publisher/owner-controlled trust roots, and registry entries whose root role
does not equal their asserted role. Publisher signatures bind the whole
unsigned envelope; tier and revocation signatures remain independently portable
but exact-subject bound.

The #425 package is supplied as the three explicit regular, non-symlink local
files emitted by `write_package`: `compatibility-report.json`, `persona.json`,
and `manifest.json`, plus the canonical ADL input. The validator hashes their
raw bytes and requires every JSON file to equal `JCS(parsed) + LF`. Before any
`artifactSetDigest` is derived, `manifest.files` must be the exact ordered
two-row inventory emitted by #425: `compatibility-report.json` followed by
`persona.json`, each with its exact media type, raw-byte length, and raw-byte
SHA-256; duplicate, extra, missing, reordered, or mismatched rows refuse. The
validator also requires `manifest.reportDigest == reportDigest`.

Pin ownership is deliberately asymmetric: the listing's `upstreamCommit`,
`forkCommit`, and `adapterCommit` each compare only to the same-named field in
`compatibility-report.json.target`. `persona.json` has no source-pin fields, so
the validator neither requires nor synthesizes any. Report/persona agreement is
limited to the fields #425 actually shares: `report.canonicalAdl` equals
`persona.source`; `report.surfaceRows` equals `persona.lossReport` in exact
order; `paymentMode` is `none` in both; and every shared #425 canonical/one-way
and false boundary flag is equal and retains its required false value. The
canonical ADL raw-byte digest and supplied URI/version/source-commit conditions
must independently match `report.canonicalAdl`. Only after the inventory and
all owned cross-links pass does the validator derive `artifactSetDigest`; there
is no free-form `packageDigest`. A changed ADL, report, persona, manifest,
inventory row, owned pin, shared field, or link refuses the subject.

The complete `--identity-binding` file is passed to the same #424 verifier used
by #425 (factored without semantic changes from `buzz_export.py` if sharing is
needed). It recomputes the immutable `bindingDigest`, verifies the exact
`ownerBindingProof`, all `lifecycleEvidence`, every `relatedBindings` proof and
activation, relationship/sequence chronology, expiry, rotation, supersession,
and revocation at the pinned evaluation time. The curation envelope carries
only that verified digest/status summary and requires it to equal the #425
report's identity summary; it never reconstructs, abbreviates, or independently
folds owner lifecycle evidence.

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
`rap-payment-authority` may assert `payment-enabled` only. The external trust
policy contains exactly one preconfigured root for each role and is not signed
or extended by any publisher, owner, listing, envelope, or registry key. Each
registry entry contains exactly one role/tier and an assignment signed by that
role's root. In particular only the externally pinned RAP receipt/payment roots
can delegate those roles: an owner or publisher key cannot self-designate as a
RAP authority even if it signs both registry and assertion. Unknown/missing
roots, multiple roles, role/tier mismatch, invalid/expired/root-signature-failed
assignments, or a signature under a different key produce
`BUZZ_CURATION_ISSUER_UNAUTHORIZED` and fail only that assertion unless the
publisher/`listed` assertion is affected.

Curation revocations support exactly two target types: `tier-assertion` targets
an exact `tierAssertionDigest`, and `issuer-assignment` targets an exact
`issuerAssignmentDigest`. Owner-binding rotation/revocation is forbidden in
this array and is evaluated only by the unchanged #424 lifecycle verifier.
Each curation revocation contains a unique id, target type/digest, signer id/key,
decimal sequence, `effectiveAt`, reason code, and evidence digest. Assertion
revocation is authorized only by that assignment's named revocation key;
assignment revocation only by the matching role trust root. Sequence scope is
the tuple `(targetType,targetDigest,authorizedSignerKey)`; within that scope
positive sequences are unique and strictly increase with chronological
`effectiveAt`. Records sort by target type, decoded target digest, parsed
`effectiveAt`, integer sequence, then decoded revocation digest. Array order has
no authority. An effective valid revocation is irreversible and wins over its
target and every later positive claim about that target.

Unknown target types, absent targets, wrong target digests, wrong role roots,
unauthorized signers, invalid signatures/evidence digests, non-positive or
duplicate sequences, decreasing sequence/time pairs, or same-sequence
conflicts are malformed supplied authority evidence: emit
`BUZZ_CURATION_REVOCATION_INVALID` and `refused`. A well-formed effective
revocation of the publisher/`listed` assertion or its issuer assignment yields
`hold`; a well-formed effective revocation of another assertion/assignment
yields `downgraded`. Incidents are separately issuer-scoped advisory evidence
and cannot revoke anything.

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
- `BUZZ_CURATION_REVOCATION_INVALID`
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
| 1 | Schema parse/closure failure; duplicate object member or semantic id; core subject/report/persona/manifest/artifact-set/envelope digest mismatch; invalid required publisher signature; invalid/unauthorized/wrong-target revocation; tier/payment inference; false receipt/reputation claim; executable install/runtime/payment authority; or other tampering | `refused` |
| 2 | Public branding/distribution requested before #424 attribution clearance | `hold` with `BUZZ_CURATION_ATTRIBUTION_HOLD` (never install-authority refusal) |
| 3 | Listing/publisher assertion, its authenticated issuer assignment, owner binding, role trust policy, or issuer registry is expired/revoked/ambiguous; required current #424 binding cannot be re-verified; or no current `listed` assertion remains | `hold` |
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
deployment. Authority-request fields are separate from the two review-intent
fields `publicDistributionRequested` and `publicBrandingRequested`. Setting an
authority flag true emits `BUZZ_CURATION_INSTALL_AUTHORITY_REFUSED` and produces
no handoff/render output. Setting either review-intent field true while #424
clearance remains false instead produces the static review and handoff with all
authority flags still false, decision `hold`, and only
`BUZZ_CURATION_ATTRIBUTION_HOLD`; it is never caught by the authority refusal.

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
   Include three isolated listing/report pin-mismatch fixtures—one each for
   `upstreamCommit`, `forkCommit`, and `adapterCommit`—without adding pin fields
   to the persona.
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
- [ ] Each issuer assignment verifies under a separately pinned role-specific
  root; owner/publisher self-designation and especially false RAP authority are
  refused. Tests swap each root, assignment role, issuer key, and signature.
- [ ] The exact #424 verifier and complete binding input are reused, including
  proof, lifecycle, related-binding, rotation, revocation, expiry, and report-
  summary equality tests; #426 defines no alternate owner-binding digest/fold.
- [ ] Explicit #425 ADL/report/persona/manifest files form a checked inventory
  and artifact-set digest chain; mutation or substitution of any byte, path,
  length, digest, owned pin, shared canonical ADL field, ordered loss, or
  boundary refuses deterministically. Listing pins compare only to
  `report.target`; report/persona parity covers only their actual shared fields,
  and separate negative fixtures mismatch each of the three pins without
  inventing persona fields.
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
  under #424 until separately reviewed. Dedicated tests prove branding/
  distribution review intent renders a hold artifact while every true install,
  runtime, network, tool, wallet, payment, or deployment authority request
  refuses with no output.
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
| 2026-08-01 | Fresh Oli/Sara BLOCK: registry entries could self-authorize RAP roles, #424 binding and #425 package chains were redefined/incomplete, revocation scope was partial, and branding hold contradicted the catch-all authority refusal | Added external role-root-signed issuer assignments; unchanged complete #424 verifier reuse; explicit ADL/report/persona/manifest inventory and artifact-set chain; exhaustive curation revocation targets/scope/precedence; and distinct branding/distribution review intent | Still deferred; this bounded step updates the plan only |
| 2026-08-01 | Sara exact-head BLOCK: the plan required persona source pins that #425 does not emit and did not order inventory verification before the artifact-set digest | Assigned all three pins solely to `report.target`; limited report/persona parity to actual shared canonical ADL, ordered loss, payment-none, and false-boundary fields; made exact manifest inventory verification precede digest derivation; required one negative fixture per listing/report pin | Still deferred; this bounded step updates the plan only |
