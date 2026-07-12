# Static x402/MCP-to-RAP Bridge Report

_Generated for issue #137. Mode: report-only/static._

## Scope

This evidence covers deterministic bridge checks for x402-paid MCP service metadata that may later be handed to Reddi Agent Protocol.

No runtime agent was activated. No MCP server was resolved or invoked. No wallet, facilitator, settlement rail, credential, or external service was touched.

## Fixtures

- `tests/fixtures/rap-bridge-x402-paid-mcp-ready.json`: x402-paid MCP service metadata with bounded AP2-like mandate constraints, static x402 `PaymentRequired` / `PaymentSignature` / `PaymentResponse` vocabulary, receipt evidence, and reputation signals.
- `tests/fixtures/rap-bridge-x402-paid-mcp-unsafe.json`: negative fixture containing live server/facilitator fields, executable/env fields, wallet/signature material placeholders, live access claims, unbounded authority, and payment-only success.

## Expected Outcomes

- Ready fixture: `bridgeReady=true`; x402 vocabulary, authority, receipt, and reputation fields are preserved as RAP-ready or metadata-only.
- Unsafe fixture: `bridgeReady=false`; live execution, wallet/facilitator/server, live x402 resource URLs, unbounded authority, and payment-without-service-success paths are reported as unsafe or unsupported.
- Regression fixture mutation: an otherwise-ready bridge document with only `x402.PaymentRequired.resource=https://...` fails closed with `bridgeReady=false`.

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
