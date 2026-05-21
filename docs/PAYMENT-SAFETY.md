# Payment Safety Notes

_Loop 60. Anchor issue: #61._

## Rules

- Payment examples default to dry-run.
- Dry-run receipts must never imply settlement.
- Real payment requires budget policy.
- Real payment requires receipt enforcement.
- Human approval is required above configured thresholds.
- Reputation signals require evidence references.

## Current Boundary

ReddiAgent Lab can define payment intent and receipt shape. Reddi Agent Protocol owns real settlement semantics.

