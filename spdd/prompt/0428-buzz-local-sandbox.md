# REASONS-LITE — Owner-reviewed local Buzz sandbox

_Status: draft | Owner: Loki on behalf of Nissan | Project: reddiagent-lab | Issue: [#428](https://github.com/reddinft/reddiagent-lab/issues/428) | Parent: [#421](https://github.com/reddinft/reddiagent-lab/issues/421)_

SPDD-LITE is required because this is the first executable Buzz gate and crosses
software supply-chain, identity, approval, local process, storage, privacy, and
future payment boundaries. This artifact is the implementation plan. If the
reviewed source, sandbox design, lifecycle, evidence shape, or safety boundary
changes, implementation must stop and update this artifact before continuing.

## R — Requirements / Definition of Done

Prove that one validated, one-way ADL projection can be explicitly reviewed,
installed, used for one bounded local collaboration task, stopped, revoked,
uninstalled, and reset in a disposable, loopback-only Buzz sandbox. ADL remains
canonical. Buzz events are provenance/context only. RAP remains authoritative
for mandates, rail truth, work/eval receipts, disputes/refunds, accounting
acceptance, and reputation eligibility.

**DoD checklist:**

- [ ] A review surface binds exact ReddiAgent commit, ADL URI/version/digest,
  exporter/report/persona/manifest/curation digests, Buzz tag/commit/artifact
  digest, projection losses, permissions, warnings, sandbox id, one task
  digest, approval nonce/window, and `paymentMode=none`.
- [ ] The owner can decline before installation. Install/start are impossible
  without a fresh, exact-scope owner signature; stale, revoked, mismatched, or
  tampered evidence refuses before execution.
- [ ] The sandbox denies non-loopback network, external relay, ambient
  credentials, external provider/model, tool/MCP/shell/file-edit authority,
  wallet, RPC, payment, delegated spend, external testers, deployment, and
  localnet/devnet/mainnet.
- [ ] One predeclared signed local task produces one bounded signed response and
  one explicit `hold` or `reject` context. No arbitrary follow-up work is
  admitted.
- [ ] Evidence covers decline, install, start, task, response, hold-or-reject,
  stop, revoke, uninstall, residual-data guidance, reset, and a terminal state.
- [ ] Upstream block/buzz#2911 is used only if merged and re-pinned on the
  implementation head. Otherwise the manual owner-review path is used.
- [ ] block/buzz#2603 is reproduced at the exact Buzz pin when safely possible;
  while it remains open/failing, shared and cross-owner agents are explicitly
  unsupported and are not used for the collaboration proof.
- [ ] Exact-head focused checks, deterministic evidence validation, GitHub
  Actions, and current-head Oli security QA pass before merge.

Out of scope: hosted signup; external relay, network product call, provider,
ambient credential, or external tester; public marketplace deployment; wallet,
RPC, payment request, settlement, or delegated spend; Surfpool/localnet;
devnet/mainnet; production deployment; upstream contact; audit vendor/spend;
and all work on #429–#433.

## E — Entities / Handoff Objects

| Entity / object | Purpose | Required fields / invariants |
|---|---|---|
| Pin manifest | Freezes every reviewed input | ReddiAgent commit, ADL URI/version/digest, report/persona/manifest/curation digests, Buzz repo/tag/commit/artifact filename/size/SHA-256, installer signature verification result, evaluation time |
| Review bundle | Human-readable decision surface | Exact pins, direct/lossy/unsupported/refused rows, permissions, public-prompt/memory/network/storage warnings, denied boundaries, `paymentMode=none`, one task digest, rollback/reset plan |
| Owner approval | Authorizes one sandbox and one task | #427 approval-scope wire contract, owner key binding, sandbox id, task digest, nonce, issued/expiry time, exact review-bundle digest; no wildcard or delegation |
| Sandbox policy | Deny-by-default local execution boundary | Unique root, created-path allowlist, loopback-only endpoints, empty credential allowlist, no inherited secret environment, no provider/tools/wallet/payment, process/resource bounds |
| Lifecycle ledger | Proves the closed G2 transition graph | #427 state/payload digest and signature rules, exact actor/proof per edge, predecessor chain, decision and diagnostics derived by verifier |
| Collaboration context | One signed provenance exchange | approval/sandbox/task/agent binding, monotonic sequence, nonce, prior-event digest, request/response/hold-or-reject kind, pure Ed25519 signature; no authority claim |
| Retention manifest | Makes cleanup limits visible | Every created/read path, content class, deletion/reset action, before/after observation, intentionally retained redacted evidence, unverifiable residue and guidance |
| Evidence bundle | Reviewable implementation result | Redacted commands, exit codes, version/hash checks, policy observations, lifecycle ledger, event proofs, #2911/#2603 result, cleanup/reset result, boundary assertions |

All machine-readable objects are closed and reject duplicate JSON member names.
Callers cannot assert `verified`, `safe`, `approved`, `current`, `clean`, or
`complete`; the local verifier derives them from exact bytes and observations.

## A — Approach / Key Decisions

### Reviewed pin and owner-review route

The planning pin is Buzz Desktop `desktop-v0.5.3`, upstream commit
`3a96acea09b4a9e3f02c3a26cfb0607d2ccacf42`, published 2026-07-31. On the
current Apple Silicon host, the candidate release artifact is
`Buzz_0.5.3_aarch64.app.tar.gz`, size `91633977`, release SHA-256
`aa4673e16fbdf0f37b770d7fb28e33abb70169e3d6c0702d074decaf76d6711f`;
its detached signature artifact has release SHA-256
`3751303fad6b4edc71d3e93bb27b47dc7d6096099a2ed2692ce7235f22d06295`.
These are planning inputs, not permission to download or install in this plan
step. Implementation must re-read the immutable release/tag metadata, download
only the selected pinned artifacts into the disposable sandbox, verify byte
digests and the upstream signing procedure/key from pinned source documentation,
and record any verification limitation. A mismatch or unverifiable signature
refuses before extraction.

block/buzz#2911 is open at plan time, so the selected route is the existing
manual owner-review/draft-create flow. No `buzz://install-agent` deep link may
be tested from the open PR or an unreviewed branch. If #2911 becomes merged
before implementation, that is a material plan change: pin the containing
release/commit, review its exact diff and security assertions, update this
artifact, and obtain owner/Oli acceptance before using it.

block/buzz#2603 is open at plan time, including reports through v0.5.2. The
sandbox therefore uses one locally owned, locally managed agent only.
Shared/cross-owner discovery, mention, add-member, or sibling messaging is
unsupported. A negative probe may document the exact-pin behavior but cannot
expand the task or weaken NIP-OA binding to make it pass.

### Isolation and least privilege

Use a disposable sandbox root created with a restrictive umask and explicit
paths for application data, cache, configuration, temporary files, logs, and
evidence. Launch through an environment allowlist containing only values proved
necessary for local operation and sandbox paths; do not enumerate, copy, log,
or inherit ambient secrets. Before start, record a redacted process/network
baseline. During the task, bind any required relay/service only to loopback and
deny all non-loopback egress with an OS-enforced per-process/container boundary
whose exact mechanism and verification commands are reviewed before use.

The implementation must prefer the smallest local components that satisfy the
issue. It may not attach the sandbox to the user's normal Buzz profile, global
application data, browser session, keychain, workspace, SSH/Git credentials,
provider configuration, wallet, RPC endpoint, or existing relay. Synthetic
keys and public test text live only inside the sandbox. The canonical ADL is
read to generate a reviewed projection before start; runtime write access to
the repository is denied.

Any inability to enforce and observe non-loopback denial, empty ambient
credentials, or sandbox-only storage is a blocker, not a reason to fall back to
the normal desktop profile. Loopback traffic is local transport only and does
not authorize Surfpool/localnet, an external relay, a provider, or any payment
surface.

### Closed lifecycle and bounded task

Reuse the exact G2 lifecycle, digest, signature, decision-precedence, stop,
revocation, and terminal semantics frozen in `spdd/prompt/0427-buzz-threat-model.md`
and its implemented evidence. The implementation must not invent a weaker
parallel state machine.

Two evidence branches are required:

1. `not-reviewed → review-presented → declined → terminal` proves a decline
   causes no extraction, installation, start, task, or retained sandbox state.
2. `not-reviewed → review-presented → owner-approved → installed → started →
   task-admitted → response-recorded → held-or-rejected → stopped → revoked →
   uninstalled → residual-guidance-recorded → reset-verified → terminal`
   proves the authorized path.

The sole task uses fixed, non-sensitive public fixture text and asks the local
agent to summarize that text without tools, provider calls, file edits, network
lookups, memory carry-over, or follow-up actions. The expected response is
bounded by an exact schema and byte/token ceiling. A second or mutated task,
stale approval, injected tool/provider/payment instruction, external URL, or
post-stop/post-revocation event must be held or rejected and recorded. Task and
response signatures prove provenance only; they do not prove service
acceptance, payment, receipt, or reputation.

### Cleanup and evidence retention

Stop processes before revocation and uninstall. Revoke the exact approval and
agent binding, remove only the predeclared disposable sandbox paths, and verify
absence plus no listener/process remains. Never delete a broad directory,
normal Buzz profile, repository, credential store, or unresolved path. The
retention manifest distinguishes deleted runtime data from intentionally kept,
redacted repository evidence. Secure-erasure claims are forbidden; snapshots,
backups, filesystem journals, OS caches, and other unverifiable residue receive
plain residual-data guidance and a visible limitation/hold where applicable.

## S — Structure / Files Touched

| Surface | Planned change |
|---|---|
| `spdd/prompt/0428-buzz-local-sandbox.md` | Accepted plan and prompt/code sync log |
| `scripts/buzz_local_sandbox_evidence.py` | Closed, fail-closed evidence validator/renderer; orchestration only for reviewed local commands |
| `tests/test_buzz_local_sandbox_evidence.py` | Pin, approval, lifecycle, tamper/stale, boundary, retention, and determinism checks |
| `tests/fixtures/buzz-local-sandbox-*` | Synthetic valid/decline/refusal/cleanup evidence; no credentials or private prompts |
| `tests/BUZZ-LOCAL-SANDBOX-EVIDENCE.md` | Redacted exact-pin local execution and rollback/reset report |
| `tests/smoke-validation.sh` | Focused deterministic evidence validation wiring |

Buzz binaries, application state, synthetic keys, local relay/service state,
and transient logs remain under the disposable sandbox root and are never
committed. No upstream Buzz source modification, global install, normal user
profile mutation, provider/wallet configuration, public deployment, or payment
surface is planned.

## O — Operations / Ordered Tasks

1. Merge and accept this plan before any Buzz artifact download, extraction,
   installation, local process start, or task execution.
2. Implement the closed evidence schema, lifecycle validator, pin/digest and
   signature checks, deterministic renderer, synthetic fixtures, and focused
   tests without starting Buzz.
3. Obtain exact-head Oli review of the implementation harness and the proposed
   OS-level isolation commands before they are allowed to run.
4. In a later, separately checkpointed lifecycle step, re-pin the selected
   Buzz release/source/signing documentation and #2911/#2603 state; refuse on
   drift, mismatch, or missing verification.
5. In a later bounded local-runtime step, create the disposable sandbox, prove
   denied boundaries, execute the decline branch, then execute the one approved
   install/start/task/hold-or-reject/stop/revoke/uninstall/reset branch. Report
   the local runtime/install action explicitly in STATUS, memory, issue/PR, and
   Telegram. Do not chain this operation from the planning or harness step.
6. Validate and render the redacted evidence from explicit files only. Run a
   second clean verification to prove deterministic output and absence of
   process/listener/sandbox residue.
7. Request fresh exact-head Oli security QA. Mark ready and squash-merge only
   after local checks, GitHub Actions, reviews/requests/threads, and Oli PASS
   are current and green.
8. After merge, verify #428 closure and G2 evidence. Update #421/#419 handoffs
   and STATUS/memory. Only if G2 is fully green, remove the bounded cron and
   stop for fresh Nissan approval before G3; never begin #429–#433.

## N — Norms

- ADL is canonical; Buzz is a disposable, optional, one-way projection.
- RAP remains the sole payment/receipt/reputation authority.
- Pin exact bytes and fail closed on drift; never use `latest` at execution.
- Owner review is a cryptographic, exact-scope lifecycle step, not a UI click
  inferred from install/start or a prior authorization.
- Keep all task content synthetic/public and all evidence redacted.
- Treat loopback as a transport boundary, not general network permission.
- Preserve the dirty primary checkout and unrelated worktrees; all repository
  edits use clean disposable worktrees from current `origin/main`.
- Update this plan in the same PR when implementation materially diverges.

## S — Safeguards / Acceptance Checklist

- [ ] Planning and harness-only steps perform no Buzz download, extraction,
  install, start, relay/service start, agent task, provider call, credential
  access, wallet/RPC/payment action, or external network product call.
- [ ] Artifact verification checks exact name, size, SHA-256, tag, commit, and
  detached signature procedure/key. Archive inspection rejects traversal,
  absolute paths, links/devices, duplicate paths, unexpected executable hooks,
  and extraction outside the sandbox root.
- [ ] Review/approval checks bind every pin, loss, permission, warning,
  boundary, sandbox, task, nonce, and validity time using the #427 signature
  contract. Decline creates no install/runtime state. Tampered, stale, revoked,
  replayed, cross-task, or cross-sandbox approval refuses.
- [ ] The execution environment is constructed from an allowlist, contains no
  ambient secret/provider/wallet/RPC variables, cannot read the repository or
  normal Buzz profile, and can write only declared sandbox paths.
- [ ] OS-level evidence proves no non-loopback connection succeeds and no
  external relay/provider/tester is configured. DNS and metadata endpoints are
  denied. Failure to prove this blocks start.
- [ ] `paymentMode=none` is immutable throughout every state and event. Wallet,
  RPC, payment, mandate, settlement, delegated spend, and RAP request surfaces
  are absent/refused.
- [ ] Tool/MCP/shell/subprocess/file-edit requests, external URLs, follow-up
  tasks, mutated task digests, and post-stop/revocation work are held or
  rejected with stable diagnostics.
- [ ] Signed event verification covers exact task/approval/sandbox/agent
  binding, pure Ed25519 wire bytes, sequence, nonce, predecessor, replay,
  stop/revocation precedence, and non-authority wording.
- [ ] #2911 remains manual-fallback unless a merged, owner-reviewed, exact pin
  is accepted through a plan update. No open-PR build or deep link is executed.
- [ ] #2603 result is honest. Shared/cross-owner behavior remains unsupported
  while the exact-pin test fails or cannot safely be proven; stripping NIP-OA
  or weakening identity to bypass it is forbidden.
- [ ] Stop/revoke/uninstall/reset checks prove no sandbox process or listener,
  no declared runtime path, no reusable approval, and no retained synthetic
  private key remains. Evidence never claims secure erasure.
- [ ] Retained repository evidence is redacted, deterministic, contains no
  host username/absolute sandbox path/private key/credential/private prompt,
  and explains residual-data limitations.
- [ ] Planned focused validation commands:

  ```text
  python3 tests/test_buzz_local_sandbox_evidence.py
  python3 -m py_compile scripts/buzz_local_sandbox_evidence.py tests/test_buzz_local_sandbox_evidence.py
  python3 scripts/buzz_local_sandbox_evidence.py validate --evidence tests/fixtures/buzz-local-sandbox-valid.json --evaluation-time <PINNED_RFC3339_UTC>
  python3 scripts/buzz_local_sandbox_evidence.py render --evidence tests/fixtures/buzz-local-sandbox-valid.json --evaluation-time <PINNED_RFC3339_UTC> --output /tmp/buzz-local-sandbox-evidence.md
  git diff --check origin/main...HEAD
  PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
  ```

- [ ] Exact-head Oli QA reviews supply-chain verification, owner approval,
  lifecycle/signature fidelity to #427, OS isolation, credential/network/tool/
  storage/payment denials, #2911/#2603 handling, cleanup evidence, and all G2
  non-goals before ready/merge.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-08-01 | Initial #428 local-sandbox plan; no Buzz download, install, runtime, relay, agent task, credential, provider, wallet/payment, or external action | Created | Deferred until this plan is accepted |
