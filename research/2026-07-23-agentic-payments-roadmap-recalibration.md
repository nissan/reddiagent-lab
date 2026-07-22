# Agentic Payments Roadmap Recalibration

_Date: 2026-07-23 AEST. Anchor issue: #356. Parent: #220._

## Boundary

This packet is research/spec/roadmap evidence only. It does not authorize or
perform live runtime activation, hosted deployment, Docker/Surfpool/Coolify
mutation, credential access/storage, MCP invocation, devnet/mainnet execution,
wallet access, facilitator calls, settlement actions, package/archive
publishing, production gateway mutation, or mainnet action.

## Executive Verdict

Recommendation: pivot the next #220 children into a Surfpool/localnet beta
rehearsal first, then add a tightly bounded Solana devnet external-tester gate,
while keeping RAP scoped as the layer that binds x402 payment evidence to
AP2/FIDO-style authority, receipts, and audit records.

Do not continue the current offline packet queue unchanged. It successfully
proved the ADL v0.2 local beta baseline through #355, but more offline archive
packets will not answer the next risk questions: can a tester understand the
release path, can localnet rehearse payment-like state without live rails, and
can devnet evidence be collected without weakening delegated authority,
privacy, or audit readiness?

Confidence: high for the release-ladder recommendation; medium for exact
x402/AP2 implementation timing because the standards and facilitator ecosystem
are still moving.

## Sources

| Source | Date checked | What it supports | Confidence |
|---|---:|---|---|
| Coinbase CDP x402 overview: https://docs.cdp.coinbase.com/x402/welcome | 2026-07-23 | x402 is HTTP-native payment negotiation for APIs/content; flow is request, 402 challenge, payment signature, facilitator verification/settlement, resource response; current docs advertise EVM and Solana network support through facilitator paths. | High |
| x402 Foundation repository: https://github.com/x402-foundation/x402 | 2026-07-23 | x402 is presented as an open standard for internet-native payments across networks and value forms. | High |
| Cloudflare x402 Foundation announcement: https://blog.cloudflare.com/x402/ | 2026-07-23 | x402 ecosystem is broadening beyond one vendor and is positioned as a common web payment language. | Medium |
| Google Cloud AP2 announcement: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol | 2026-07-23 | AP2 is payment-agnostic, integrates with A2A and MCP, and uses signed mandates/verifiable credentials for authorization, authenticity, and accountability. | High |
| AP2 documentation: https://ap2-protocol.org/ | 2026-07-23 | AP2 frames user control, privacy, verifiable intent, and non-repudiable audit trail as core principles. | High |
| FIDO Alliance agentic standards announcement: https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/ | 2026-07-23 | FIDO formed agentic authentication and payments workstreams; Google AP2 and Mastercard Verifiable Intent are inputs to standardization. | High |
| Mastercard Verifiable Intent: https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html | 2026-07-23 | Verifiable Intent links identity, intent, and action into a privacy-preserving record and aims to prove what was authorized. | Medium-high |
| MCP authorization tutorial: https://modelcontextprotocol.io/docs/tutorials/security/authorization | 2026-07-23 | Authorization is recommended for MCP servers that access user data, need auditability, require consent, or need rate/usage tracking. | High |
| MCP authorization spec: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization | 2026-07-23 | Protected MCP servers act as OAuth 2.1 resource servers and must use protected resource metadata for authorization-server discovery. | High |
| Solana payments docs: https://solana.com/docs/payments | 2026-07-23 | Solana payment rails offer low fees, fast settlement, fee abstraction, and programmability, useful for beta payment flows. | High |
| Solana production-readiness docs: https://solana.com/docs/payments/production-readiness | 2026-07-23 | Devnet is useful before production; mainnet requires different keys/mints, production RPC, transaction landing handling, confirmation policy, key separation, monitoring, and address allowlists. | High |
| SoK: Blockchain Agent-to-Agent Payments: https://arxiv.org/html/2604.03733v1 | 2026-07-23 | A2A payments should be reasoned about across discovery, authorization, execution/settlement, and accounting; known gaps include weak intent binding, valid-authorization misuse, payment-service decoupling, and limited accountability. | Medium |
| SoK: Security of Autonomous LLM Agents in Agentic Commerce: https://arxiv.org/html/2604.15367v2 | 2026-07-23 | Agentic commerce security is cross-layer: agent integrity, transaction authorization, inter-agent trust, market manipulation, and regulatory compliance. | Medium |
| AIP: Agent Identity Protocol for Verifiable Delegation Across MCP and A2A: https://arxiv.org/abs/2603.24775 | 2026-07-23 | Emerging proposals bind identity, attenuated authorization, scope constraints, and provenance into invocation-bound artifacts. | Medium |
| IMF Note: How Agentic AI Will Reshape Payments: https://www.elibrary.imf.org/view/journals/068/2026/004/article-A001-en.xml | 2026-07-23 | Agent-initiated payments raise operational, legal, and systemic risk unless safeguards are designed before adoption. | Medium |

