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

