# Beta E2E Acceptance Smoke Report

Issue: #285

This report covers the deterministic local/free/dry-run beta end-to-end acceptance smoke runner. The runner consumes the committed #279 onboarding quickstart fixture and #283 reviewer acceptance checklist fixture by pinned path and sha256, validates their accepted evidence payloads, and emits one reviewer/operator accept, hold, or reject evidence artifact before any runtime activation.

## Evidence

- Script: `scripts/beta_e2e_acceptance_smoke_runner.py`
- Scenarios: `tests/fixtures/beta-e2e-acceptance-smoke-scenarios.json`
- Generated fixture: `tests/fixtures/beta-e2e-acceptance-smoke.json`
- Test: `tests/test_beta_e2e_acceptance_smoke_runner.py`

## Local Boundaries

- No external network or hosted demo fetch.
- No service start or live runtime activation.
- No Docker, Surfpool, Coolify, gateway, or production mutation.
- No credential access or storage.
- No provider/model API call or live MCP invocation.
- No wallet, payment, facilitator, or settlement rail access.
- No devnet or mainnet transaction.
- No package or archive publishing.

## Validation

Run from the repository root:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_e2e_acceptance_smoke_runner.py --output tests/fixtures/beta-e2e-acceptance-smoke.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_e2e_acceptance_smoke_runner.py
```

Mainnet remains blocked until fresh Nissan approval.
