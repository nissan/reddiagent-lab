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
| `canonicalAdl.sourceCommit` | Full source repository commit; required only when `canonicalAdl.uri` identifies repository-backed content, otherwise omitted. |
| `target.kind` | Stable target id `buzz-static-projection`. |
| `target.upstreamCommit` | Full `block/buzz` commit reviewed for compatibility. |
| `target.forkCommit` | Full `reddinft/buzz` commit, even when identical to upstream. |
| `target.adapterCommit` | Full `reddiagent-lab` exporter commit. |
| `target.contractVersion` | This contract version, `0.1`. |
| `target.generatedAt` | Omitted from digest-bearing output or supplied as a caller-pinned value. |

The report is the evidence record. A package must embed the report digest and
the canonical ADL identity fields. Changing any source, schema, adapter,
upstream, or fork pin requires regeneration and review. Missing, abbreviated,
mutable, mismatched, or unreviewed required pins block package emission. A
repository-backed canonical URI without `canonicalAdl.sourceCommit` is a
missing required pin; a non-repository source does not invent one.

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
| `BUZZ_CANONICAL_REF_MISSING` | URI, digest, schema digest, or version is absent, or a repository-backed source commit is absent. | Refused, blocking. |
| `BUZZ_INSTRUCTION_FILE_UNAVAILABLE` | A non-empty `harness.instructions.path` resolves within the reviewed source root but the referenced file is absent, unreadable, or not a regular file. | Refused, blocking. |
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

Every applicable diagnostic must be emitted. When one value activates more
than one refusal rule, the exporter must not choose between them: it emits all
applicable codes and orders them by ADL path, severity rank, then code as
specified above. The matrix below maps each refusal trigger to its required
code, so #425 must not invent policy or collapse a compound failure.

## 4. Complete ADL v0.2 surface matrix

The matrix covers the canonical top-level surface and every supporting semantic
surface named by ADL v0.2. Nested fields inherit their row unless a stricter
refusal rule below applies.

