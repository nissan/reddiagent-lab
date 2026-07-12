# Static AP2/x402 Mandate Mapping Report

_Added for issue #133._

This evidence covers deterministic, report-only mapping from Reddi payment extension metadata to AP2-style mandates and x402 payment evidence.

No runtime agent was activated. No MCP server was resolved or invoked. No wallet, facilitator, settlement rail, credential, verifier, issuer, payment network, or external service was touched.

## Fixtures

- `tests/fixtures/ap2-x402-mandate-ready.json`: bounded Reddi payment intent and budget mapped to AP2 `IntentMandate`, `CartMandate`, and `PaymentMandate`, with static x402 `PaymentRequired` / `PaymentSignature` / `PaymentResponse` vocabulary and RAP facilitator profile metadata.
- `tests/fixtures/ap2-x402-mandate-lossy.json`: negative fixture with live access claims, live URLs, wallet/signature material placeholders, over-broad mandate scopes, unbounded budget, rail/asset mismatch, and payment-only success.

## Report Contract

The checker reports:

- `ap2Ready`: true only when all three mandates are bounded and map cleanly to Reddi budget/receipt metadata.
- `rapFacilitatorProfile`: `metadata-only` for ready fixtures and `blocked` for unsafe/lossy fixtures.
- `mandateMapping`: Reddi intent/cart/budget/receipt fields mapped to AP2 mandates and RAP receipt policy.
- `metadataOnly`: AP2 Verifiable Credential refs, x402 payment evidence, and RAP facilitator profile sections that are preserved but not executed or verified.
- `unsupported` and `unsafe`: lossy, over-broad, live, or payment-only-success paths.

## Static Boundary

Every report hard-codes:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

## Validation

Focused validation:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_ap2_x402_mandate_report.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/ap2_x402_mandate_report.py tests/fixtures/ap2-x402-mandate-ready.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/ap2_x402_mandate_report.py tests/fixtures/ap2-x402-mandate-lossy.json # exits 2
```

The full smoke validation includes this guard.

## References

- `specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md`
- `specs/RAP-BRIDGE-v0.1.md`
- `specs/X402-DRY-RUN-RECEIPT-v0.1.md`
- `research/2026-07-08-x402-mcp-micropayments.md`
- Google Cloud AP2 announcement: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol
- AP2 documentation mirror used for static vocabulary review: https://ap2-protocol.org/
