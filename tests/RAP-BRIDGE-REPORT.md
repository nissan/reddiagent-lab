# RAP Dry-Run Bridge Conformance Report

_Updated for issue #178. Mode: report-only/static._

## Scope

This evidence covers deterministic dry-run bridge conformance checks for x402-paid MCP service metadata that may later be handed to Reddi Agent Protocol.

No runtime agent was activated. No MCP server was resolved or invoked. No wallet, facilitator, settlement rail, credential, or external service was touched.

## Fixtures

- `tests/fixtures/rap-bridge-x402-paid-mcp-ready.json`: x402-paid MCP service metadata with bounded AP2-like mandate constraints, static x402 `PaymentRequired` / `PaymentSignature` / `PaymentResponse` vocabulary, receipt evidence, reputation signals, and a `conformance` block that keeps the bridge report-only.
- `tests/fixtures/rap-bridge-x402-paid-mcp-unsafe.json`: negative fixture containing live server/facilitator/settlement fields, executable/env fields, wallet/signature material placeholders, live access claims, unbounded authority, payment-only success, and an unsafe live-bridge conformance claim.

## Expected Outcomes

- Ready fixture: `bridgeReady=true`; x402 vocabulary, authority, receipt, reputation, and dry-run conformance fields are preserved as RAP-ready or metadata-only.
- Unsafe fixture: `bridgeReady=false`; live execution, wallet/facilitator/server/settlement, live x402 resource URLs, unbounded authority, unsafe conformance claims, and payment-without-service-success paths are reported as unsafe or unsupported.
- Regression fixture mutation: an otherwise-ready bridge document with only `x402.PaymentRequired.resource=https://...` fails closed with `bridgeReady=false`.

## Conformance Checks

The checker emits a deterministic `dryRunBridgeConformance` summary with:

- `x402-payment-evidence`
- `authority-mandate-bounded`
- `receipt-payment-plus-service-result`
- `reputation-after-receipt`
- `unsafe-live-field-scan`

These checks are evidence labels only. They do not create a live RAP bridge, verify settlement, call a facilitator, sign a payment, invoke MCP, or mutate reputation.

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
