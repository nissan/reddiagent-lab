# Reputation Signals v0.1

_Loop 37. Anchor issue: #39._

## Purpose

Reputation should describe verified harness behavior, not raw model confidence.

## Signal Types

| Signal | Meaning |
|---|---|
| taskCompleted | Harness reached a valid completion state |
| evalPassed | Required eval gates passed |
| receiptVerified | Receipt exists and matches task/payment metadata |
| budgetRespected | Spend stayed within configured policy |
| toolPolicyRespected | Tools stayed within permission boundary |
| humanApproved | Human approval was obtained where required |
| disputeOpened | A user or counterparty disputed the result |
| refundIssued | Payment was reversed or refunded |

## Minimum Fields

- signal
- agentId
- taskId
- timestamp
- evidenceRef
- issuer
- confidence

## Rule

Signals should be append-only and evidence-backed.

