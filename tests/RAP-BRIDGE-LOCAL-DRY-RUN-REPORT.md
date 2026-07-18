# RAP Bridge Local Dry-Run Report

_Issue: #245. Scope: local executable dry-run prototype only._

## Summary

- `scripts/rap_bridge_local_dry_run.py` evaluates deterministic local RAP bridge scenarios from `tests/fixtures/rap-bridge-local-dry-run-scenarios.json`.
- Positive evidence is pinned at `tests/fixtures/rap-bridge-local-dry-run.json`.
- The passing scenario binds one `runId` across trace, receipt, payment handoff, operator transcript, source, budget, rollback, and reputation evidence.
- The generated artifact includes RAP-style intent, quote, metadata-only payment handoff, dry-run receipt, operator evidence, source evidence, budget evidence, rollback proof, reputation evidence, and trace events.

## Fail-Closed Coverage

The fixture and `tests/test_rap_bridge_local_dry_run.py` cover:

- missing receipt binding;
- missing runtime trace;
- unapproved payment rail;
- wallet, facilitator, and settlement request;
- non-boolean truthy mainnet and wallet request flags;
- live MCP request;
- devnet request outside this issue scope;
- mainnet request.

## Boundary

This prototype does not call a live RAP bridge, invoke MCP, call providers/models, read credentials, touch wallets/facilitators/payment rails/settlement, use devnet/mainnet, deploy, publish packages, or spend externally. All payment and reputation fields are local dry-run metadata.

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/rap_bridge_local_dry_run.py --output tests/fixtures/rap-bridge-local-dry-run.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_rap_bridge_local_dry_run.py
```