## Layer Map

| Layer | What the market is converging on | RAP/ADL implication |
|---|---|---|
| User/delegator authority | AP2 mandates, FIDO agentic authentication workstreams, Verifiable Intent records. | ADL must continue to require principal, spender, scope, max amount, expiry, revocation, audit path, and policy refs before any spend-capable intent is considered Level 3 ready. |
| Tool/resource access | MCP OAuth/resource-server model for protected remote MCP surfaces. | MCP authorization is not payment authorization. ReddiAgent should validate remote protected-resource metadata separately from x402/AP2 payment metadata once live paths are approved. |
| Request-level payment | x402 HTTP 402 challenge, selected payment payload/signature, facilitator verification/settlement, and paid response. | Keep x402 as payment evidence and rail vocabulary. Do not let x402 alone imply permission to spend or task success. |
| Settlement rail | Solana Pay/Solana-native payments, stablecoins, devnet rehearsal, and mainnet production constraints. | Use Surfpool/localnet for transaction-shape rehearsal, devnet only for external tester field evidence, and mainnet only after official audit and go-live readiness. |
| Receipt/accounting | Payment proof plus service-result proof plus eval status. | RAP should bind request hash, response hash, mandate refs, payment response, settlement reference, service result, eval gate, and dispute/rollback status into one receipt envelope. |
| Reputation | Reputation follows verified completion, not raw payment success. | Existing ReddiAgent reputation signals are directionally right: emit only after receipt verification, eval pass, policy compliance, and dispute outcome checks. |

## Practical Release Ladder

| Milestone | Environment | What external testers can validate | Required guardrails |
|---|---|---|---|
| 1. Local/static reviewer beta | Local files and static HTML only | Understand ADL v0.2 examples, inspect policy/receipt/reputation fields, run deterministic validators and packet tests. | No network, no runtime activation, no credential lookup, no wallet/facilitator calls, no paid provider calls. |
| 2. Surfpool/localnet beta rehearsal | Local Solana validator or Surfpool-style localnet | Rehearse transaction intent, account/mint allowlists, replay controls, receipt creation, rollback/kill-switch paths, and failure UX without real value. | Local-only keys, isolated test mints, fixture-funded accounts, no devnet/mainnet endpoints, no reusable secrets, all runs reproducible from reset state. |
| 3. Solana devnet external tester gate | Solana devnet with bounded tester cohort | Test human approval, delegated authority UX, devnet transaction landing/confirmation, receipt/settlement proof capture, support workflow, and feedback loop. | Explicit devnet labels, small capped budgets, test wallet separation, allowlisted mints/programs, no mainnet addresses, per-tester spend ceilings, rollback drill before expansion. |
| 4. Audit-readiness freeze | Repo/spec/test suite plus auditor packet | Verify invariants, threat model, delegated authority constraints, privacy limits, receipt proofs, replay/atomicity coverage, and upgrade/disable controls. | Independent audit scope, frozen program IDs/IDLs, deterministic test evidence, known-risk register, no mainnet launch until official audit is complete and go-live readiness is approved. |
| 5. Post-audit mainnet candidate | Mainnet only after audit and Nissan go-live readiness | Real settlement with production monitoring and support. | Official audit pass/remediation, production RPC, key-management review, incident runbook, limits, monitoring, and explicit go-live approval. |

## External Tester MVP Candidates

### MVP A: Paid Data Access Receipt Reviewer

User: external builder evaluating whether ReddiAgent can describe a paid API or
MCP-backed data call safely.

Task: load an ADL with an x402-protected data/tool declaration, inspect the
AP2-style authority constraints, run static validation, and review a dry-run
receipt that binds request hash, response hash, payment metadata, eval result,
and reputation eligibility.

Payment flow: x402 objects remain static at first; localnet/devnet later
rehearses payment-like proof and settlement reference without exposing a live
facilitator until approved.

Success metric: 3 of 5 testers can produce a valid receipt review and explain
why payment success alone is not task success.

Feedback loop: structured tester form captures confusing fields, missing
examples, guardrail questions, and whether the receipt is audit-useful.

Guardrails: no real paid API calls in the first milestone; devnet-only labels
and tiny caps in the devnet milestone; no mainnet.

### MVP B: Delegated Spend Limit Sandbox

User: operator or protocol reviewer assessing whether a bounded agent mandate
can prevent overspend and scope drift.

Task: configure a localnet/devnet mandate for a simple allowed purchase, then
attempt over-budget, expired, wrong-purpose, wrong-merchant, and replayed
variants.