| ADL surface | Primary class | Buzz projection rule | Blocking/refusal override |
|---|---|---|---|
| `apiVersion` | `direct` | Preserve with canonical reference. | Unknown/invalid version: `BUZZ_ADL_INVALID`. |
| `kind` | `direct` | Preserve `Agent` as source kind. | Other kind: `BUZZ_ADL_INVALID`. |
| `metadata.name` | `direct` | Candidate persona display name. | Impersonation or false authority: `BUZZ_AUTHORITY_CLAIM_REFUSED`; unreviewed public branding: `BUZZ_ATTRIBUTION_REVIEW_REQUIRED`. |
| `metadata.description` | `direct` | Candidate persona description. | Secret or public-sensitive content: `BUZZ_PUBLIC_SENSITIVE_CONTENT`. |
| `conformance` | `metadata-only` | Display requested/achieved levels and evidence refs. | Buzz-achieved ADL runtime conformance claim: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `model.capability` | `lossy` | Map to advisory persona capability label. | Inferred target capability: `BUZZ_METADATA_NOT_ENFORCED`. |
| `model.providers` | `metadata-only` | Preserve ordered provider ids as review metadata. | Provider selection/call/credential resolution: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `model.requirements` | `metadata-only` | Preserve required capabilities and loss detail. | Claim of Buzz enforcement: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `model.cost` | `metadata-only` | Advisory budget/cost metadata only. NIP-AM may be referenced as telemetry. | Billing, settlement, or limit-authority claim: `BUZZ_PAYMENT_AUTHORITY_REFUSED`. |
| `harness.instructions.inline` | `lossy` | Emit only reviewed public-safe persona instructions; retain source digest. | Secret/private/public-sensitive content: `BUZZ_PUBLIC_SENSITIVE_CONTENT`. |
| `harness.instructions.path` | `lossy` | Package reviewed file content plus original path/digest; never host-path authority. | Missing/empty field: `BUZZ_ADL_INVALID`; absent, unreadable, or non-regular referenced file: `BUZZ_INSTRUCTION_FILE_UNAVAILABLE`; out-of-root/symlink escape/sensitive content: `BUZZ_PUBLIC_SENSITIVE_CONTENT`. |
| `harness.tools` | `metadata-only` | List ids, descriptions, schemas, permissions, and policy refs for review. | Invocation/auto-enable: `BUZZ_RUNTIME_CAPABILITY_REFUSED`; unsafe/unresolved policy: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.functions` | `metadata-only` | List callable contract metadata only. | Execution, credential, network, shell, or filesystem mutation: `BUZZ_RUNTIME_CAPABILITY_REFUSED`; unresolved policy: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.skills` | `lossy` | Package only reviewed static skill description/assets allowed by later #425 rules. | Executable hooks or automatic install: `BUZZ_RUNTIME_CAPABILITY_REFUSED`; unsafe path: `BUZZ_PUBLIC_SENSITIVE_CONTENT`; unresolved policy: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.dataSources` | `metadata-only` | Preserve type, trust, citation, and redacted source identity. | Private credential/data: `BUZZ_PUBLIC_SENSITIVE_CONTENT`; unapproved fetch: `BUZZ_RUNTIME_CAPABILITY_REFUSED`; unverifiable source boundary: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.memory` | `unsupported` | Report mode, retention, privacy, and storage refs; no memory is copied. | Persistent/external memory export or workspace copy: `BUZZ_PUBLIC_SENSITIVE_CONTENT`; claim that Buzz enforces retention: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `harness.policies` | `metadata-only` | Preserve normalized policy declarations and report non-enforcement. | Missing/mismatched refs or claim of enforcement: `BUZZ_POLICY_UNRESOLVED`. |
| `harness.evalGates` | `metadata-only` | Preserve gate definitions and evidence refs. | Buzz reaction/event translated into a passed gate: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `harness.runtime` | `unsupported` | Report target and compatibility only. | Any activation/start/provider resolution: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `harness.deployment` | `unsupported` | Report deployment intent only, with distribution blocked in G1. | Deploy/host/release instruction: `BUZZ_RUNTIME_CAPABILITY_REFUSED`. |
| `harness.observability` | `metadata-only` | Preserve required event/redaction/retention contract. | Relay/event presence claimed as required trace evidence: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `harness.recovery` | `metadata-only` | Preserve disable/rollback expectations for later review. | Claim that deleting a Buzz persona rolls back external state: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `extensions.identity` | `direct` | Bind canonical agent identity through the lifecycle in section 5. | Missing/stale/revoked/ambiguous join: `BUZZ_IDENTITY_BINDING_INVALID`. |
| `extensions.x402` | `metadata-only` | Emit only `paymentMode: none` plus redacted external RAP refs. | Spend/refund authority, live rail, wallet, or executable intent: `BUZZ_PAYMENT_AUTHORITY_REFUSED`. |
| `extensions.receipts` | `metadata-only` | Preserve RAP evidence refs and required status. | Buzz event/audit entry represented as RAP receipt or acceptance: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| `extensions.reputation` | `metadata-only` | Preserve declared RAP evidence refs and eligibility status. | Registry/Buzz presence or event inferred as reputation: `BUZZ_AUTHORITY_CLAIM_REFUSED`. |
| reviewed `x-*`/URI extension | `metadata-only` | Preserve namespaced, redacted JSON plus source path. | Authority-like semantics: `BUZZ_AUTHORITY_CLAIM_REFUSED`; secret content: `BUZZ_PUBLIC_SENSITIVE_CONTENT`; executable semantics: `BUZZ_RUNTIME_CAPABILITY_REFUSED`; unreviewed semantics: `BUZZ_SURFACE_UNSUPPORTED`. |

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
- `ownerBindingProof`: an object containing exactly `proofVersion` (fixed to
  `1`), `canonicalizationVersion` (fixed to `RFC8785`),
  `signatureAlgorithm`, `signerKeyId`, and `signatureBytes`. It is a detached
  owner signature over the exact domain-separated proof preimage defined
  below;
- `issuedAt`, `notBefore`, `expiresAt`, and `sequence` as immutable binding
  fields;
