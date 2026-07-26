# Agent Payments Landscape and Backlog Alignment

_Date: 2026-07-26 AEST. Follows the 2026-07-23 recalibration (#356) and the
2026-07-25 standards refresh (#374/#381). Three live research sweeps: protocol
landscape, Solana ecosystem, academic/cross-chain. Sources checked 2026-07-26._

## Executive Verdict

The rails are consolidating fast (x402 under Linux Foundation governance,
MPP as the main non-crypto rail, AP2 mandates converging with Verifiable
Intent), but **no protocol yet binds settlement proof to verified service
delivery** — RAP's receipt-integrity thesis is validated by peer-reviewed
security research and its window is open, while adjacent squares fill in from
the edges (Mastercard Verifiable Intent, Nevermined outcome pricing, Virtuals
ACP onchain evaluations, MCP-attestation receipt projects). The Solana trust
layer moved under us: a Foundation-endorsed Agent Registry (ERC-8004 port) and
SATI are live on mainnet, both building on Solana Attestation Service.
Launching RAP reputation siloed from those would be a strategic error.

## 1. Protocol landscape (delta since 2026-07-23)

| Finding | Source (date) | Implication |
|---|---|---|
| x402 Foundation operational under Linux Foundation 2026-07-14; 40 members; premier board incl. Solana Foundation, Stripe, Visa, Mastercard, AWS, Google, Circle, Cloudflare | tftc.io, techtimes.com (Jul 2026) | ADL's x402 authority contracts bind to an LF-governed standard, not a vendor product. Track the TSC for spec churn. |
| x402 V2 (2025-12-11) is current: Solana first-class, dynamic recipients, wallet sessions, **automatic discovery metadata** facilitators index; `/.well-known/x402` + CDP Bazaar are the catalog conventions | x402.org/x402-v2-launch, docs.cdp.coinbase.com/x402/bazaar | ADL's missing price-discovery field should be *pointers* to V2 discovery metadata / `.well-known/x402` / registry refs — not a bespoke price schema. |
| MPP (Stripe/Tempo, 2026-03-18): session-based streamed micropayments, 100+ launch services, Cloudflare dual-supports x402+MPP, Circle published a Solana USDC charge spec, Pay.sh speaks both | stripe.com/blog, github.com/tempoxyz/mpp-specs, developers.cloudflare.com | MPP stays non-canonical in ADL but its adapter priority rises; ADL's payment-authority schema needs a session-cap concept before any MPP adapter is possible. |
| ACP (Stripe/OpenAI) spec 2026-04-17; checkout-oriented; ChatGPT Instant Checkout branding retired ~Mar 2026. **Naming collision**: Virtuals "Agent Commerce Protocol" (also ACP) entered public beta 2026-07-03 on Base, records agreements/evaluations onchain | github.com/agentic-commerce-protocol, whitepaper.virtuals.io | ACP (Stripe/OpenAI) confirmed non-canonical. All RAP docs must disambiguate the two ACPs. Virtuals ACP is a partial receipts competitor (ecosystem-bound). UCP (Google/Shopify) is watch-only. |
| AP2 v0.2.0 (Apr 2026): mandates are SD-JWT VCs with key binding, OpenID4VP presentation; A2A v1.0 under LF (Mar 2026); production-ready A2A x402 extension carries mandates into settlement | ap2-protocol.org, github.com/google-agentic-commerce/AP2 | AP2-FIDO mapping refresh has concrete targets: SD-JWT+kb / OpenID4VP formats; RAP receipts should ingest mandate hashes via the A2A x402 extension. |
| Mastercard Verifiable Intent became an open standard 2026-03-05 (FIDO+EMVCo+IETF+W3C base, selective disclosure) | pymnts.com | Closest incumbent to RAP's layer, but card-rail focused. Position RAP as the x402/stablecoin-rail counterpart; consider field mapping for cross-rail credibility. |
| Receipts space fragmenting: Notarized Agents (arXiv 2606.04193), Agent Receipts (Ed25519+W3C VC), Signet, IETF draft-farley-acta-signed-receipts, Microsoft compliance-receipts proposal — none payment-rail-bound | various (Jun–Jul 2026) | RAP's niche is open. Align the receipt envelope with the Ed25519 + W3C VC conventions these share; watch the IETF draft as a portability target. |
| Pay.sh = Solana Foundation + Google Cloud gateway (2026-05-05): x402 **and** MPP, PayAI settlement, 50+ API providers incl. Google Cloud APIs | solana.com/news | Queued Pay.sh report strengthened but must widen scope to MPP semantics. Pay.sh is both biggest competitor and biggest channel — its trust layer is the gap RAP fills. |

## 2. Solana ecosystem

| Finding | Source (date) | Implication |
|---|---|---|
| Foundation-endorsed **Agent Registry** (ERC-8004 port w/ Quantu, ~Mar 2026): Identity/Reputation/Validation registries, markets "API monetization with x402"; **SATI** (Cascade) live on mainnet+devnet (`satiRkxE…`); both build reputation on Solana Attestation Service | solana.com/agent-registry, docs.sati.cascade.fyi, SRFC #7 | Registry-compat work upgraded to urgent; RAP should emit/consume attestations compatible with the official registry (dual-publish reputation reveals as SAS attestations). |
| **Kora** fee relayer (Foundation, Apr 2026): gasless x402, fees payable in any SPL token, TEE/KMS signing | github.com/solana-foundation/kora | Solves "agent has stablecoin but no SOL"; the enabler for the AUDD story; adopt in the RAP client path. |
| **Surfpool** is now the default Anchor validator (Anchor v1.0, 2026-04-02) with copy-on-read **mainnet forking** | github.com/solana-foundation/surfpool | Ladder rung 1 upgrades: rehearse against forked mainnet state — real USDC/PYUSD/AUDD mints and live registry programs — before devnet. |
| x402-Solana dominant: ~77% of x402 volume (Dec 2025); facilitators: CDP (`@x402/svm`, all SPL tokens), PayAI (`solana` + `solana-devnet`), self-host via Faremeter or the Foundation's Kora facilitator guide | solana.com/x402, facilitator.payai.network | PayAI `solana-devnet` is the concrete devnet-gate rail. Self-hosting avoids single-vendor dependency. |
| Token-2022: all key extensions mainnet-live; PYUSD flagship adopter; **transfer hooks and confidential transfers cannot combine**; CT lacks wallet UX | solana.com/solutions/token-extensions | Re-scope the Token-2022 issue: (a) escrow *compatibility* with hook/fee-bearing third-party mints = launch-blocking; (b) RAP-issued receipt NFT / spend-limit token = post-launch; drop CT near-term. |
| AUDD live on Solana; issuer AUDC (Novatti) granted **ASIC AFSL Feb 2026**; zero evidence of AUDD in any agent-payment flow anywhere | audd.digital, rwa.xyz, australianfintech.com.au | First-mover window for AUD-denominated agent payments is real; expect to bootstrap facilitator support (Faremeter/Kora make arbitrary-SPL settlement feasible). |
| Alpenglow: BLS key registration on mainnet wk of 2026-07-20; full activation ~Oct 2026 (Agave 4.3, ~150ms finality). 60M CU live (SIMD-0256); Agave 4.0 QUIC-only + async sigverify | coindesk.com, SIMD-0286 | Launch lands pre-Alpenglow: no 150ms finality assumptions; plan a post-launch re-validation pass ~Oct; landing-reliability improvements are tailwind. |
| Adjacent: Tiny Place (agents pay agents via x402 bounties), PayAI marketplace, Flovia (Frontier winner — machine-paid API analytics) | solana.com news, blog.colosseum.com | "Agents discover and pay agents" is now a recognized category; Flovia validates receipts/analytics as a lane; RAP's escrow + commit-reveal + receipt integrity remains differentiated. |
| Calendar: **Colosseum Eternal Challenge open now** (~$250K pre-seed, closes ~early Sep); Superteam Agentic Engineering Grants rolling; Superteam Earn has AGENT_ALLOWED/AGENT_ONLY listings | colosseum.com/hackathon, superteam.fun | Best-fit venues for the 2026-08-31 launch; agent-only Earn listings are an on-brand demo target for the delegation examples. |

## 3. Academic anchors (receipt-integrity spec citations)

Primary anchors:

1. **"When HTTP 402 Meets the Blockchain"** (arXiv 2607.19545, USENIX Security
   2026): security-rule violations found in **all 15 major x402 facilitators**;
   4 attack classes (Free Shopping, Asset Theft, Service Denial, Gas Abuse);
   Coinbase fixed post-disclosure. Peer-reviewed proof that settlement
   evidence alone is untrustworthy.
2. **"Five Attacks on x402"** (arXiv 2605.11781): demonstrates both
   "unpaid service" and **"paid-but-denied"** — the core RAP invariant
   failing in the wild. Cite for replay + payment-service decoupling.
3. **"Zero-Trust Runtime Verification for AP2"** (arXiv 2602.06345):
   issuance-valid mandates still fail at runtime; consume-once nonces +
   context binding — semantics the RAP receipt model should encode.

Supporting: **TessPay** (2602.00213) verify-then-pay escrow validates
eval-gated settlement; **AgentBound** (2606.30970) independently converges on
multi-artifact cryptographic receipts (validates the 5-layer model);
**AgentReputation** (2605.00073) verifier-collusion threat model;
**skill-conditional reputation** (2606.14200) — receipts must tag the ADL
capability invoked, no single scalar score; **Whispers of Wealth**
(2601.22569) scope boundary: receipts attest *authorized/paid/delivered/
evaluated*, not *well-formed intent* (prompt injection upstream of mandate
signing is out of scope and must be stated as such); **Free-Riding**
(2605.30998) replay-window attack — bind payment proof to a single request ID.

Incidents in the wild: Oct 2025 x402-token exploit drained USDC from 200+
wallets; Hello402 unlimited-mint failure.

## 4. ERC-8004 status

Live on Ethereum mainnet + Base since ~2026-02-05 (spec page still "Draft";
effectively frozen for deployment). Identity = ERC-721 with A2A agent-card /
MCP endpoints native; Reputation = signed bounded feedback with optional
off-chain file that **explicitly supports a `proofOfPayment` object and names
x402 enrichment**; v2 working track is standardizing x402 payment-proof
schemas inside feedback attestations. Adoption measured at ~10k agents but
concentrated and shallow (arXiv 2606.12128) — the right interop target, not
yet a functioning economy; RAP receipts would be differentiated supply into
its Reputation/Validation registries. Target **v2's payment-proof schema**,
not v1's loose object. ERC-8126 (AI Agent Verification) noted, unverified.

Identity interop: AIP is now IETF `draft-prakash-aip-00` (IBCTs; Biscuit
chained mode fits RAP's delegation chain); OAuth agent drafts
(`draft-oauth-ai-agents-on-behalf-of-user-02`) define delegation-chain claims;
FIDO agentic TWGs seeded (no specs before ~2027 — watch-list).

## 5. Superteam member perks mapped to the release ladder

| Ladder stage | Perks to activate |
|---|---|
| Localnet/devnet staging | Helius 30% RPC; GetBlock ≤$10k/90d credits; Alchemy ≤$25k credits + 3mo platform ($1k/mo usage); Azxa 2wk dedicated RPC; Chainstack/Ironforge/Shyft free months |
| External tester gate | Privy 25% (tester wallet/auth onboarding); Civic 12mo free SaaS + 1,000 verifications (tester identity); zauth Vector free agentic-pentest credits |
| Audit-readiness → audit | Sec3 (Solana-specialized + OSS scans), Ackee 10% (Trident fuzzing), Adevar 25%, FYEO 40%, Cantina 15% + 1yr bug bounty, Hacken 10% + HackenProof bounty, Quantstamp/Zellic/QuillAudits |
| Production infra | OVHcloud ≤40% (Solana-node DDoS profiles), Carbium 6mo free + 10% lifetime |
| Funding/launch | Instagrants, Project Advisory, Fast Track, exclusive RFPs (Solana Foundation/Backpack), Reap $500 business banking; Colosseum Eternal Challenge |

## 6. Queued-backlog verdicts (input to the sanity check)

- **#376 Pay.sh/x402 discovery report** — keep, widen scope: cover MPP
  semantics, PayAI facilitator (incl. `solana-devnet`), x402 V2 discovery
  metadata and `.well-known/x402` conventions.
- **#377 AP2-FIDO mandate mapping refresh** — keep, now with concrete targets:
  AP2 v0.2.0 SD-JWT+kb, OpenID4VP, A2A v1.0 x402 extension, FIDO TWG watch.
- **#378 AIP + Agent Registry/SATI compatibility** — keep, upgrade priority:
  two live mainnet registries; add SAS attestation dual-publishing; update AIP
  citation to IETF I-D.
- **#379 Token-2022 evaluation** — keep, re-scope into escrow *compatibility*
  (launch-blocking) vs RAP-issued asset *issuance* (post-launch); drop
  confidential transfers near-term.
- **#380 MPP/ACP classification** — keep with corrections: ACP non-canonical
  confirmed; MPP non-canonical but adapter priority raised; add Virtuals-ACP
  disambiguation and UCP watch entry.
- **New scope with no issue yet**: receipt-integrity validator implementation
  (consumes #375's threat model; cites the academic anchors); charge-side
  conformance enforcement + price-discovery pointers (ADL v0.3 seeds from the
  delegation examples); Kora integration spike; Pay.sh listing/interop spike;
  ERC-8004 v2 payment-proof mapping refresh; Alpenglow post-launch
  re-validation; Surfpool mainnet-fork rehearsal upgrade; perks activation
  (RPC credits, audit-vendor shortlist, Instagrants/Colosseum applications);
  cross-repo TRACKS alignment; payments-builder education track; 2026-08-31
  launch plan with workback dates.

## Boundary

Research/report evidence only. No live invocation, settlement, credential
use, wallet/facilitator action, deployment, or registry mutation occurred.
Mainnet remains blocked behind official audit and explicit go-live approval.
