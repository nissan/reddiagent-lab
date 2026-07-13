# RAP Dry-Run Bridge Conformance Report

_Updated for issue #187. Mode: report-only/static._

## Scope

This evidence covers deterministic dry-run bridge conformance checks for x402-paid MCP service metadata that may later be handed to Reddi Agent Protocol.

No runtime agent was activated. No MCP server was resolved or invoked. No wallet, facilitator, settlement rail, credential, or external service was touched.

## Fixtures

- `tests/fixtures/rap-bridge-x402-paid-mcp-ready.json`: x402-paid MCP service metadata with bounded AP2-like mandate constraints, static x402 `PaymentRequired` / `PaymentSignature` / `PaymentResponse` vocabulary, receipt evidence, reputation signals, and a `conformance` block that keeps the bridge report-only.
- `tests/fixtures/rap-bridge-x402-paid-mcp-unsafe.json`: negative fixture containing live server/facilitator/settlement fields, executable/env fields, wallet/signature material placeholders, live access claims, unbounded authority, payment-only success, and an unsafe live-bridge conformance claim.
- `tests/fixtures/rap-dry-run-receipt-reputation-conformance.json`: pinned positive `receiptReputationConformance` summary covering x402 receipt binding, AP2-like authority binding, service-result evidence, required eval-gate evidence, and reputation signals after receipt evidence.

## Expected Outcomes

- Ready fixture: `bridgeReady=true`; x402 vocabulary, authority, receipt, reputation, and dry-run conformance fields are preserved as RAP-ready or metadata-only.
- Unsafe fixture: `bridgeReady=false`; live execution, wallet/facilitator/server/settlement, live x402 resource URLs, unbounded authority, unsafe conformance claims, payment-without-service-success paths, payment-only receipt emission, and reputation-without-receipt evidence are reported as unsafe or unsupported.
- Regression fixture mutation: an otherwise-ready bridge document with only `x402.PaymentRequired.resource=https://...` fails closed with `bridgeReady=false`.

## Conformance Checks

The checker emits a deterministic `dryRunBridgeConformance` summary with:

- `x402-payment-evidence`
- `authority-mandate-bounded`
- `receipt-payment-plus-service-result`
- `reputation-after-receipt`
- `unsafe-live-field-scan`

These checks are evidence labels only. They do not create a live RAP bridge, verify settlement, call a facilitator, sign a payment, invoke MCP, or mutate reputation.

## Receipt And Reputation Checks

The checker also emits a deterministic `receiptReputationConformance` summary with:

- `x402-receipt-payment-ref-bound`
- `ap2-authority-ref-bound`
- `service-result-pass-required`
- `required-eval-gate-pass-required`
- `reputation-signals-after-receipt`

The passing fixture pins the x402 payment reference to the static payment response reference, binds `PaymentSignature.authorizationRef` to the AP2-like mandate id, requires `serviceResultStatus=pass`, requires `requiredEvalGateStatus=pass`, and preserves the required reputation signals `receipt_verified`, `service_result_pass`, and `required_eval_gate_pass`.

The unsafe fixture fails closed when receipt emission is payment-only or required reputation signals are missing. These are static report checks only; they do not verify a transaction, call a reputation service, or mutate any payment/reputation state.

## Boundary Flags

Every checker output explicitly reports:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

## Validation

Focused validation command:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_rap_bridge_report.py
```

Expected result:

```text
PASS RAP bridge report
```
