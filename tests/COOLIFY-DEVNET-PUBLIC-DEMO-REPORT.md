# Coolify Devnet Public Demo Report

Issue: #280
Parent: #220
Related: #247, #250, #277

`scripts/coolify_devnet_public_demo.py` records the readiness contract for moving the ReddiAgent demo from static-only review pages to a public Coolify-hosted devnet demo URL.

## Evidence

- Public entrypoint: `docs/index.html`
- Build path: explicit `Dockerfile` copying `docs/` into nginx, built on the VPS and deployed through Coolify's Docker Image resource from a loopback-only registry.
- Health route: `/`
- Scenario source: `tests/fixtures/coolify-devnet-public-demo-scenarios.json`
- Generated evidence: `tests/fixtures/coolify-devnet-public-demo.json`
- Focused test: `tests/test_coolify_devnet_public_demo.py`
- Public target URL: `https://reddiagent-devnet.preview.reddi.tech/`

## Guardrail Coverage

- Positive fixture: public Coolify preview, devnet scope, explicit nginx Dockerfile build, loopback-registry Docker Image deployment, root health route, local UI pages, and rollback metadata.
- Negative fixtures: mainnet claims, payment/settlement claims, missing health route, credential-like environment leakage, provider/live MCP claims, and production gateway mutation claims.
- Boundary assertions: devnet is allowed only for the public demo lane; mainnet, payment rails, settlement, wallet/facilitator access, embedded credential values, provider product calls, live MCP invocation, package publishing, and production gateway mutation remain blocked.

Current outcome: #280 removes the repo-side packaging roadblocks for a public Coolify devnet demo. Any live Coolify deployment evidence must still report the app UUID, public URL, route checks, health check, rollback/teardown notes, and redacted logs.
