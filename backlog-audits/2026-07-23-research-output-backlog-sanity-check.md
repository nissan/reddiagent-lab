# Research Output Backlog Sanity Check

Date: 2026-07-23 AEST

Scope: read-only planning pass to compare the #356 agentic-payments roadmap recalibration output against current GitHub epics/issues before creating, closing, or superseding issues.

## Inputs Checked

- `projects/reddiagent-lab/STATUS.md`
- `memory/2026-07-23.md`
- `memory/2026-07-22.md`
- `research/2026-07-23-agentic-payments-roadmap-recalibration.md`
- GitHub open issues for `reddinft/reddiagent-lab`
- GitHub issue #220
- GitHub issue #247
- GitHub issue #206
- GitHub issue #201
- GitHub issue #361
- `docs/ROADMAP.md`

## Current Read-Only Findings

Open GitHub issue inventory is small:

- #361 `Build RAP x402/AP2 audit-prep alignment packet`
- #247 `Epic: ReddiAgent testing environments and validation infrastructure`
- #220 `Epic: ReddiAgent executable prototype and beta runtime track`
- #206 `Epic: ReddiAgent human-readable docs and architecture hub`
- #201 `Epic: Vercel eve static compatibility lane`

The #356 research sprint has already been converted into the first three practical follow-ups:

- #359 Surfpool/localnet external beta rehearsal packet: closed via PR #362.
- #360 Solana devnet external tester gate: closed via PR #363.
- #361 RAP x402/AP2 audit-prep alignment packet: open and next active gate.

The active roadmap should now be the #356 ladder:

1. Local/static reviewer beta: completed by the ADL v0.2 release/handoff/archive chain through #355.
2. Surfpool/localnet beta rehearsal: completed by #359.
3. Solana devnet external tester gate: completed by #360 as design/evidence gate only, with no devnet execution.
4. RAP x402/AP2 audit-prep alignment: open as #361.
5. Post-audit mainnet candidate: not authorized and not ready for issue creation beyond checklist/spec gates.

Backlog mismatches:

- #220 remains valid as the active parent, but its issue body still starts from the 2026-07-17 prototype/beta framing. Its comments contain the real queue history, but it needs a top-level refresh comment or body update after #361 so humans do not mistake old child tasks for current direction.
- #247 has met its original acceptance criteria. Its child lanes #248/#249/#250 are complete and have already been consumed as pull-in evidence. Leaving it open makes the backlog look like environment setup is still pending.
- #206 has met its original child-task list, but the docs/architecture hub should now be refreshed from #356/#359/#360/#361. Closing it immediately would hide the need to update the public roadmap/docs with the current payment-infrastructure direction.
- #201 appears complete/parked. Its static Vercel eve child work #202/#203/#204 is closed. It is still useful as historical export-target context, but it is not part of the current external tester/payment/audit roadmap.
- `docs/ROADMAP.md` is stale. It still presents the older `Now/Next/Later` report-only roadmap and does not mention the completed ADL v0.2 beta baseline, #356 research findings, Surfpool/localnet first, devnet tester gate, or audit/mainnet ladder.

Potential missing backlog coverage from #356:

- External tester MVP packaging is not yet separately tracked. #360 defines the devnet gate, but no issue currently packages the actual MVP A/B/C tester scripts/forms/evidence templates.
- Smart-contract/program audit-readiness freeze is only partly covered by #361. #361 maps invariants and audit deltas, but a later implementation issue should turn those deltas into an audit packet/checklist once the alignment packet is complete.
- Devnet field-test execution is intentionally not authorized by #360; a later issue should exist only after #361 and only if Nissan explicitly wants a bounded cohort/devnet run.
- Public/docs roadmap refresh is not tracked as a child of #206 or #220.

## Proposed Issue Actions

Do not mutate GitHub until the plan is reviewed, except for the already-known cron retarget blocker if this run has the right control privileges.

Recommended keep/update/close/create actions:

1. Keep #220 open as the active umbrella epic.
   - Add a new queue-hygiene comment after this audit summarizing the current authoritative ladder and noting #361 as next.
   - Consider updating the body later so it no longer foregrounds old initial child tasks.

2. Keep #361 as the next active issue.
   - It already maps cleanly to #356 recommendation 3.
   - Run it next after the cron retarget is fixed.

3. Close #247 as complete, or comment then close.
   - Rationale: #248/#249/#250 are all complete and available as pull-in evidence.
   - Closing it does not remove the evidence; it reduces active backlog noise.

4. Keep #206 open for one new docs-refresh child, then close once done.
   - Proposed child: `Refresh ReddiAgent roadmap/docs hub from #356 payment-infrastructure ladder`.
   - Scope: update `docs/ROADMAP.md`, docs hub narrative, and possibly architecture/ADR references to reflect ADL v0.2 beta baseline, localnet -> devnet -> audit-prep -> post-audit mainnet ladder, and deprecate old report-only framing.

5. Close #201 as complete/parked.
   - Rationale: the static Vercel eve compatibility lane child work is complete and not part of the current payment/external beta roadmap.
   - If eve becomes relevant again, reopen or create a new specific issue from current requirements rather than leaving this old epic active.

6. Create new issue after #361: `Build external tester MVP packet for agentic payment beta`.
   - Should convert MVP A/B/C from #356 into concrete tester workflows, forms, acceptance evidence, support/rollback notes, and no-mainnet/no-real-value guardrails.
   - This is not a devnet execution issue; it packages the cohort-facing tester experience.

7. Create new issue after #361: `Build smart-contract audit-readiness freeze checklist and evidence packet`.
   - Should consume #361 outputs and turn invariants, replay resistance, atomicity, authority constraints, spend limits, privacy, settlement proof, and kill-switch criteria into an auditor-facing checklist/evidence packet.

8. Do not create a mainnet issue yet.
   - Mainnet remains blocked until official audit and explicit go-live readiness.
   - The nearest safe future issue is a mainnet-readiness checklist, not a mainnet implementation/run.

## Execution Plan Before Mutation

Phase 0: fix the immediate automation blocker.

- Retarget cron `3165bfa3-df8f-43ca-bade-67776d693591` to #361 from an unrestricted control path if available.
- If unavailable, report that as the only operational blocker and leave GitHub issue mutation for a control session.

Phase 1: complete #361 first.

- Build the RAP x402/AP2 audit-prep alignment packet.
- Keep it static/local/deterministic.
- Do not run devnet, mainnet, wallets, facilitators, live MCP, credentials, deployments, Docker, Surfpool, or package publishing.

Phase 2: backlog hygiene after #361 merges.

- Post #220 authoritative ladder update.
- Comment/close #247 as complete.
- Comment/close #201 as complete/parked.
- Create the docs-refresh child under #206 or #220.
- Create the external tester MVP packet issue.
- Create the smart-contract audit-readiness freeze checklist/evidence issue.
- Update `projects/reddiagent-lab/STATUS.md` and `memory/2026-07-23.md`.

Phase 3: docs + tester packet.

- Refresh stale `docs/ROADMAP.md` and docs hub references.
- Build external tester MVP packet only after #361 gives the cross-layer contract.

Phase 4: audit packet, then later devnet execution decision.

- Build the audit-readiness freeze checklist/evidence packet.
- Only then decide whether to authorize a real bounded devnet cohort run.
- Mainnet remains blocked until official audit and explicit go-live approval.
