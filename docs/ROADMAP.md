# ReddiAgent Lab Roadmap

_Issue #367. Parent epics: #206, #220. Alignment update 2026-07-26 below._

## 2026-07-26 Alignment Update

Following the maintainer-approved backlog alignment (research:
`research/2026-07-26-agent-payments-landscape-and-backlog-alignment.md` and
`research/2026-07-26-microsoft-agent-framework-compatibility.md`), the ladder
below stands with three amendments and a posture change:

1. **Rung 2 upgrade — Surfpool mainnet-fork rehearsal.** Surfpool (now the
   default Anchor validator) supports copy-on-read mainnet forking: localnet
   rehearsal should run against forked mainnet state (real USDC/PYUSD/AUDD
   mints, live Agent Registry/SATI programs), which de-risks the
   devnet→mainnet jump more than synthetic fixtures do.
2. **Rung 3 anchor — PayAI `solana-devnet` facilitator** is the concrete
   devnet rail for the external tester gate; self-hosted settlement paths
   (Faremeter, Kora facilitator guide) avoid single-vendor dependency.
3. **Post-launch re-validation.** Alpenglow fully activates ~Oct 2026;
   confirmation/finality semantics change after the 2026-08-31 launch, so the
   rehearsal harness and CI stay live through Q4 for a re-validation pass.

Posture: **substance-first** — the receipt-integrity validator and proof
implementations validate the spec before the public call for review; the
2026-08-31 community launch epic tracks the workback. Framework adapter
ordering: Microsoft Agent Framework first (only GA declarative YAML target),
Google ADK on payment-convergence watch (x402 Foundation premier member),
Open Agent Spec mapping tracked through its AGNTCY OASF absorption.
Development follows `.github/AGENT-DEVELOPMENT-PROCESS.md`.

## Current Release Ladder

ReddiAgent has moved beyond the old report-first backlog. Report-only outputs still matter for compatibility targets and safety review, but the executable/beta lane is now anchored on deterministic evidence that can graduate toward external testing without blurring live-action boundaries.

The accepted ladder is:

1. **ADL v0.2 beta baseline.** Keep ADL canonical, validate the local beta release/archive evidence chain, and preserve stable diagnostics, policy gates, receipts, and rollback criteria before any external cohort work.
2. **Surfpool/localnet rehearsal.** Rehearse Solana-facing payment and receipt scenarios on localnet first, with deterministic fixture accounts, mints, authorities, replay cases, rollback metadata, and `realValueTransfer=false` guardrails.
3. **Solana devnet external tester gate.** Define the external tester decision gate only after localnet evidence is green. Devnet work must stay bounded to devnet labels, devnet-only wallets and keys, allowlisted programs/mints, tiny test caps, failure scenarios, rollback evidence, and no mainnet ambiguity.
4. **RAP x402/AP2 audit-prep alignment.** Align ADL/RAP evidence with x402 payment proof, AP2/FIDO/Verifiable Intent delegated authority, MCP protected-resource access, and Solana settlement proof before any payment-capable public beta.
5. **External tester MVP packet.** Package the baseline, localnet, devnet gate, and audit-prep evidence into a tester-facing MVP packet. This is still packet/design work unless a later issue explicitly authorizes live tester execution.
6. **Audit-readiness freeze and evidence packet.** Freeze the smart-contract and protocol evidence needed for review: invariants, replay resistance, atomicity, delegated authority constraints, spend limits, privacy/PII, receipt and settlement proofs, rollback and kill-switch expectations, and devnet/mainnet confusion tests.
7. **Official audit and go-live readiness.** Mainnet remains blocked until official audit completion and explicit go-live readiness approval.

Completed evidence chain:

- #356 researched agentic payments roadmap recalibration and created the localnet/devnet/audit-readiness ladder.
- #359 built the Surfpool/localnet external beta rehearsal packet.
- #360 added the Solana devnet external tester gate.
- #361 built the RAP x402/AP2 audit-prep alignment packet.

Current follow-up queue:

- #367 refreshes this roadmap and the docs hub references.
- #365 builds the external tester MVP packet.
- #366 builds the smart-contract audit-readiness freeze checklist and evidence packet.

## Layer Boundaries

Do not collapse the protocol layers:

- **x402** is payment challenge/proof/response evidence.
- **AP2/FIDO/Verifiable Intent** is delegated authority and mandate evidence.
- **MCP** is protected-resource access and tool invocation boundary evidence.
- **Solana** is devnet/localnet/mainnet settlement proof and program evidence.
- **RAP** binds receipt, accounting, reputation, and protocol-level evidence above the payment rail.

ReddiAgent Lab may model and validate these layers, but live invocation, settlement, credential use, wallet use, facilitator action, production gateway mutation, deployment, or mainnet activity must come from a later issue with explicit authorization.

## Now

- Keep the ADL v0.2 beta baseline deterministic and reviewable.
- Refresh human-readable docs so they point to the accepted localnet -> devnet tester gate -> x402/AP2/RAP audit-prep -> external tester MVP -> audit-readiness ladder.
- Build #365 as an external tester MVP packet that consumes #359/#360/#361 without activating live tester execution.
- Build #366 as the audit-readiness freeze/evidence packet after the tester packet is available.

## Next

- Convert the external tester packet into a bounded tester cohort decision only when a later issue explicitly authorizes live tester execution.
- Keep devnet evidence clearly separated from production and mainnet claims.
- Add or update deterministic validation whenever docs, fixtures, or generated reports are checked by existing tests.
- Use Surfpool/localnet before Solana devnet whenever local rehearsal can answer the question.

## Later

- Reassess public beta activation after tester packet and audit-readiness freeze evidence are complete.
- Enter official smart-contract/protocol audit only with frozen evidence, reviewed invariants, and explicit scope.
- Consider go-live readiness only after official audit completion, audit findings are resolved or accepted, and the project maintainer explicitly approves go-live.

## Deprecated Roadmap Posture

The older Vercel eve-first and report-only compatibility ladder is no longer the active release roadmap. Vercel eve, Agent Spec, A2A Agent Card, Agent Skills, provider mappings, and other compatibility surfaces remain useful static/export targets, but they should not outrank the accepted beta readiness ladder when the goal is external tester and audit readiness.

Report-only remains valid for documentation, compatibility, policy, and safety evidence. It is no longer the default answer when a deterministic localnet/devnet/audit-prep artifact would move the release ladder forward.

## Mainnet Gate

Mainnet is not a roadmap item until all of these are true:

- the external tester MVP packet is complete and accepted;
- the audit-readiness freeze/evidence packet is complete and accepted;
- official audit has completed;
- critical audit findings are resolved or explicitly accepted;
- go-live readiness is explicitly approved.

Until then, every roadmap item must preserve no-mainnet guardrails and fail closed on mainnet ambiguity.
