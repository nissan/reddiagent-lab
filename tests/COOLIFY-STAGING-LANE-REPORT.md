# Coolify Hosted Staging / Operator UI Lane Report

Issue: #250
Parent: #247
Related: #220

`scripts/coolify_staging_lane.py` builds deterministic, local-only evidence for deciding when ReddiAgent should use Coolify hosted staging and operator UI testing. The lane records local-first selection criteria, app/service boundaries, pinned source and image inputs, environment-variable contracts without values, private network/access-control expectations, health-check expectations, redacted logs, storage cleanup, teardown, rollback, and operator UI evidence requirements.

## Evidence

- Scenario source: `tests/fixtures/coolify-staging-lane-scenarios.json`
- Generated evidence: `tests/fixtures/coolify-staging-lane.json`
- Focused test: `tests/test_coolify_staging_lane.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guardrail Coverage

- Positive fixtures: local static/operator review evidence and Coolify-staging-required selection evidence.
- Negative fixtures: unpinned source, unpinned image, public exposure, secret env value persistence, missing teardown/rollback/cleanup, missing or unsafe health checks, devnet/mainnet/live-network flags, production/deployment claims, credential-like payload leakage, missing operator UI evidence, and wallet/payment/facilitator/settlement requests.
- Boundary assertions: no Coolify mutation, hosted service use, credential persistence, public exposure, live MCP invocation, provider/API calls, devnet/mainnet, package publication, deployment, settlement, or spend.

Current outcome: #250 is ready for review as a hosted staging/operator UI evidence contract. It is not a live Coolify deployment and does not claim runtime, deployment, settlement, or production readiness.
