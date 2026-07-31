# REASONS-LITE — Optional Buzz adapter contract

_Status: draft | Owner: Loki on behalf of Nissan | Project: reddiagent-lab | Issue: [#424](https://github.com/reddinft/reddiagent-lab/issues/424)_

SPDD-LITE is required because this boundary crosses identity, privacy, runtime,
payment, licensing, and future deployment concerns. This artifact is the update
plan for `specs/BUZZ-ADAPTER-CONTRACT-v0.1.md`; implementation must stop and
update both documents if the reviewed contract changes materially.

## R — Requirements / Definition of Done

Freeze a one-way, optional ADL v0.2 to Buzz projection contract before an
exporter or runtime integration is built. ADL remains canonical, Buzz remains a
version-pinned target, and RAP remains authoritative for mandates, rail truth,
work/eval receipts, disputes/refunds, accounting acceptance, and reputation
eligibility.

**DoD checklist:**

- [ ] The contract classifies every ADL v0.2 surface as `direct`, `lossy`,
  `metadata-only`, `unsupported`, or `refused` and assigns stable diagnostics.
- [ ] Canonical ADL URI/digest/version and one-way projection semantics are
  mandatory and machine-checkable.
- [ ] Canonical agent, ADL digest, Buzz agent key, and owner key bindings define
  expiry, rotation, revocation, and fail-closed joins.
- [ ] NIP-OA, NIP-AM, Buzz events, and Buzz audit evidence cannot be interpreted
  as mandate, settlement, service acceptance, or reputation authority.
- [ ] Adapter/fork decision order, source/support/rollback pins, drift checks,
  attribution obligations, branding hold, and rollback criteria are explicit.
- [ ] G1 remains deterministic, static, local, no-runtime, no-network, and
  no-credential.
- [ ] Oli reviews safety/contract completeness and Sara reviews public wording,
  attribution, and branding before this spec is accepted.

Out of scope: Buzz source changes; upstream contact; runtime, relay, or agent
startup; install; bidirectional import; provider or credential access; wallet,
payment, or settlement; public distribution/branding; deployment; devnet; and
mainnet.

## E — Entities / Handoff Objects

| Entity / object | Purpose | Key states/fields | Existing or new? |
|---|---|---|---|
| Canonical ADL document | Sole definition authority | URI, `apiVersion`, digest, and source commit when repository-backed | Existing |
| Compatibility report | Complete, deterministic loss/refusal evidence | source/target pins, mapping rows, diagnostics, boundary flags | New in #425 |
| Buzz projection package | Optional, non-canonical static target | report digest, persona/listing files, no import claim | New in #425 |
| Identity binding | Joins canonical identity to Buzz provenance | immutable canonical identity fields and emergency-revocation scope; owner-signed binding proof; fully signed, sequenced lifecycle records | New |
| Source pin set | Makes drift and rollback reviewable | upstream, fork, adapter, ADL/schema, supported and rollback commits | New |
| Attribution manifest | Records Apache-2.0 and branding review evidence | license paths, NOTICE state, modified files, disclaimer status | New |

## A — Approach / Key Decisions

- Derive a report from validated ADL, then optionally emit a Buzz package. Never
  derive canonical ADL from a Buzz persona, event stream, or package.
- Extend the existing static export-target parity machinery in #425 instead of
  creating another compatibility vocabulary.
- Choose integration surfaces in this order: external adapter, reviewed
  upstream extension, then minimal reversible core patch. A lower option needs
  recorded evidence that every higher option is insufficient.
- Treat Nostr/Buzz identity and events as provenance/context only. RAP and the
  authoritative payment rail keep their existing authority.
- Require a domain-separated owner signature over the immutable canonical
  ADL/agent/Buzz/owner binding digest, including the exact empty or enumerated
  emergency-revocation authority/scope array; exclude derived lifecycle status
  and fold separately signed, sequenced transition/revocation evidence to
  derive it. The owner proof signs one exact RFC 8785 metadata envelope whose
  binding digest is the 64-character lowercase-hex text, never decoded raw
  digest bytes. Lifecycle records fold by a fully specified ascending total
  order, including chronological instant, numeric sequence, enumerated action
  rank, and unsigned-byte evidence-digest comparison. Canonical preimages and
  evidence-digest inclusion rules are exact. NIP-OA alone does not bind the ADL
  digest.
- Reject public-sensitive content, unresolved policies, executable/runtime
  semantics, embedded spend authority, and unprovable payment/reputation claims.

Rejected alternatives: making Buzz canonical, silent best-effort export,
bidirectional synchronization, carrying wallet authority in a Buzz key, and
starting with a maintained core fork.

Known tradeoff: a useful projection will intentionally omit or display as
metadata many ADL harness semantics. Users must retain the canonical ADL and
compatibility report to understand that loss.

## S — Structure / Files Touched

| Surface | Expected change | Owner/gate |
|---|---|---|
| `specs/BUZZ-ADAPTER-CONTRACT-v0.1.md` | Normative G1 boundary contract | #424 |
| `spdd/prompt/0424-buzz-adapter-contract.md` | Durable update plan and prompt/code sync | #424 |
| `scripts/static_export_target_parity.py` | Add Buzz report row using existing vocabulary | #425 |
| `scripts/buzz_export.py` | Deterministic report and optional static projection | #425 |
| `tests/fixtures/buzz-*` | Positive, lossy, unsupported, refusal, identity, and pin fixtures | #425 |
| `tests/test_buzz_export.py` | Mapping, determinism, refusal, one-way, and boundary assertions | #425 |
| `tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md` | Buzz parity evidence | #425 |
| Marketplace envelope/schema surfaces | Evidence tiers and optional install handoff only | #426 |
| Threat model and negative regression fixtures | G2/G3 preconditions; no execution | #427 |

## O — Operations / Ordered Tasks

1. Accept #424's contract, diagnostics, identity lifecycle, fork policy,
   attribution manifest, and release/rollback checklist after Oli/Sara review.
2. In #425, add the Buzz row to existing parity output before creating the
   exporter, so classification vocabulary cannot drift.
3. Implement report generation first; prove deterministic pins, complete
   surface coverage, and refusal behavior with local fixtures.
4. Permit static package emission only when the report has no `refused` or
   blocking `unsupported` rows; retain visible loss metadata.
5. In #426, consume the report and identity binding in the Reddi-owned curation
   envelope without adding install/runtime authority.
6. In #427, freeze abuse cases and G2/G3 safeguards before any request to start
   local Buzz work.

## N — Norms

- ADL v0.2 and its digest are canonical; every Buzz artifact is disposable.
- Reuse stable diagnostics and static parity structures before adding fields.
- Report semantic loss; never infer missing authority or silently downgrade.
- Preserve RAP separation across payment, receipts, disputes, and reputation.
- Keep secrets and public-sensitive prompts out of reports and artifacts.
- Keep #428–#433 authorization-gated; G1 issue existence grants no runtime work.
- Update this REASONS artifact with any material implementation divergence.

## S — Safeguards / Acceptance Checklist

- [ ] External services are unconfigured and unused; all G1 boundary flags are
  false and any attempted live action is refused before resolution.
- [ ] Buzz/Nostr keys cannot be reused or inferred as wallet, mandate, payment,
  service-acceptance, or reputation authority.
- [ ] Expired, revoked, mismatched, stale, or ambiguous identity/pin evidence
  blocks package emission.
- [ ] Public distribution remains blocked until downstream name, disclaimer,
  license/NOTICE state, modified-file notices, and trademark review pass.
- [ ] Rollback means selecting a previously reviewed adapter/source pin and
  regenerating from canonical ADL; it never imports state from Buzz into ADL.
- [ ] Docs validation: `python3 scripts/check_markdown_links.py` if present,
  otherwise scoped source-reference inspection plus `git diff --check`.
- [ ] Oli and Sara review this artifact and the normative spec on the exact PR
  head before acceptance/merge.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-07-31 | Initial #424 contract; no implementation yet | Created | Deferred to #425–#427 |
| 2026-07-31 | Oli found unsigned ADL identity binding, ambiguous refusal-code overrides, and an inconsistent source-commit rule | Require owner-signed full binding digest, map every override to stable codes with all-applicable ordering, and require source commit only for repository-backed ADL | Still deferred to #425–#427 |
| 2026-07-31 | Sara found mutable lifecycle status inside the signed binding digest and a conflicting missing-instruction-path diagnostic | Make the binding digest immutable, derive status from signed lifecycle evidence, and distinguish invalid/missing path fields from unavailable referenced files | Still deferred to #425–#427 |
| 2026-07-31 | Sara found ambiguous owner-proof digest bytes and unspecified lifecycle-fold directions/comparisons | Define the exact owner-proof JCS preimage using lowercase-hex digest text and bind all proof metadata; define every ascending fold key, action rank, and raw-byte digest comparison | Still deferred to #425–#427 |
