# Payment Dry-Run Receipt Fixture Report

Issue #157 refreshed the payment dry-run receipt fixture after the AP2/x402 and RAP bridge work.

## Evidence

- `examples/payment-agent.yaml` emits `static-payment-dry-run-receipt-report` with `receiptVersion=reddiagent.receipt/v0.2`.
- The receipt binds payment intent, rail candidates, bounded amount, request hash, response hash, service-result status, required eval-gate status, and allowed reputation signals.
- The negative fixture `tests/fixtures/payment-dry-run-receipt-unsafe.yaml` fails closed when input claims payment access, uses live facilitator/wallet fields, has an unbounded amount, or disables required receipts.

## Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

No wallet, facilitator, payment rail, settlement, credential, MCP server, provider, network, or live runtime path is invoked.
