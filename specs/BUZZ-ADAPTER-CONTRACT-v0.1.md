# Optional Buzz Adapter Contract v0.1

_Status: draft | Anchor issue: [#424](https://github.com/reddinft/reddiagent-lab/issues/424) | Update plan: `spdd/prompt/0424-buzz-adapter-contract.md`_

## 1. Purpose and normative boundary

This specification freezes the G1 contract for projecting canonical ADL v0.2
into an optional, version-pinned Buzz target. The words **must**, **must not**,
**should**, **should not**, and **may** carry RFC 2119/RFC 8174 force.

ADL is the only canonical agent definition. A Buzz persona, listing, package,
Nostr event, key, audit entry, or compatibility report must not become a second
definition authority and must not be imported as if it reconstructs ADL.

RAP remains authoritative for payment mandates, authoritative rail
reconciliation, work and eval receipts, disputes/refunds, accounting acceptance,
and reputation eligibility. NIP-OA is provenance, NIP-AM is advisory telemetry,
and Buzz events are context. None is, by itself, spend authority, settlement,
service acceptance, or reputation.

G1 is static, local, deterministic, no-runtime, no-network, and no-credential.
All reports and packages must set these boundary flags to `false`:

```json
{
  "runtimeExecutionAllowed": false,
  "networkAccess": false,
  "relayAccess": false,
  "providerAccess": false,
  "credentialAccess": false,
  "mcpInvocation": false,
  "toolInvocation": false,
  "paymentAccess": false,
  "walletAccess": false,
  "deploymentAllowed": false,
  "bidirectionalImportAllowed": false
}
```

## 2. Canonical source and target pins

Every report and projection package must bind all of the following:

| Field | Rule |
|---|---|
| `canonicalAdl.uri` | Stable source URI or repository-relative source identity; required. |
| `canonicalAdl.apiVersion` | Must equal the validated source value; G1 target is `reddiagent.dev/v0.2`. |
| `canonicalAdl.digest` | Lowercase SHA-256 over the canonical source bytes; required. |
| `canonicalAdl.schemaDigest` | SHA-256 of the exact schema used to validate the source. |
| `canonicalAdl.sourceCommit` | Full source repository commit when repository-backed. |
| `target.kind` | Stable target id `buzz-static-projection`. |
| `target.upstreamCommit` | Full `block/buzz` commit reviewed for compatibility. |
| `target.forkCommit` | Full `reddinft/buzz` commit, even when identical to upstream. |
| `target.adapterCommit` | Full `reddiagent-lab` exporter commit. |
| `target.contractVersion` | This contract version, `0.1`. |
| `target.generatedAt` | Omitted from digest-bearing output or supplied as a caller-pinned value. |

The report is the evidence record. A package must embed the report digest and
the canonical ADL identity fields. Changing any source, schema, adapter,
upstream, or fork pin requires regeneration and review. Missing, abbreviated,
mutable, mismatched, or unreviewed pins block package emission.

The initial research baseline is upstream/fork commit
`d88313f369acfa17973029787ee4c0bbea07fa51`. It is an assessment pin, not a
permanent support promise or authorization to run that source.

## 3. Classification and diagnostic contract

Every row must use exactly one primary classification:

| Classification | Meaning | Package effect |
|---|---|---|
| `direct` | Target artifact preserves the reviewed meaning without inventing authority. | May emit. |
| `lossy` | A reviewed target representation exists but omits or weakens meaning. | May emit only with explicit loss detail. |
| `metadata-only` | Meaning is displayed for review but Buzz cannot enforce it. | May emit only as visibly non-authoritative metadata. |
| `unsupported` | No reviewed target representation exists. | Report emits; package is blocked unless the row is explicitly non-blocking in this contract. |
| `refused` | Emission would expose sensitive data, enable live action, or make a misleading authority claim. | Report emits; package must not emit. |

Diagnostics must be deterministically ordered by ADL path, severity rank, then
code. Each diagnostic contains `code`, `classification`, `severity`, `path`,
`message`, `remediation`, and `blocking`. Stable codes use the `BUZZ_` prefix:

| Code | Trigger | Result |
|---|---|---|
| `BUZZ_ADL_INVALID` | Source fails ADL v0.2 schema/semantic validation. | Refused, blocking. |
| `BUZZ_CANONICAL_REF_MISSING` | URI, digest, schema digest, version, or source commit is absent. | Refused, blocking. |
| `BUZZ_TARGET_PIN_INVALID` | Target pin is missing, mutable, abbreviated, mismatched, or unreviewed. | Refused, blocking. |
| `BUZZ_SEMANTIC_LOSS` | Reviewed representation weakens ADL meaning. | Lossy, visible. |
| `BUZZ_METADATA_NOT_ENFORCED` | Buzz may display but cannot enforce the semantics. | Metadata-only, visible. |
| `BUZZ_SURFACE_UNSUPPORTED` | No reviewed target representation exists. | Unsupported; blocking unless the matrix says report-only. |
| `BUZZ_PUBLIC_SENSITIVE_CONTENT` | Secret, private source, public-sensitive prompt, or unsafe metadata would be emitted. | Refused, blocking. |
| `BUZZ_POLICY_UNRESOLVED` | Policy reference is missing, mismatched, or not statically enforceable. | Refused, blocking. |
| `BUZZ_RUNTIME_CAPABILITY_REFUSED` | Artifact requests runtime, provider, network, tool/MCP invocation, credential, install, or deployment authority. | Refused, blocking. |
| `BUZZ_PAYMENT_AUTHORITY_REFUSED` | Spend/refund authority, wallet material, live rail, or payment execution claim would cross the boundary. | Refused, blocking. |
| `BUZZ_AUTHORITY_CLAIM_REFUSED` | Event/key/audit/telemetry is represented as mandate, settlement, acceptance, or reputation. | Refused, blocking. |
| `BUZZ_IDENTITY_BINDING_INVALID` | Identity join is missing, stale, expired, revoked, ambiguous, or inconsistent. | Refused, blocking. |
| `BUZZ_ONE_WAY_ONLY` | Caller requests Buzz-to-ADL reconstruction or round-trip equivalence. | Refused, blocking. |
| `BUZZ_ATTRIBUTION_REVIEW_REQUIRED` | License/NOTICE/modified-file or downstream branding evidence is incomplete. | Refused for distribution. |
| `BUZZ_UPSTREAM_DRIFT_UNREVIEWED` | Drift check detects unreviewed relevant change or negative-claim dependency. | Refused for release. |

## 4. Complete ADL v0.2 surface matrix

The matrix covers the canonical top-level surface and every supporting semantic
surface named by ADL v0.2. Nested fields inherit their row unless a stricter
refusal rule below applies.

| ADL surface | Primary class | Buzz projection rule | Blocking/refusal override |
|---|---|---|---|
| `apiVersion` | `direct` | Preserve with canonical reference. | Unknown/invalid version: `BUZZ_ADL_INVALID`. |
| `kind` | `direct` | Preserve `Agent` as source kind. | Other kind: `BUZZ_ADL_INVALID`. |
| `metadata.name` | `direct` | Candidate persona display name. | Misleading impersonation/branding claim: refused. |
| `metadata.description` | `direct` | Candidate persona description. | Secret or public-sensitive content: `BUZZ_PUBLIC_SENSITIVE_CONTENT`. |
| `conformance` | `metadata-only` | Display requested/achieved levels and evidence refs. | Must not imply Buzz achieved ADL runtime conformance. |
| `model.capability` | `lossy` | Map to advisory persona capability label. | Target capability must not be inferred. |
| `model.providers` | `metadata-only` | Preserve ordered provider ids as review metadata. | Provider selection/call/credential resolution: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `model.requirements` | `metadata-only` | Preserve required capabilities and loss detail. | Claim of Buzz enforcement: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `model.cost` | `metadata-only` | Advisory budget/cost metadata only. NIP-AM may be referenced as telemetry. | Billing, settlement, or limit authority claim: refused. |
| `harness.instructions.inline` | `lossy` | Emit only reviewed public-safe persona instructions; retain source digest. | Secret/private/public-sensitive content: refused. |
| `harness.instructions.path` | `lossy` | Package reviewed file content plus original path/digest; never host-path authority. | Missing/out-of-root/symlink escape/sensitive content: refused. |
| `harness.tools` | `metadata-only` | List ids, descriptions, schemas, permissions, and policy refs for review. | Any invocation/auto-enable or unsafe/unresolved policy: refused. |
| `harness.functions` | `metadata-only` | List callable contract metadata only. | Execution, credential, network, shell, filesystem mutation, or unresolved policy: refused. |
| `harness.skills` | `lossy` | Package only reviewed static skill description/assets allowed by later #425 rules. | Executable hooks, unsafe paths, unresolved policy, or automatic install: refused. |
| `harness.dataSources` | `metadata-only` | Preserve type, trust, citation, and redacted source identity. | Private credentials/data, unapproved fetch, or unverifiable source boundary: refused. |
| `harness.memory` | `unsupported` | Report mode, retention, privacy, and storage refs; no memory is copied. | Persistent/external memory export, workspace copy, or retention claim: refused. |
| `harness.policies` | `metadata-only` | Preserve normalized policy declarations and report non-enforcement. | Missing/mismatched refs or claim of enforcement: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.evalGates` | `metadata-only` | Preserve gate definitions and evidence refs. | Must not translate Buzz reactions/events into passed gates. |
| `harness.runtime` | `unsupported` | Report target and compatibility only. | Any activation/start/provider resolution: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `harness.deployment` | `unsupported` | Report deployment intent only, with distribution blocked in G1. | Deploy/host/release instruction: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `harness.observability` | `metadata-only` | Preserve required event/redaction/retention contract. | Relay/event presence must not satisfy required trace evidence. |
| `harness.recovery` | `metadata-only` | Preserve disable/rollback expectations for later review. | Claim that deleting a Buzz persona rolls back external state: refused. |
| `extensions.identity` | `direct` | Bind canonical agent identity through the lifecycle in section 5. | Missing/stale/revoked/ambiguous join: `BUZZ_IDENTITY_BINDING_INVALID`. |
| `extensions.x402` | `metadata-only` | Emit only `paymentMode: none` plus redacted external RAP refs. | Spend/refund authority, live rail, wallet, or executable intent: `BUZZ_PAYMENT_AUTHORITY_REFUSED`. |
| `extensions.receipts` | `metadata-only` | Preserve RAP evidence refs and required status. | Buzz event/audit entry represented as RAP receipt or acceptance: refused. |
| `extensions.reputation` | `metadata-only` | Preserve declared RAP evidence refs and eligibility status. | Registry/Buzz presence or event inferred as reputation: refused. |
| reviewed `x-*`/URI extension | `metadata-only` | Preserve namespaced, redacted JSON plus source path. | Authority-like, secret, executable, or unreviewed semantics: unsupported/refused. |

`unsupported` rows are blocking for package emission in G1 unless the exporter
emits no corresponding executable content and the row is explicitly listed here
as report-only: `harness.memory`, `harness.runtime`, and `harness.deployment`.
Their presence must remain visible and cannot be called lossless. Any live or
stateful value within those rows activates the refusal override.

## 5. Identity binding lifecycle

### 5.1 Binding fields

An identity binding must contain:

- `canonicalAgentId`: stable Reddi/RAP identifier, never derived solely from a
  Buzz/Nostr key;
- `canonicalAdlUri`, `canonicalAdlDigest`, and `canonicalAdlVersion`;
- `buzzAgentPubkey`: target agent public key/coordinate;
- `ownerPubkey`: distinct owner identity key when the target supports it;
- `ownerAttestationRef`: signed NIP-OA or equivalent provenance reference;
- `issuedAt`, `notBefore`, `expiresAt`, `sequence`, and `status`;
- `previousBindingDigest` for rotation, when applicable;
- `revocationRef` and `reason` for revoked bindings;
- `bindingDigest` over canonical serialized fields.

The Buzz agent key and owner key must not be interpreted as a wallet, payment
principal, delegated spender, RAP mandate signer, or reputation issuer. NIP-OA
may prove a reviewed owner-to-agent provenance assertion; it does not prove the
owner had payment authority or accepted work.

### 5.2 States and transitions

| State | Entry condition | Allowed transition | Package effect |
|---|---|---|---|
| `proposed` | Complete unsigned/static binding candidate. | `bound` or `revoked` | Report only. |
| `bound` | Owner attestation and all pins verify within validity window. | `active`, `rotating`, `revoked`, `expired` | Report only until explicit activation review. |
| `active` | Current reviewed binding selected for static package. | `rotating`, `revoked`, `expired` | Package may reference it. |
| `rotating` | New higher-sequence binding references the active digest. | New binding `active`; old binding `superseded`; or both `revoked` on ambiguity. | Block until atomic selection is proven. |
| `superseded` | A verified higher-sequence binding is active. | `revoked` | Historical evidence only. |
| `revoked` | Signed/operator-reviewed revocation matches binding. | Terminal | Block immediately. |
| `expired` | `expiresAt` is not later than evaluation time. | Terminal; create a new binding | Block. |

Joins are fail-closed. Conflicting owner claims, equal sequence with different
digests, missing predecessor, digest mismatch, clock ambiguity, stale cache,
revoked predecessor, or missing revocation evidence produces
`BUZZ_IDENTITY_BINDING_INVALID`. Rotation must not reuse a revoked key or silently
extend expiry. Consumers must re-evaluate revocation and expiry whenever a
package is reviewed, installed, or refreshed.

## 6. Authority separation

| Buzz/Nostr evidence | Permitted interpretation | Forbidden interpretation |
|---|---|---|
| NIP-OA owner/agent assertion | Provenance claim tied to exact key, digest, and validity window. | RAP/AP2 mandate, wallet delegation, spend authority, or owner reputation. |
| NIP-AM usage/cost event | Advisory telemetry to reconcile against authoritative evidence. | Invoice, billing truth, settled amount, budget authority, or accounting acceptance. |
| Signed Buzz event | Attributable context from a key at a point in time. | Human approval, task acceptance, settlement, eval pass, dispute closure, or reputation. |
| Buzz audit chain | Tamper-evident local history under its documented threat assumptions. | Tamper-resistant external truth, authoritative rail receipt, or non-repudiation by itself. |
| Channel membership/reaction | Collaboration context. | Principal authority, approval, mandate, or service completion. |

Any projection text or field name that implies a forbidden interpretation must
be refused with `BUZZ_AUTHORITY_CLAIM_REFUSED`.

## 7. Adapter, upstream, and thin-fork decision record

Integration choices must be evaluated in this order:

1. **External adapter:** preferred. Use public/stable Buzz inputs and keep all
   Reddi policy, receipts, and curation outside Buzz core.
2. **Upstream extension:** allowed only when the adapter cannot represent a
   generally useful, non-Reddi-specific surface and a reviewed upstream issue/PR
   is appropriate. Upstream contact needs separately recorded authorization.
3. **Minimal core patch:** last resort. Each patch needs a named missing
   extension point, owner, test, upstream-drift risk, rollback instruction, and
   deletion condition. No unrelated fork divergence is allowed.

The decision record must include `chosenLayer`, evidence for each rejected
higher layer, affected paths/API surfaces, fork delta count, upstream candidate,
maintenance owner, and removal trigger. #425 starts at layer 1.

### Pin and drift policy

A supported pin set contains exact ADL/schema, adapter, upstream Buzz, and fork
commits plus artifact digests. A rollback pin is a previously reviewed complete
pin set, never merely "latest" or a branch name.

Drift must be checked before each release candidate, after a relevant upstream
security/identity/persona/event/package change, and at least weekly while a
release lane is active. The report records merge-base, commits changed, relevant
paths, linked upstream issues, classification changes, negative claims requiring
re-verification through #418, reviewer, and decision. Relevant unreviewed drift
blocks release with `BUZZ_UPSTREAM_DRIFT_UNREVIEWED`.

Rollback regenerates a package from canonical ADL using the rollback pin set,
revokes/supersedes the newer identity binding if required, and retains both
reports. Rollback must never reconstruct ADL from Buzz state or assert that
external/runtime state was reverted in G1.

## 8. Attribution and branding manifest

The assessed Buzz pin is Apache-2.0 licensed. This contract is not legal advice;
public distribution requires reviewed legal/brand evidence. The manifest must
record, at minimum:

| Manifest item | Required evidence/status |
|---|---|
| Upstream work and pin | `block/buzz` repository URL and full commit. |
| Downstream fork and pin | `reddinft/buzz` URL and full commit. |
| License | Unmodified Apache License 2.0 text included with source/object distribution as applicable. |
| NOTICE | Presence and digest at the selected pin; the assessed pin has no repository-root `NOTICE`, but any later NOTICE must be preserved as required. |
| Copyright/attribution notices | Retained in source and distribution materials where required. |
| Modified files | Machine-readable list plus prominent modification notices and dates where required by Apache-2.0 section 4. |
| Source/object distribution | Applicable license, notice, and attribution paths for each artifact form. |
| Third-party assets/dependencies | Separate license inventory; Apache-2.0 for Buzz does not override them. |
| Downstream name | `pending-review` until a non-infringing name is approved. |
| Public disclaimer | `pending-review`; must state optional compatibility, no upstream endorsement, ADL canonicality, and RAP authority boundaries. |
| Trademark/brand review | Explicit reviewer, date, scope, and decision. No inference from the software license. |

Until every applicable item is reviewed, `publicDistributionAllowed` and
`publicBrandingAllowed` must be `false`, and distribution is refused with
`BUZZ_ATTRIBUTION_REVIEW_REQUIRED`.

## 9. G1 release and rollback checklist

### Release candidate

- [ ] Exact canonical ADL URI/version/digest/schema/source commit validate.
- [ ] Exact adapter/upstream/fork pins and generated artifact digests validate.
- [ ] Every ADL surface has one ordered mapping row and stable diagnostics.
- [ ] No blocking `refused` or disallowed `unsupported` row exists.
- [ ] Lossy and metadata-only rows are prominent and machine-readable.
- [ ] Identity binding is current, unique, unexpired, unrevoked, and pin-bound.
- [ ] All G1 boundary flags are false and negative fixtures prove refusal.
- [ ] NIP-OA/NIP-AM/event/audit wording passes authority-separation review.
- [ ] Drift and #418 negative-claim re-verification are current.
- [ ] Attribution manifest is complete; public branding/distribution remain
      false unless separately reviewed and approved.
- [ ] Focused tests, snapshot determinism, `git diff --check`, full deterministic
      smoke, exact-head GitHub Actions, and Oli QA pass.
- [ ] Sara approves public-facing identity, attribution, and disclaimer wording.

### Rollback readiness

- [ ] A previously reviewed complete rollback pin set and report are retained.
- [ ] Package withdrawal/revocation references are defined without runtime use.
- [ ] Identity rotation/revocation does not leave two active bindings.
- [ ] Canonical ADL remains unchanged and independently retrievable.
- [ ] New and rollback reports expose classification differences.
- [ ] Incident record names trigger, affected artifacts, owner, evidence, and
      next approval gate.

Passing this checklist completes only #424's reviewed contract gate. It does
not authorize #425 implementation merge by itself, and it never authorizes
Buzz installation/runtime, relay/agent startup, credentials/providers,
wallets/payments, localnet/devnet/mainnet, testers, deployment, or production.
