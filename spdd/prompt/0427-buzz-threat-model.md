# REASONS-LITE — Buzz boundary threat model and gated regression evidence

_Status: draft | Owner: Loki on behalf of Nissan | Project: reddiagent-lab | Issue: [#427](https://github.com/reddinft/reddiagent-lab/issues/427) | Normative inputs: `specs/BUZZ-ADAPTER-CONTRACT-v0.1.md`, `spdd/prompt/0425-buzz-exporter.md`, and `spdd/prompt/0426-buzz-marketplace-envelope.md`_

SPDD-LITE is required because this work defines the security gate between static
Buzz projection evidence and later local runtime and payment-capable phases.
This artifact is the implementation update plan. Implementation must update it
in the same PR if the threat registry, evidence contract, files, or safeguards
materially diverge.

## R — Requirements / Definition of Done

Produce a deterministic, static threat model and negative-regression evidence
for the optional ADL to Buzz boundary. ADL remains canonical and Buzz remains a
one-way, disposable projection. RAP remains authoritative for payment mandates,
rail truth, work/eval receipts, disputes/refunds, accounting acceptance, and
reputation eligibility.

**DoD checklist:**

- [ ] A closed, versioned threat-model document identifies assets, actors,
  attacker capabilities, trust boundaries, data flows, security assumptions,
  STRIDE categories, controls, detection evidence, response, and residual risk.
- [ ] The registry covers public persona prompt leakage, malicious packages,
  source/hash substitution, owner/agent key rotation, replay, stale approvals,
  shared-agent confusion, MCP/shell/file-edit tools, environment injection,
  memory/workspace retention, relay tampering, misleading receipt/reputation
  claims, and payment retries.
- [ ] Required decline/refusal/hold, stop, revoke, uninstall, rollback/reset,
  incident, privacy/redaction, and audit-evidence behavior is deterministic and
  tied to stable diagnostics.
- [ ] The model states that Buzz's keyless audit chain is tamper-evident under
  its documented assumptions, not tamper-resistant or independently
  authoritative.
- [ ] G2 and G3 checklists are machine-readable, version-pinned, and prove that
  a later gate cannot inherit authorization from an earlier gate.
- [ ] Later request-only payment design requires authoritative rail
  reconciliation and at-most-once semantics; G2 remains `paymentMode=none`.
- [ ] Deterministic negative fixtures cover every threat and every denied
  boundary without installing or executing Buzz.
- [ ] Focused tests, deterministic snapshots, `git diff --check`, full smoke,
  exact-head GitHub Actions, and current-head security reviewer PASS are green.

Out of scope: Buzz source changes or contact with upstream; install or runtime
activation; relay or agent start; provider/model/network calls; credential or
secret access; tool/MCP/shell/file execution; wallet, RPC, payment, settlement,
or delegated spend; public distribution; deployment; external testers;
localnet, devnet, or mainnet; and work on #428 or #429+.

## E — Entities / Handoff Objects

| Entity / object | Purpose | Required invariants |
|---|---|---|
| Threat-model registry | Closed machine-readable security contract | Version, normative pin/digest inputs, pinned evaluation time, trust boundaries, actors, assets, threats, controls, gate mappings, residual risk |
| Threat record | One testable abuse case | Stable id, STRIDE categories, asset, attacker, entry point, preconditions, impact, preventive/detective controls, decision, diagnostics, evidence, response, residual risk, fixture ids |
| Approval scope | Prevents ambient or stale owner consent | Exact ADL/report/persona/manifest/curation digests, Buzz/source/adapter pins, permission/loss/warning digests, sandbox id, one task digest, nonce, issued/expiry time, owner key and signature |
| Signature wire contract | Makes approval and event proofs reproducible | Separate digest/signature domain bytes, NUL separator placement, RFC 8785/JCS payload bytes, exhaustive digest/signature field exclusions, SHA-256 digest representation, pure Ed25519 algorithm id, UTF-8/base64url encodings, signer key id, trust-root binding |
| Sandbox policy | Defines G2 least privilege without starting it | Local-only, deny-by-default filesystem/network/environment/provider/tool/wallet/payment surfaces; explicit created-path allowlist and resource bounds |
| Event context | Signed collaboration provenance only | Sandbox/task/approval/agent binding, monotonic local sequence, nonce, prior-event digest, event digest; no mandate/acceptance/payment/reputation authority |
| Audit evidence | Tamper-evident local history and limitations | Ordered raw records, chain verification, missing-prefix/tail warning, signer/pin context, export digest, explicit non-authority and non-tamper-resistance statement |
| Retention manifest | Makes cleanup and residual data reviewable | Declared created/read paths, content class, retention need, deletion/reset instruction, before/after presence checks, unverifiable residue disclosure |
| Incident record | Freezes unsafe continuation | Trigger, affected pins/artifacts/sandbox, evidence digests, containment, revocation/stop state, cleanup state, owner, next approval gate |
| G2 lifecycle state machine | Preconditions for #428 local sandbox work | Exact pins, owner review, denied external/payment boundaries, branch-aware transition table, predecessor/state digests, terminal state rules, decline/install/task/hold-or-reject/stop/revoke/uninstall/reset evidence |
| G3 economic-intent state machine | Static future request-only payment gate | Fresh separate authorization, request/mandate/idempotency digest, immutable rail-visible binding, atomic attempt states, authoritative reconciliation, retry/finality rules, receipt/eval/dispute separation; never executable in #427/#428 |

Every JSON object is closed. Callers cannot supply derived `verified`, `safe`,
`approved`, `current`, `reconciled`, or `complete` booleans. The evaluator
derives decisions from exact bytes, signatures, times, sequences, and policy.

## A — Approach / Key Decisions

### Trust boundaries and attacker model

The implementation models these boundaries explicitly and does not collapse
them into a generic "trusted local" zone:

1. canonical ADL and reviewed #424–#426 evidence to static Buzz artifacts;
2. static artifacts to the later owner-review surface;
3. owner approval to a single disposable local sandbox and task;
4. local sandbox to host filesystem, environment, network, provider, tools,
   memory, and process control, all denied unless a later gate explicitly says
   otherwise;
5. Buzz agent/event key to owner identity and canonical ADL binding;
6. signed events and local audit chain to human interpretation;
7. Buzz context to RAP request/payment/receipt/reputation authority; and
8. active sandbox state to stop/revoke/uninstall/reset and residual storage.

Attackers include a malicious package publisher, compromised or stale owner or
agent key, another local user/process, malicious prompt/task/event participant,
compromised relay, compromised dependency or Buzz source pin, and an operator
making an honest but unsafe inference. Host-root compromise, kernel compromise,
physical compromise, and independently proving secure erasure are outside the
model's prevention claim and remain explicit residual risks.

STRIDE labels are applied per threat and may be multiple: spoofing, tampering,
repudiation, information disclosure, denial of service, and elevation of
privilege. Privacy, supply-chain, replay, authorization, and payment-safety
facets are recorded separately rather than forced into one STRIDE label.

### Deterministic threat and decision contract

Add a local validator/renderer whose only inputs are explicit repository files
and a caller-pinned RFC 3339 UTC evaluation time. It must not inspect ambient
credentials, host environment values, running processes, mutable branches,
network identities, relays, wallets, or payment rails.

The overall decision is one of `g1-threat-evidence-ready`, `hold`, or `refused`.
Schema/digest/signature/pin tampering, authority escalation, executable content,
unknown threats/controls, or a claimed PASS with missing negative evidence is
`refused`. Current but unresolved risk, unsupported shared-agent behavior,
unverifiable cleanup, or incomplete later-gate prerequisites is `hold`. A G3
hold does not prevent the G1 threat artifact from being complete; it prevents
G3 authorization and must remain visible.

Stable diagnostics include at minimum:

- `BUZZ_SECURITY_INPUT_INVALID`
- `BUZZ_SECURITY_PIN_OR_DIGEST_MISMATCH`
- `BUZZ_SECURITY_PUBLIC_CONTENT_REFUSED`
- `BUZZ_SECURITY_PACKAGE_TAMPERED`
- `BUZZ_SECURITY_IDENTITY_INVALID`
- `BUZZ_SECURITY_SIGNATURE_PREIMAGE_INVALID`
- `BUZZ_SECURITY_SIGNATURE_KEY_INVALID`
- `BUZZ_SECURITY_APPROVAL_STALE`
- `BUZZ_SECURITY_EVENT_REPLAYED`
- `BUZZ_SECURITY_LIFECYCLE_TRANSITION_INVALID`
- `BUZZ_SECURITY_SHARED_AGENT_UNSUPPORTED`
- `BUZZ_SECURITY_TOOL_CAPABILITY_REFUSED`
- `BUZZ_SECURITY_AMBIENT_CREDENTIAL_REFUSED`
- `BUZZ_SECURITY_NETWORK_OR_RELAY_REFUSED`
- `BUZZ_SECURITY_RETENTION_HOLD`
- `BUZZ_SECURITY_AUDIT_LIMITATION`
- `BUZZ_SECURITY_AUTHORITY_CLAIM_REFUSED`
- `BUZZ_SECURITY_ECONOMIC_INTENT_MISMATCH`
- `BUZZ_SECURITY_PAYMENT_ATTEMPT_STATE_INVALID`
- `BUZZ_SECURITY_PAYMENT_RETRY_REFUSED`
- `BUZZ_SECURITY_RAIL_RECONCILIATION_REQUIRED`
- `BUZZ_SECURITY_INCIDENT_HOLD`
- `BUZZ_SECURITY_RESET_INCOMPLETE`

Diagnostics are all-applicable and ordered by threat id, evidence JSON pointer,
severity rank, then code. Existing #424 exporter/identity diagnostics remain
normative for their own surfaces; the security evaluator references them and
must not reinterpret a failed #424–#426 result as safe.

### Approval, replay, identity, and shared-agent rules

A later G2 approval signs one exact domain-separated approval scope. It binds
all canonical/package/curation digests, exact source pins, disclosed losses,
permissions, warnings, sandbox instance, one bounded task digest, a unique
nonce, and a short issued/expiry window. Approval cannot be wildcarded,
refreshed implicitly, transferred between sandboxes/tasks, or inferred from a
Buzz/Nostr event, channel membership, reaction, prior install, or prior phase.

Approval and event proofs use SHA-256 for object identity and pure Ed25519
(RFC 8032 `Ed25519`, not `Ed25519ph`) for signatures. There is no algorithm
negotiation. The closed approval payload is the complete approval-scope object
after removing exactly `approvalDigest`, `signature`, `signatureBytes`,
`signatureAlgorithm`, `proof`, `verified`, `decision`, and `diagnostics`. The
closed event payload removes exactly `eventDigest`, `signature`,
`signatureBytes`, `signatureAlgorithm`, `proof`, `verified`, `decision`, and
`diagnostics`. A removed field cannot be represented as `null`; an
unknown digest, signature, proof, or derived field is rejected before hashing.

The object digests are exactly:

```text
approvalDigest = SHA-256(
  ASCII("reddiagent.buzz.g2.approval.digest.v0.1") || 0x00 ||
  RFC8785-JCS-UTF8(closedApprovalPayload)
)
eventDigest = SHA-256(
  ASCII("reddiagent.buzz.g2.event.digest.v0.1") || 0x00 ||
  RFC8785-JCS-UTF8(closedEventPayload)
)
```

Each stored digest is the unpadded base64url encoding of the raw 32-byte SHA-256
result. The exact bytes signed with pure Ed25519 are, respectively:

```text
ASCII("reddiagent.buzz.g2.approval.signature.v0.1") || 0x00 || rawApprovalDigest
ASCII("reddiagent.buzz.g2.event.signature.v0.1") || 0x00 || rawEventDigest
```

The only accepted `signatureAlgorithm` value is `Ed25519`. Implementations must
call the pure Ed25519 sign/verify operation over the 75-byte approval signed
representation or 72-byte event signed representation above and must not
prehash those bytes or select Ed25519ph. JSON is UTF-8 RFC 8785/JCS canonical
form. Binary digests, public keys, key ids, nonces, and signatures are unpadded
base64url strings over their raw bytes.

The signing key must resolve through the #424 owner or agent binding verifier
for the exact role, canonical ADL digest, source pins, evaluation time, and
revocation state. A valid cryptographic signature under the wrong role, stale
binding, superseded key, unrelated ADL, or alternate domain is invalid.

Negative fixtures must cover omitted payload fields, substituted digests,
caller-supplied/circular `approvalDigest` or `eventDigest` fields in the hashed
payload, unknown digest-like fields, alternate digest or signature domains,
missing or duplicated NUL separators, signing JCS bytes instead of the signed
digest representation, different canonicalization, UTF-16 or locale encoding,
padded or non-canonical base64url, `Ed25519ph`/prehashed verification under an
`Ed25519` claim, pure-Ed25519 verification under an `Ed25519ph` claim, wrong algorithm,
wrong owner key, wrong agent key, owner-key-as-agent-key, agent-key-as-owner-key,
rotation between approval and use, revoked key, and caller-supplied
`verified=true`. All emit `BUZZ_SECURITY_SIGNATURE_PREIMAGE_INVALID`,
`BUZZ_SECURITY_SIGNATURE_KEY_INVALID`, `BUZZ_SECURITY_IDENTITY_INVALID`, or the
more specific pin/digest diagnostic before any later lifecycle decision.

Before any later install/start/task transition, the verifier must re-run the
unchanged complete #424 identity lifecycle verifier and the #425/#426 artifact
chain checks at the pinned evaluation time. Rotation, supersession, revocation,
expiry, source drift, permission/loss changes, or any byte change invalidates
approval. Stop and revoke override queued work; a revoked task/event cannot be
made current by replay or a higher local sequence.

Signed local event context binds the exact approval, task, sandbox, canonical
agent, Buzz agent key, nonce, monotonic sequence, and previous digest. Duplicate
nonces/digests, gaps, forks, wrong predecessor, wrong signer, wrong task, events
after stop/revocation, and stale approval refuse. Wall-clock order alone is not
authority. The first event's `previousEventDigest` is exactly JSON `null` in
the closed event payload; every later value is the unpadded base64url raw digest
of the immediately preceding event. Missing, string `"null"`, empty, all-zero,
forked, or substituted predecessors refuse before signature verification.

Upstream block/buzz#2603 is treated as an unresolved shared/cross-owner-agent
boundary unless #428 tests an exact reviewed pin and proves otherwise. The G2
default is one owner, one isolated agent identity, one sandbox, and one task.
No fixture or checklist may claim shared-agent support from schema acceptance or
same-owner success.

### Tools, credentials, network, memory, and malicious package controls

The G2 policy defaults to no external network or relay; no ambient environment;
no external provider; no wallet/RPC/payment/delegated spend; and no tool, MCP,
shell, subprocess, dynamic import, package lifecycle script, or file mutation
outside an explicit disposable sandbox allowlist. Package/archive validation
rejects traversal, absolute paths, symlinks/hardlinks, device files, sockets,
duplicate normalized/case-folded paths, executable hooks, binary surprises,
unreviewed dependencies, extra files, hash mismatch, and mutable source pins.

Public persona/prompt output is allowlist-based. Secret-shaped values, private
instructions, workspace content, credential references that reveal values,
host paths, and memory contents are refused before an artifact is admitted.
Redaction must replace the entire value with a stable classification marker;
partial secret logging is forbidden. Negative fixtures contain synthetic
canaries only, never real credentials or workspace data.

The retention manifest distinguishes ephemeral sandbox files, Buzz state,
logs/audit records, caches, generated artifacts, and operator-exported evidence.
The later uninstall/reset gate verifies declared paths are absent or explains
why evidence is intentionally retained. It must disclose that process memory,
filesystem snapshots/backups, host telemetry, and already disclosed external
data cannot be proven erased by a local script. Any undeclared or unexplained
residue is `hold`, not a false clean claim.

### Audit-chain and relay limitations

Buzz's keyless audit chain is treated only as tamper-evident local history under
the exact reviewed implementation and key-custody assumptions. Hash continuity
can detect mutation, reordering, and some truncation when a trusted checkpoint
is available. A host/key compromise may rewrite records and checkpoints; a
local chain alone cannot prove completeness, independent timestamp, human
approval, non-repudiation, service acceptance, settlement, or reputation.

G2 denies external relay use. Static fixtures still model injection, deletion,
reorder, replay, fork, wrong-author, and stale relay events so any later relay
proposal fails closed. No relay event can alter canonical ADL, owner approval,
RAP authority, revocation state, or local policy.

### G2 lifecycle checklist contract

The machine-readable G2 checklist contains ordered, individually evidenced
states: review and explicit decline; fresh approval; verified install; explicit
start; one signed local task and response plus hold or reject context; stop;
revoke; uninstall; residual-data guidance; and reset/rollback verification.
Each state binds exact before/after policy, artifact, process, filesystem, and
audit digests. Skipping, reordering, reusing approval, or claiming a later state
from log text fails. The checklist is designed here but exercised only in #428
after G1 closes.

The G2 lifecycle is a total deterministic state machine with these states:
`not-reviewed`, `declined`, `approval-issued`, `install-verified`,
`started`, `task-recorded`, `task-held`, `task-rejected`, `incident-recorded`, `stopped`,
`revoked`, `uninstalled`, `residual-guidance-recorded`, `reset-verified`, and
`terminal`. The only normal success branch is:
`not-reviewed -> approval-issued -> install-verified -> started ->
task-recorded -> task-held|task-rejected -> stopped -> revoked -> uninstalled
-> residual-guidance-recorded -> reset-verified -> terminal`. The explicit
decline branch is `not-reviewed -> declined -> terminal`; decline never creates
install/start/task authority. Incident branches transition from any
non-terminal post-approval state to `incident-recorded`, then `stopped`,
`revoked`, and cleanup.
`terminal` is absorbing and cannot be reopened; any later run needs a fresh
approval and a new sandbox id.

Every transition names one actor role (`owner`, `operator`, or `verifier`),
the required signature or local verifier proof, the predecessor state digest,
the current state payload digest, the exact evaluation time, and the expected
decision. Missing predecessor, predecessor mismatch, skipped state, duplicate
state id, branch join without the required prior state, post-terminal event,
or stale approval emits `BUZZ_SECURITY_LIFECYCLE_TRANSITION_INVALID` or
`BUZZ_SECURITY_APPROVAL_STALE`.

The transition relation is closed by the following matrix. A source/destination
pair absent from this table is invalid. Set-valued source cells expand to one
edge per named source; no actor may substitute for the sole actor shown.

| From | To | Sole actor | Required proof |
|---|---|---|---|
| genesis | `not-reviewed` | verifier | `local-verifier-genesis-v1` |
| `not-reviewed` | `declined` | owner | pure-Ed25519 `owner-decision-v1` |
| `not-reviewed` | `approval-issued` | owner | pure-Ed25519 approval-scope proof defined above |
| `declined` | `terminal` | verifier | `local-verifier-terminal-v1` |
| `approval-issued` | `install-verified` | verifier | `local-verifier-install-v1` |
| `install-verified` | `started` | operator | pure-Ed25519 `operator-action-v1` under the operator key pinned by the approval |
| `started` | `task-recorded` | operator | pure-Ed25519 `operator-task-submit-v1` under that same key |
| `task-recorded` | `task-held` | verifier | `local-verifier-policy-decision-v1` |
| `task-recorded` | `task-rejected` | verifier | `local-verifier-policy-decision-v1` |
| `task-held`, `task-rejected` | `stopped` | operator | pure-Ed25519 `operator-action-v1` |
| any of `approval-issued`, `install-verified`, `started`, `task-recorded`, `task-held`, `task-rejected` | `incident-recorded` | verifier | `local-verifier-incident-v1` bound to the incident digest |
| `incident-recorded` | `stopped` | verifier | `local-verifier-incident-stop-v1` |
| `stopped` | `revoked` | owner | pure-Ed25519 `owner-revocation-v1` |
| `revoked` | `uninstalled` | verifier | `local-verifier-uninstall-v1` |
| `uninstalled` | `residual-guidance-recorded` | verifier | `local-verifier-retention-v1` |
| `residual-guidance-recorded` | `reset-verified` | verifier | `local-verifier-reset-v1` |
| `reset-verified` | `terminal` | verifier | `local-verifier-terminal-v1` |

The approval payload pins `operatorKeyId` and `operatorPubkey`; both must equal
the key id and public key of the current #424-bound owner identity for the same
canonical ADL, sandbox, task, source pins, and validity interval. They do not
create another identity or delegation mechanism. Verifier proofs
are closed deterministic evidence objects emitted by the static verifier, not
caller assertions or signatures. Agent event signatures prove response/event
provenance but never authorize a lifecycle edge.

Every state record uses these exact digest rules. `statePayload` excludes
`statePayloadDigest`, `stateDigest`, `signature`, `proof`, `verified`,
`decision`, and `diagnostics`. `statePayloadDigest` is the unpadded base64url
encoding of:

```text
SHA-256(ASCII("reddiagent.buzz.g2.state-payload.digest.v0.1") || 0x00 ||
        RFC8785-JCS-UTF8(statePayload))
```

`stateDigest` is the unpadded base64url encoding of:

```text
SHA-256(ASCII("reddiagent.buzz.g2.state-record.digest.v0.1") || 0x00 ||
        RFC8785-JCS-UTF8({
          "actorRole": actorRole,
          "evaluationTime": evaluationTime,
          "predecessorStateDigest": predecessorStateDigest,
          "proofType": proofType,
          "state": state,
          "stateId": stateId,
          "statePayloadDigest": statePayloadDigest
        }))
```

For the sole genesis `not-reviewed` record,
`predecessorStateDigest` is the JSON value `null` and those literal JCS bytes
participate in `stateDigest`. For every other record it is the unpadded
base64url raw digest of the immediately preceding record. Missing, string
`"null"`, empty, all-zero, wrong-branch, or substituted predecessors refuse.
Fixtures cover every matrix edge plus every absent edge, wrong actor,
wrong proof type, agent-event-as-transition-proof, payload/state substitution,
initial-null variants, skipped predecessor, fork, and post-terminal replay.

For matrix rows whose proof type is pure Ed25519 other than the separately
defined approval-scope proof, the exact bytes signed are:

```text
ASCII("reddiagent.buzz.g2.lifecycle.signature.v0.1") || 0x00 || rawStateDigest
```

The `proofType`, actor role, and actor key id are inside the hashed state
record, so a proof cannot be relabeled or moved to another edge. The only
accepted algorithm is pure `Ed25519`; Ed25519ph, signing the JCS payload
directly, or signing `statePayloadDigest` instead of `stateDigest` refuses.

Decision precedence is total. `refused` outranks `hold`, which outranks
`g1-threat-evidence-ready`. Signature, schema, pin/digest, stale/revoked
approval, executable authority, external/payment boundary, and invalid
transition failures are `refused`. Retention residue, incomplete cleanup,
shared-agent unsupported status, unresolved incident evidence, and G3
preconditions are `hold` when no refusal applies. If a compound fixture contains
both refused-before-hold evidence, the rendered output must show both
diagnostics but return `refused`; the hold reason remains visible as secondary
evidence. Stop and revoke outrank queued work, but they do not erase evidence
or falsely complete uninstall/reset.

Every G2 state keeps `paymentMode=none`, external network/relay false, ambient
credentials false, external provider false, wallet/RPC/payment/delegated spend
false, external testers false, and deployment false. Decline, hold, stop,
revoke, uninstall, and reset must remain possible without provider or network
availability.

### G3 reconciliation and at-most-once contract

G3 remains unauthorized. Its static checklist requires fresh Nissan approval
and a separate request-only RAP authority object; nothing from G2 grants it.
A later payment request must bind canonical ADL/task, principal, payee, purpose,
amount/currency, expiry, revocation, rail, request digest, idempotency key, and
attempt number. The Buzz event is context only and cannot be that authority.

The future economic intent digest is domain separated from G2 events:

```text
sha256("reddiagent.rap.g3.economic-intent.v0.1" || 0x00 || <rfc8785-jcs-json-bytes>)
```

The JSON bytes bind canonical ADL digest, task digest, principal id, payee id,
purpose, amount, currency, expiry, revocation pointer, RAP request-core digest,
rail id, and policy version. The rail-visible idempotency key is derived from,
and is deliberately excluded from, this payload to avoid a circular digest.
The request-core digest itself excludes economic-intent/idempotency, attempt,
receipt, reconciliation, signature/proof, and derived outcome fields; the final
RAP request envelope then carries both that core digest and the completed
economic-intent digest without recursive hashing.
This digest is the
at-most-once scope. It must be included unchanged in every local attempt record,
RAP request object, and mandatory rail idempotency field,
receipt join record, reconciliation record, and rendered evidence. Changing
payee, amount, currency, task, principal, rail, expiry, or policy version
creates a different economic intent and cannot be treated as a retry of the
prior intent. Any idempotency key other than the single derived key below is a
mismatch and refuses rather than creating a new intent.

Rail support for one immutable, rail-visible idempotency key is mandatory. The
key is exactly `base64url(rawEconomicIntentDigest)`, must be carried in the
rail's authenticated request/idempotency field, and must be returned unchanged
in authenticated status, reconciliation, and final receipt evidence. Unknown
capability is `hold`; a rail that cannot preserve and return this binding is
`refused` before submission. A local-only key, mutable metadata, or receipt-text
echo is insufficient.

Before a first submission, one durable compare-and-swap creates the unique
attempt row keyed by `economicIntentDigest` and the unique rail idempotency key,
moving version 0 `not-submitted` to version 1 `pending-recorded`. Only CAS from
the exact current version may advance the row; duplicate insert, losing worker,
stale version, key change, or second attempt id refuses. The request bytes and
request digest are frozen at version 1. Submission may occur once from that
row. No final rejection, success, duplicate, conflict, key rotation, expiry,
or revocation permits a new attempt id or a different key for the same economic
intent.

A same-key transport replay is not a new payment attempt, but is allowed only
when the exact request bytes/digest are unchanged, the pinned rail contract
guarantees replay returns the original result without a second economic action,
and fresh authenticated reconciliation has proved the current rail state. It
uses the same attempt id and CAS row. `unknown`, timeout, stale/missing
reconciliation, or a rail without that replay guarantee forbids automatic
replay and remains `hold`. A success, final rejection, duplicate-final,
conflicting result, missing authenticated receipt, or unreconciled state
forbids resubmission. Recovery requires read-only
authoritative rail reconciliation, exact receipt/request join, and human review
when the result remains ambiguous. At-most-once applies to the economic intent,
not merely to one HTTP call. Payment success never proves work success, eval
pass, accounting acceptance, dispute closure, or reputation eligibility.

Future attempt records are atomic and append-only: `not-submitted`,
`pending-recorded`, `submitted`, `rail-accepted`, `rail-rejected-final`,
`duplicate-final`, `unknown-requires-reconciliation`,
`conflict-requires-human-review`, and `terminal`. A process crash, concurrent
worker, key rotation, or stale owner approval cannot create a second automatic
submission for the same economic intent. Negative fixtures must model crash
after pending-before-submit, crash after submit-before-receipt, two workers
racing the same intent, rail duplicate with success semantics, rail duplicate
with conflicting metadata, changed key between request and receipt, missing
authenticated rail signature, stale reconciliation read, and forged receipt.
These emit `BUZZ_SECURITY_ECONOMIC_INTENT_MISMATCH`,
`BUZZ_SECURITY_PAYMENT_ATTEMPT_STATE_INVALID`,
`BUZZ_SECURITY_PAYMENT_RETRY_REFUSED`, or
`BUZZ_SECURITY_RAIL_RECONCILIATION_REQUIRED`.

The fresh G3 authorization pins the rail trust root (`railId`, root key id,
raw public-key digest, signature algorithm, reconciliation maximum age, and
accepted finality policy). A reconciliation payload excludes exactly
`reconciliationDigest`, `signature`, `signatureAlgorithm`, `proof`, `verified`,
`decision`, and `diagnostics`, and
binds economic-intent digest, rail-visible idempotency key, request digest,
attempt id, rail transaction/reference id or explicit null, status, finality,
monotonic rail sequence, observed time, valid-until time, and prior
reconciliation digest or explicit null. Its digest and signed representation
are exactly:

```text
reconciliationDigest = SHA-256(
  ASCII("reddiagent.rap.g3.reconciliation.digest.v0.1") || 0x00 ||
  RFC8785-JCS-UTF8(closedReconciliationPayload)
)
ASCII("reddiagent.rap.g3.reconciliation.signature.v0.1") || 0x00 ||
rawReconciliationDigest
```

The pinned rail root signs that representation with pure Ed25519; the only
accepted reconciliation signature algorithm is `Ed25519`.
Verification requires `observedTime <= evaluationTime <= validUntilTime`, age
within the pinned maximum, strictly increasing rail sequence, an unbroken
reconciliation predecessor chain, and finality matching the pinned policy.
Only authenticated `final-settled` or `final-rejected` evidence is final;
`pending`, `unknown`, unfinalized, or stale evidence remains hold. Wrong root,
wrong signature preimage, altered idempotency/request join, regressed sequence,
or false finality refuses. Fixtures cover unsupported rails, local-only keys,
same-key replay with changed bytes, changed-key retry, duplicate CAS workers,
wrong/stale root, missing/invalid signatures, freshness boundaries, predecessor
forks, and non-final status presented as final.

## S — Structure / Files Touched

| Surface | Planned change |
|---|---|
| `spdd/prompt/0427-buzz-threat-model.md` | This accepted implementation plan and prompt/code sync log |
| `specs/BUZZ-THREAT-MODEL-v0.1.md` | Human-readable normative trust-boundary, STRIDE, abuse-case, G2/G3, incident, and residual-risk model |
| `specs/BUZZ-THREAT-MODEL-v0.1.schema.json` | Closed deterministic threat/evidence/checklist schema |
| `scripts/buzz_threat_model.py` | Static validate/evaluate/render CLI; no Buzz/runtime/network integration |
| `tests/test_buzz_threat_model.py` | Closure, coverage, decision, ordering, tamper, replay, retention, audit-limit, and boundary assertions |
| `tests/fixtures/buzz-threat-*.json` | Valid registry plus isolated and compound negative abuse cases |
| `tests/BUZZ-THREAT-MODEL-EVIDENCE.md` | Deterministic rendered threat, regression, G2/G3, and residual-risk summary |
| `tests/smoke-validation.sh` | Focused deterministic validation and snapshot wiring |

No Buzz repository/source, install/runtime configuration, provider, credential,
wallet/payment, relay, deployment, or public distribution surface is modified.

## O — Operations / Ordered Tasks

1. Merge and accept this #427 plan before implementation.
2. Freeze assets, actors, trust boundaries, threat ids, STRIDE classifications,
   stable diagnostics, decision precedence, and closed schema.
3. Implement the pure static validator/evaluator and deterministic Markdown
   renderer from explicit pinned files only.
4. Add one isolated fixture for every required threat plus compound fixtures
   for package substitution plus stale approval, replay after revocation,
   malicious tool plus environment injection, relay tamper plus false receipt,
   retention residue, audit-chain truncation, and unknown payment outcome retry.
5. Prove threat/checklist coverage is bidirectional: every normative threat has
   at least one regression fixture and every fixture names existing threats,
   controls, diagnostics, expected decision, and expected evidence.
6. Wire focused validation and full deterministic smoke; update this artifact
   for material divergence and request exact-head Oli security review.
7. Merge only after local checks, GitHub Actions, review/request/thread
   freshness, and Oli PASS are green. Close #420/G1 only after #427 closes; do
   not begin #428 in the same invocation.

## N — Norms

- ADL is canonical; Buzz packages, listings, events, approvals, and audit
  records are scoped evidence, never protocol authority.
- Deny by default at every trust boundary and emit all applicable diagnostics.
- Preserve #424–#426 byte, pin, identity, loss, and authority contracts; do not
  define weaker parallel verification.
- Treat prompts, packages, signed events, and local logs as attacker-controlled
  until exact validation succeeds.
- Make residual risk and unverifiable cleanup visible; never upgrade absence of
  evidence to proof of safety or deletion.
- G2 remains local/payment-none and #428-gated. G3/#429+ remains unauthorized.
- Update this plan with any material implementation divergence.

## S — Safeguards / Acceptance Checklist

- [ ] The schema is closed at every object boundary, JSON parsing rejects
  duplicate member names, and semantic validation rejects duplicate ids,
  unknown cross-references, missing/extra threats, unknown diagnostics,
  caller-supplied outcomes, and mutable/latest pins.
- [ ] Exact raw-byte digests bind the #424 contract, #425 report/persona/
  manifest, #426 plan or implemented curation evidence when available, threat
  registry, and rendered evidence. Any substitution, normalization, path
  ambiguity, or pin mismatch refuses before gate evaluation.
- [ ] Every issue #427 threat appears in the registry, STRIDE table, regression
  matrix, G2/G3 checklist where applicable, and rendered evidence; tests compare
  these sets for exact equality.
- [ ] Approval fixtures prove exact scope, short expiry, nonce uniqueness,
  owner signature, pin/loss/permission/warning binding, sandbox/task isolation,
  and re-verification after rotation/revocation. Wildcard, stale, replayed,
  cross-task, cross-sandbox, or altered approvals refuse.
- [ ] Approval and event signature fixtures prove the exact domain tags, NUL
  separators, SHA-256 digest preimages, exhaustive circular/digest/signature
  field exclusions, exact pure-Ed25519 signed representation, UTF-8 and
  unpadded base64url encodings, role-specific #424 key binding, and rotation/
  revocation handling. Omission, substitution, alternate domain/encoding,
  digest-field injection, Ed25519/Ed25519ph confusion, wrong-key, wrong-role,
  stale-key, and caller-supplied verified fields refuse before lifecycle
  evaluation.
- [ ] Event fixtures prove signer/task/sandbox/approval binding, predecessor and
  sequence integrity, nonce uniqueness, stop/revocation precedence, and no
  authority inference. #2603 stays explicitly unsupported for cross-owner or
  shared-agent use unless later exact-pin #428 evidence changes that status.
- [ ] Malicious package/tool fixtures cover archive traversal, links/devices,
  duplicate paths, lifecycle scripts, dynamic imports, shell, subprocess,
  file-edit escape, MCP invocation, provider/network/relay access, ambient
  environment, wallet/RPC/payment, and delegated spend.
- [ ] Synthetic canaries prove public prompt, logs, diagnostics, and rendered
  evidence contain no secret/private value; no real secret, credential lookup,
  environment inspection, workspace scan, or network call is used.
- [ ] Memory/workspace fixtures prove declared path minimization, bounded
  retention, uninstall/reset checks, intentional evidence retention, residual
  guidance, and a hold for undeclared or unverifiable residue.
- [ ] Audit fixtures mutate, remove, reorder, fork, replay, and truncate records
  and assert the precise detectable result. Output always states that the local
  keyless chain is not tamper-resistant or independently authoritative.
- [ ] G2 checklist has exact decline, install, start, one task/response with
  hold-or-reject, stop, revoke, uninstall, residual guidance, and reset states,
  while all external/payment boundaries remain false.
- [ ] G2 lifecycle fixtures prove all allowed branches, invalid transitions,
  the exact closed actor/proof matrix, skipped/reordered states, duplicate
  states, explicit-null genesis and predecessor/state digest mismatch,
  post-terminal replay, incident branch containment, fresh-approval-after-
  terminal requirements, and refused-before-hold decision precedence.
- [ ] G3 fixtures prove missing reconciliation, ambiguous/timeout, duplicate,
  conflicting receipt, changed payee/amount/task, expired/revoked authority,
  and automatic retry all hold or refuse. No fixture enables payment execution.
- [ ] G3 economic fixtures prove the domain-separated economic-intent digest,
  immutable rail-visible idempotency binding, append-only atomic attempt states,
  unique CAS transitions, same-key retry rules, pinned reconciliation trust
  root/signature preimage/freshness/finality, crash recovery, concurrent
  workers, unsupported rails, key changes, duplicate rails, stale reads,
  forged receipts, and changed principal/payee/amount/task/rail/policy all hold
  or refuse. No fixture
  performs a rail, wallet, RPC, payment, settlement, or delegated-spend action.
- [ ] Incident fixtures prove containment order: deny new work, stop, preserve
  redacted evidence, revoke approval/key/package as scoped, reconcile any
  ambiguous authority state, uninstall/reset, document residue, and require a
  fresh gate. Destructive cleanup is never inferred from incident creation.
- [ ] Two clean runs from identical explicit inputs and evaluation time produce
  identical JSON/Markdown bytes and digests with no host paths, usernames,
  mtimes, process ids, environment values, or wall-clock reads.
- [ ] Planned validation commands:

  ```text
  python3 tests/test_buzz_threat_model.py
  python3 -m py_compile scripts/buzz_threat_model.py tests/test_buzz_threat_model.py
  git diff --check origin/main...HEAD
  PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
  ```

- [ ] Exact-head Oli security review covers threat completeness, trust
  boundaries, package/identity/approval/event verification, tool/credential/
  network/memory containment, audit limitations, G2 lifecycle, G3 at-most-once
  reconciliation, deterministic evidence, and all denied G1 boundaries.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-08-01 | Initial #427 threat-model implementation plan; no implementation or runtime action | Created | Deferred until this plan is accepted |
| 2026-08-01 | Oli exact-head security QA BLOCK required frozen approval/event signature preimages, total G2 lifecycle semantics, and enforceable future G3 economic at-most-once rules | Added byte-level signature wire contract, branch-aware lifecycle state machine with decision precedence, and economic-intent/idempotency/attempt-state requirements | Deferred until this plan is accepted |
| 2026-08-01 | Second Oli exact-head BLOCK found Ed25519ph/no-prehash conflict, incomplete digest/state wire rules, and optional rail idempotency/reconciliation semantics | Selected pure Ed25519 over domain-separated SHA-256 digests with exhaustive exclusions; added the closed actor/proof transition matrix and explicit-null state chain; made rail-visible idempotency, CAS uniqueness, same-key replay, and pinned reconciliation trust/finality mandatory | Deferred until this plan is accepted |
