# Observability v0.1

_Loop 17. Anchor issue: #18._

## Purpose

An agent harness must be inspectable. Prosumers need to see what happened, why, and what it cost.

## Events

- session.started
- model.called
- tool.called
- policy.checked
- eval.checked
- payment.intent.created
- payment.settled
- receipt.emitted
- reputation.signal.emitted
- task.completed
- task.failed

## Trace Fields

- traceId
- agentId
- taskId
- model
- runtime
- toolCalls
- policyResults
- evalResults
- tokenUsage
- costEstimate
- paymentReferences
- receiptReference

## Builder UX Requirement

Every example runtime should produce a human-readable run summary before it produces a dashboard integration.

