# Cross-Repo Tracks: ReddiAgent Lab and Reddi Agent Protocol

_Issue #397. Child of launch epic #386. Alignment source:
`research/2026-07-26-agent-payments-landscape-and-backlog-alignment.md`._

Two repositories carry this project, and they carry different things. This
document is the single map of who owns what, where the release ladder stands
on each side, and how work flows between them.

## The two repos and their contracts

**`reddinft/reddiagent-lab` (this repo) is the open spec home.** ADL v0.2 is
canonical here: `specs/ADL-v0.2.md`, its machine-checked schema, the
conformance checker, validated and negative example fixtures, deterministic
validators, and compatibility reports. Code is Apache-2.0; specs and docs are
CC BY 4.0. The audience is agent framework and platform builders. The
trajectory is community governance as the contributor base forms.

**`nissan/reddi-agent-protocol` is the implementation and proof repo.** It
holds ClawsOut/RAP: the x402 escrow program, commit-reveal reputation, and
Solana settlement work, plus an education track for autonomous-payment agent
workflows. The audience is Solana and payments builders. It consumes ADL and
proves it against real rails.

The binding rule between them: the protocol repo's ADL whitepaper (its issues
#611 and #613) **derives from and cites `specs/ADL-v0.2.md` — it must not
fork the spec narrative**. Spec changes flow lab → protocol. Implementation
feedback flows protocol → lab as issues here, the same way the delegation
examples surfaced four v0.3 spec gaps in
`docs/AGENT-TEAM-DELEGATION-EXAMPLES.md`. One spec, two repos, no drift.

## The shared release ladder, mapped to actual state

Both repos climb the same seven-rung ladder from `docs/ROADMAP.md`. Neither
repo can skip a rung the other has not reached: the lab's specs and validators
are the acceptance criteria for the protocol repo's programs, and the protocol
repo's evidence is what qualifies the spec as proven.

| Rung | Lab provides | Protocol provides | Honest status |
|---|---|---|---|
| 1. ADL v0.2 beta baseline | Canonical spec + schema, conformance checker, Level-3 delegation examples (`charge` intents, 0.10–0.25 USDC caps, `x402-dry-run` rail only) | ADL whitepaper (#611/#613) deriving from the lab spec | Lab: shipped, with a known checker gap — `charge` intents escape Level-3 conformance enforcement (v0.3 candidate). Protocol: whitepaper in progress. |
| 2. Surfpool/localnet rehearsal | Rehearsal packet (#359), `realValueTransfer=false` guardrails, deterministic fixture accounts | Anchor escrow scaffold exercised on localnet; Quasar reputation phases | Packet built. 2026-07-26 upgrade pending: rehearse against Surfpool's copy-on-read mainnet fork (real USDC/PYUSD/AUDD mints, live Agent Registry/SATI programs) instead of synthetic fixtures. |
| 3. Devnet external tester gate | Gate definition (#360): devnet-only wallets, allowlisted programs/mints, tiny caps, rollback evidence | Escrow + reputation deployed devnet-only; PayAI `solana-devnet` as the concrete facilitator rail | Gate defined; devnet-gated. No live tester execution is authorized. |
| 4. RAP x402/AP2 audit-prep alignment | Alignment packet (#361); layer boundaries (x402 / AP2 / MCP / Solana / RAP kept distinct) | Receipt implementation binding payment proof to delivery; AP2 mandate-hash ingestion | Packet built. Receipt-integrity validator (#387, PR #405) is the lab-side acceptance check for the protocol receipts. |
| 5. External tester MVP packet | Packet built (#365), consuming rungs 2–4 without activating testers | AUDD evidence tasks #632–#635 supplying the devnet payment evidence | Lab packet complete. Protocol evidence tasks open. Still packet/design work — live testers need a later authorizing issue. |
| 6. Audit-readiness freeze | Freeze checklist and evidence packet (#366): invariants, replay resistance, spend limits, kill-switch expectations | AUDD grant milestones #616–#619; frozen program code and settlement proofs | Lab freeze packet complete. Protocol milestones open. Audit not yet engaged. |
| 7. Official audit and go-live | Reviewed evidence, resolved findings | Audited programs, explicit go-live approval | Not started. Mainnet is blocked until official audit completion and explicit go-live approval — on both sides, with no exceptions. |

The plain reading of that table: the lab side has run ahead on packets and
validators; the protocol side owns the harder remaining work — real programs,
real devnet evidence, real audit. That asymmetry is by design (substance-first
means the spec home prepares the acceptance criteria before the proof lands),
but it means most rung-advancement from here is protocol-repo work that the
lab verifies.

## Interlocks

Three efforts currently share one end-to-end story — an AUDD-denominated
agent payment, escrowed via x402, receipted and reputation-scored under RAP:

- **The 2026-08-31 launch epic (#386, children #387–#401)** works back from
  the public launch date. Its substance requirement is exactly this story
  working on devnet.
- **The AUDD grant M1 evidence chain** (protocol milestones #616–#619,
  evidence tasks #632–#635) needs the same devnet payment flow as its
  milestone proof.
- **The Colosseum Eternal Challenge** (closes ~early September 2026) is the
  best-fit venue for demonstrating the same flow.

One working demo satisfies all three. A slip in the protocol repo's devnet
evidence slips all three together.

Two lab artifacts are hard gates on protocol-repo launches:

- **The receipt-integrity validator (#387, PR #405)** is the acceptance
  criteria for the protocol repo's receipt implementation. USENIX Security
  2026 research found security-rule violations in all 15 major x402
  facilitators; settlement evidence alone is not trustworthy, which is why
  receipts must pass this validator before rung 4 closes.
- **Registry/SATI attestation compatibility (#378/#392)** gates reputation
  launch. The Foundation-endorsed Agent Registry and SATI are live on Solana
  mainnet; RAP reputation reveals must dual-publish as compatible SAS
  attestations rather than launch siloed.

## Issue-flow conventions between the repos

Issues live where the work lives:

- **Lab owns**: spec changes, schema and conformance work, validators,
  compatibility mappings and reports, examples, docs-hub and process changes.
- **Protocol owns**: Anchor programs, escrow, reputation, facilitator and
  registry integration, AUDD grant milestones, devnet operations, the
  education track.
- **Spec feedback from implementation** is filed as a lab issue, citing the
  protocol-repo issue or PR that surfaced it (the pattern set by the v0.3
  candidates in `docs/AGENT-TEAM-DELEGATION-EXAMPLES.md`).
- **Cross-repo references** use the full form
  (`reddinft/reddiagent-lab#397`, `nissan/reddi-agent-protocol#616`) so links
  resolve from either side, and state the relationship explicitly
  (depends-on / blocks / relates-to).

Both repos follow `.github/AGENT-DEVELOPMENT-PROCESS.md`: exactly one
`status:*` label per issue (`product-backlog` → `sprint-backlog` →
`assigned` → `in-progress` → `in-review` → closed), work branches named
`<type>/<hyphenated-short-title>`, worktrees for parallel work, agent
attribution in commit trailers, and the Ready-to-Approve review protocol
before any squash-merge. Blocked work gets `status:blocked` and a comment
naming the required human action — never a workaround.
