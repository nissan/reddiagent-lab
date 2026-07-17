# Beta Operator Local Dry-Run Package Report

Issue: #240

## Result

`scripts/beta_operator_dry_run_package.py` builds an operator-facing local-only dry-run review artifact before any beta runtime path is enabled. It verifies the #237 beta local runtime RC gate against its pinned artifact, binds the selected ADL path, captures an operator command transcript, captures a stop/rollback dry-run transcript, and emits a compact evidence index.

## Evidence Bundle

- Operator package scenarios: `tests/fixtures/beta-operator-dry-run-package-scenarios.json`
- Pinned operator package: `tests/fixtures/beta-operator-dry-run-package.json`
- RC gate artifact reused from #237: `tests/fixtures/beta-local-runtime-rc-gate.json`
- Readiness evidence: `tests/fixtures/beta-release-readiness.json`
- Operator-control evidence: `tests/fixtures/beta-operator-control-harness.json`
- Selected local runtime evidence: `tests/fixtures/local-executable-runtime-prototype.json`

The positive fixture selects `examples/tool-agent.yaml` and includes the package checker command, selected local runtime command, stop-first dry-run transcript, rollback completion transcript, current RC gate verification, and explicit mainnet-not-approved language.

## Fail-Closed Fixtures

- Missing operator identity
- Missing selected ADL path
- Missing stop/rollback transcript
- Stale RC gate evidence
- Non-local/runtime request
- Mainnet request

## Boundaries

This package is local/free/dry-run only. It does not use live runtime activation, provider APIs, live MCP servers, credentials, wallets, facilitators, payment rails, devnet, production gateways, deployment, npm publishing, external spend, or mainnet. Mainnet deployment, settlement, and runtime execution remain not approved and require separate Nissan signoff.