- `previousBindingDigest` for rotation, when applicable;
- `emergencyRevocationAuthorities`: an immutable array sorted by UTF-8 bytewise
  ascending `signerKeyId`, then `signerPubkey`, with duplicates forbidden. An
  entry contains exactly `signerKeyId`, `signerPubkey`, `signatureAlgorithm`,
  `bindingScope` (exactly `this-binding-only`), `allowedActions` (exactly
  `["revoked"]`), and nullable `notBefore` and `expiresAt`; non-null authority
  times must fall within the binding validity window. No configured emergency
  authority is represented by the exact empty array;
- `status` as a derived evaluation result, never as signed binding input;
- `lifecycleEvidence`: the complete set of signed transition/revocation records
  used to derive `status`, deterministically ordered during evaluation. Every
  record contains `recordVersion`, `recordSequence`,
  `actorKeyId`, `actorPubkey`, `signatureAlgorithm`, `action`, `bindingDigest`,
  `previousBindingDigest` and `replacementBindingDigest` (explicit `null` when
  inapplicable), `effectiveAt`, `reasonCode`, `reason`, `evidenceDigest`, and
  `signatureBytes`;
- `bindingDigest` over the domain string
  `reddiagent-buzz-identity-binding-v1`, one `0x00` byte, and the RFC 8785 JSON
  Canonicalization Scheme (JCS) UTF-8 bytes of an object containing exactly
  `canonicalAgentId`, `canonicalAdlUri`, `canonicalAdlDigest`,
  `canonicalAdlVersion`, `buzzAgentPubkey`, `ownerPubkey`, `issuedAt`,
  `notBefore`, `expiresAt`, `sequence`, `previousBindingDigest`, and
  `emergencyRevocationAuthorities`. `previousBindingDigest` is explicit `null`
  for an initial binding. The digest is lowercase hex SHA-256 of those exact
  preimage bytes. It excludes `ownerAttestationRef`, `ownerBindingProof`,
  `status`, `lifecycleEvidence`, revocation references, reasons, and every
  other presentation or derived field.

NIP-OA at the assessed Buzz pin signs the agent key and its supported
conditions; it does not itself sign the ADL digest or complete identity join.
Therefore `ownerAttestationRef` is necessary provenance but insufficient to
enter `bound`. The exact `ownerBindingProof` signed preimage is the UTF-8 bytes
of the domain string `reddiagent-buzz-owner-binding-proof-v1`, one `0x00` byte,
and the RFC 8785 JCS UTF-8 bytes of an object containing exactly
`proofVersion`, `canonicalizationVersion`, `signatureAlgorithm`, `signerKeyId`,
and `bindingDigest`. `bindingDigest` is represented in that object as its exact
64-character lowercase-hex ASCII string; it is never hex-decoded to the raw
32-byte digest for owner-proof signing or verification. `signatureBytes` is
excluded from the preimage. The detached signature must verify under the exact
`ownerPubkey`, and `signerKeyId` must resolve uniquely to that same key.
Substituting the digest or any proof metadata invalidates the proof. An
equivalent future provenance format may replace the two records only when it
signs every binding-digest field and is version-pinned and reviewed.

Lifecycle evaluation must first verify the immutable owner binding proof, then
verify each lifecycle record against the immutable `bindingDigest`. A transition
record uses domain `reddiagent-buzz-identity-transition-v1`; a revocation record
uses `reddiagent-buzz-identity-revocation-v1`. Records must be signed by the
owner key, except an explicitly configured emergency revocation key may sign a
revocation when that key and scope were included in the original immutable
binding payload. Emergency keys cannot activate, rotate, supersede, extend, or
replace a binding, and an absent/empty authority array grants no emergency
power.

For every lifecycle record, `recordSequence` is a positive integer in the
signed record payload and must be unique for its `bindingDigest`. The exact
signed preimage is the record's domain string, one `0x00` byte, and the RFC
8785 JCS UTF-8 bytes of an object containing exactly `recordVersion` (fixed to
`1`), `recordSequence`, `actorKeyId`, `actorPubkey`, `signatureAlgorithm`,
`action`, `bindingDigest`, `previousBindingDigest`,
`replacementBindingDigest`, `effectiveAt`, `reasonCode`, and `reason`.
Inapplicable digest fields are explicit `null`; no field may be omitted.
`signatureBytes` and `evidenceDigest` are excluded from the signed preimage.
The detached signature verifies over those exact preimage bytes.
`evidenceDigest` is lowercase hex SHA-256 of the concatenation of those exact
preimage bytes, one `0x00` byte, and the decoded raw `signatureBytes`; it
therefore commits to all signed semantics, signer/algorithm metadata, and the
signature, but excludes itself and any container/list position.