Payment flow: localnet first with deterministic accounts and test mints; devnet
only after local replay/authority tests pass.

Success metric: all invalid variants fail closed with stable diagnostics and no
receipt/reputation emission.

Feedback loop: testers label diagnostics as actionable/not actionable and file
minimum repro cases for confusing failures.

Guardrails: per-run spend ceilings, one-time nonces, authority expiry,
revocation path, no production keys, no mainnet addresses, no hidden retries.

### MVP C: Agent-to-Agent Service Outcome Bundle

User: technical tester comparing agent-to-agent service/payment proof against
delivered outcome.

Task: simulate a buyer agent paying a seller agent for a small service,
validate both agents' declared authority, and inspect whether service outcome,
payment evidence, and eval status agree.

Payment flow: static A2A/MCP/x402 bundle first; localnet transaction-shape
rehearsal second; devnet only after result/receipt decoupling tests are green.

Success metric: testers can identify at least one payment-settled/service-failed
case and one service-returned/payment-missing case from the evidence bundle.

Feedback loop: issue-template-driven reports with expected vs observed
authority, payment, service, eval, and receipt states.

Guardrails: fixture counterparties, no autonomous discovery of unknown services,
no live MCP invocation, no facilitator calls, no real settlement.

## Audit Prep Deltas

| Area | Delta before devnet tester expansion | Audit-ready expectation |
|---|---|---|
| Invariants | Define supply/balance, escrow/settlement, receipt uniqueness, authority-scope, fee-payer, and reputation-emission invariants. | Invariants are implemented as unit, property, or scenario tests and referenced from the audit packet. |
| Replay resistance | Add nonce, mandate id, request hash, response hash, expiry, and transaction signature replay tests. | Replayed or stale mandates cannot spend or emit receipts/reputation. |
| Atomicity | Test payment-settled/service-failed, service-returned/payment-missing, partial multi-step workflow, and rollback-required cases. | Receipt state cannot claim success unless payment, service, and eval states all satisfy policy. |
| Delegated authority | Enforce principal, spender, payee, purpose, scope, rail, asset/mint, amount cap, time window, and revocation. | Every spend-capable path has a bounded mandate or fails before execution. |
| Spend limits | Add per-intent, per-task, per-tester, per-day, and global dry-run/devnet caps. | Limits are enforced before signing and again before receipt completion. |
| Privacy/PII | Redact user intent text when not needed; hash request/response payloads; avoid storing wallet/user identifiers beyond audit necessity. | Receipt proofs are useful for disputes without leaking raw PII or secrets. |
| Settlement proof | Specify required Solana signature, confirmation level, mint/program allowlist, amount, payee, payer/agent id, and chain/env labels. | Devnet receipts cannot be confused with mainnet receipts; mainnet requires finalized/compliance-grade records where applicable. |
| Kill switch | Add operator disable, mandate revocation, per-agent suspension, per-rail pause, and rollback evidence. | Incident response can stop future spend and mark prior receipts for review without mutating historical evidence. |

## Recommendations

1. Create a Surfpool/localnet external beta rehearsal packet as the next
   executable child after #356. It should consume #355 plus this packet and
   rehearse payment/authority/receipt state locally without devnet.
2. Add a Solana devnet external tester gate after localnet rehearsal. It should
   use a bounded cohort, devnet-only labels, tiny test caps, and receipt
   evidence that cannot be mistaken for mainnet.
3. Add a RAP x402/AP2 authority alignment and audit-prep packet before any
   payment-capable public beta. It should make the layer contract executable:
   x402 is payment evidence; AP2/FIDO/Verifiable Intent is authority; MCP auth
   is resource access; RAP binds the receipt/accounting/reputation envelope.
4. Keep mainnet blocked until official audit completion and explicit go-live
   readiness. Do not create any mainnet implementation child from this gate.

## Follow-Up Child Issues To Create Under #220

| Proposed issue | Purpose | Acceptance sketch |
|---|---|---|
| Build Surfpool/localnet external beta rehearsal packet | Convert the #355 release archive plus this roadmap into localnet-ready tester rehearsal evidence. | Packet covers localnet setup assumptions, fixture accounts/mints, authority/replay/receipt scenarios, rollback drills, no-devnet/no-mainnet guardrails, and deterministic tests. |
| Add Solana devnet external tester gate | Create a devnet-only tester gate after localnet rehearsal. | Gate covers cohort scope, devnet wallet/key separation, caps, allowlisted mints/programs, confirmation/settlement proof, feedback form, support/rollback, and no-mainnet guardrails. |
| Build RAP x402/AP2 audit-prep alignment packet | Make the cross-layer contract audit-ready before payment-capable beta. | Packet maps x402/AP2/FIDO/MCP/Solana/RAP fields into invariants, tests, privacy rules, receipt proof requirements, and kill-switch criteria. |

