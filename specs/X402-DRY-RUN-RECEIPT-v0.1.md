# x402 Dry-Run Receipt v0.1

_Loop 36. Anchor issue: #38._

## Purpose

Payment-capable agents need a safe dry-run receipt before real settlement.

## Receipt Shape

    receiptVersion: reddiagent.receipt/v0.1
    mode: dry-run
    agent: paid-specialist-researcher
    taskId: example-task
    paymentIntentId: pay-specialist
    railCandidates:
      - solana
      - base
      - stripe
    amount: "0.25"
    currency: USDC
    requestHash: sha256:...
    responseHash: sha256:...
    policyResults: []
    evalResults: []

## Rules

- Dry-run receipts must never claim settlement.
- Real settlement references are forbidden in dry-run mode.
- Receipt hash fields should be deterministic once implementation starts.
- Required eval gates must pass before emitting taskCompleted reputation signals.

## AP2/x402 Mandate Mapping

For report-only compatibility with AP2-style payment authorization, a Reddi payment intent can map to three static mandate references:

- `IntentMandate`: user intent, agent subject, bounded purpose/scope, expiry, and audit reference.
- `CartMandate`: merchant/cart evidence, exact item or service scope, price/asset summary, expiry, and audit reference.
- `PaymentMandate`: payment authority, max amount, asset, accepted rail, revocation reference, expiry, and audit reference.

The x402 dry-run receipt remains the Reddi evidence layer. It should preserve:

- `PaymentRequired` accepted rail/asset/amount/payee options;
- `PaymentSignature` proof or authorization reference, never raw signature or wallet material;
- `PaymentResponse` transaction or settlement reference as metadata only;
- request and response hashes;
- service-result status and required eval-gate status.

Report-only AP2/x402 mapping must explicitly report:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

Unsupported or unsafe mappings include over-broad mandate scope, unbounded budget, mismatched rail or asset, live endpoint URLs, credentials, wallet/private-key material, raw signatures, and payment success without service-result plus eval-gate success.

RAP facilitator profile output is metadata-only until a reviewed Reddi Agent Protocol runtime exists. It must not verify VCs, invoke facilitators, settle payments, touch wallets, call MCP services, or mutate receipts.
