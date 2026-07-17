# ADR 0005: Receipts and Reputation Sit Above Payment Evidence

## Status

Accepted.

## Context

x402 and AP2-style mandates can express payment requirements, authority, and transaction evidence, but Reddi Agent Protocol needs more than proof that money moved. It needs evidence that work was requested, bounded, performed, evaluated, and attributable for future reputation.

Relevant references:

- `research/2026-07-08-x402-mcp-micropayments.md`
- `specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md`
- `specs/X402-DRY-RUN-RECEIPT-v0.1.md`
- `specs/RAP-BRIDGE-v0.1.md`
- `specs/REPUTATION-SIGNALS-v0.1.md`
- `tests/AP2-X402-MANDATE-REPORT.md`
- `tests/RAP-BRIDGE-REPORT.md`

## Decision

Reddi receipts and reputation sit above x402/AP2-style payment evidence.

x402 payment evidence and AP2-like authority constraints are inputs to the ReddiAgent/RAP evidence model. They do not replace Reddi receipts, eval outcomes, reputation signals, source-boundary evidence, or harness traces.

## Consequences

- Payment metadata remains optional harness metadata until an approved live payment lane exists.
- RAP bridge reports should preserve payment evidence, authority constraints, receipt fields, reputation signals, and unsupported semantics separately.
- A successful payment is not sufficient proof of successful work.
- Future settlement or facilitator integrations must link payment evidence back to task, trace, eval, receipt, and reputation evidence.