`lifecycleEvidence` must contain every record supplied to the fold, with no
hidden side channel or omitted sequence. Evaluation validates signatures and
authorization first, rejects duplicate or non-positive `recordSequence`
values, recomputes every `evidenceDigest`, and then sorts the validated records
in ascending order by these keys, in this exact priority: (1) `effectiveAt` by
parsed chronological instant; (2) `recordSequence` by positive integer value;
(3) action rank, where `revoked` = 0, `superseded` = 1, `rotating` = 2, and
`active` = 3; and (4) `evidenceDigest` by lexicographic comparison of its decoded
raw 32 bytes as unsigned bytes from index 0 through 31. Only those four action
values are valid; timestamps that do not parse to an unambiguous RFC 3339
instant and digests that do not decode to exactly 32 bytes fail closed. No key
uses descending, locale-sensitive, or serialized-array ordering. The resulting
order is the sole fold input; serialized array order has no authority. Unknown,
conflicting, invalid, omitted, or unauthorized records fail closed with
`BUZZ_IDENTITY_BINDING_INVALID`.

The Buzz agent key and owner key must not be interpreted as a wallet, payment
principal, delegated spender, RAP mandate signer, or reputation issuer. NIP-OA
may prove a reviewed owner-to-agent provenance assertion; it does not prove the
owner had payment authority or accepted work.

### 5.2 States and transitions

| State | Entry condition | Allowed transition | Package effect |
|---|---|---|---|
| `proposed` | Complete unsigned/static binding candidate; no valid owner binding proof. | `bound` after proof verification, or `revoked` by valid revocation evidence. | Report only. |
| `bound` | Immutable owner binding proof and all pins verify within validity window; no later lifecycle record applies. | `active`, `rotating`, `revoked`, `expired` through verified evidence/time evaluation. | Report only until explicit activation review. |
| `active` | Valid signed activation record selects the current reviewed immutable binding. | `rotating`, `revoked`, `expired` through verified evidence/time evaluation. | Package may reference it. |
| `rotating` | A valid higher-sequence immutable binding references the active binding's stable `bindingDigest`, with a signed rotation record linking both. | New binding `active`; old binding `superseded`; or both `revoked` on ambiguity. | Block until atomic selection is proven. |
| `superseded` | A verified higher-sequence replacement is active and its signed transition references this binding's immutable digest. | `revoked` by valid revocation evidence. | Historical evidence only. |
| `revoked` | Valid signed revocation evidence references this immutable binding digest. | Terminal | Block immediately. |
| `expired` | `expiresAt` is not later than evaluation time, unless an earlier valid revocation already determines `revoked`. | Terminal; create a new immutable binding. | Block. |

Joins are fail-closed. Conflicting owner claims, equal sequence with different
digests, missing predecessor, digest mismatch, clock ambiguity, stale cache,
revoked predecessor, or missing revocation evidence produces
`BUZZ_IDENTITY_BINDING_INVALID`. Rotation must not reuse a revoked key or silently
extend expiry. Consumers must re-evaluate revocation and expiry whenever a
package is reviewed, installed, or refreshed.

## 6. Authority separation

| Buzz/Nostr evidence | Permitted interpretation | Forbidden interpretation |
|---|---|---|
| NIP-OA owner/agent assertion | Owner-to-agent-key provenance within its signed conditions; the separate owner binding proof binds canonical ADL and identity fields. | Standalone ADL-digest binding, RAP/AP2 mandate, wallet delegation, spend authority, or owner reputation. |
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

- [ ] Exact canonical ADL URI/version/digest/schema validate, plus source commit when repository-backed.
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
