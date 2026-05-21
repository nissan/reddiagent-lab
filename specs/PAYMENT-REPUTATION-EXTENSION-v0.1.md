# Payment and Reputation Extension v0.1

_Loop 7. Anchor issue: #7._

## Goal

Let a ReddiAgent harness express payment and reputation capabilities without binding the agent to one settlement rail.

## Extension Shape

    extensions:
      x402:
        enabled: true
        intents:
          - id: pay-for-research
            direction: spend
            maxAmount: "0.10"
            currency: USDC
            rails: [solana, base, stripe]
            requireReceipt: true
        policy:
          budgetPerTask: "0.25"
          requireHumanApprovalAbove: "1.00"
      receipts:
        required: true
        include:
          - requestHash
          - responseHash
          - toolCalls
          - settlementReference
      reputation:
        emitSignals:
          - taskCompleted
          - receiptVerified
          - evalPassed

## Rail Neutrality

Payment intents describe economic behavior. Rail adapters execute it.

Supported initial rail names: solana, base, stripe, other-x402.

## Reputation Rule

Reputation should attach to agent identity plus harness behavior. Raw model output alone is not enough.

Useful signals:

- completed work with receipt;
- eval gate passed;
- budget policy respected;
- tool permission respected;
- dispute/refund outcome;
- human review outcome.

## RAP Boundary

ReddiAgent describes payment/reputation requirements. Reddi Agent Protocol can provide settlement, receipts, verification, and reputation semantics.

