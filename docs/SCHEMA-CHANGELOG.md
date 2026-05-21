# Schema Changelog

_Loop 71. Anchor issue: #81._

## 2026-05-22

- Added ADL v0.1 JSON Schema.
- Added policy type enum.
- Added eval gate type enum.
- Added extension namespace registry.
- Added invalid example for missing harness instructions.
- Added builder-facing validation guidance without changing the ADL schema contract.
- Added invalid fixture examples for unsupported model capability, unsupported runtime target, invalid tool id, duplicate fallback providers, and invalid x402 rails.
- scripts/validate_examples.py now defaults to builder-facing text while preserving --format raw and adding --format json for UI/CI consumers.

## Compatibility

Current valid examples still pass after policy/eval enum tightening.
