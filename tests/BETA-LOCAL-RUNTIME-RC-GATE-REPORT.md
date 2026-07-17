# Beta Local Runtime Release-Candidate Gate Report

Issue: #237

## Result

`scripts/beta_local_runtime_rc_gate.py` builds a deterministic local-only beta RC evidence bundle by verifying the local executable runtime prototype, the beta operator-control harness, and beta release readiness evidence before accepting a selected ADL runtime path.

## Evidence Bundle

- Local runtime execution: `tests/fixtures/local-executable-runtime-prototype.json`
- Operator-control trace events: `tests/fixtures/beta-operator-control-harness.json`
- Readiness criteria: `tests/fixtures/beta-release-readiness.json`
- RC gate scenarios: `tests/fixtures/beta-local-runtime-rc-gate-scenarios.json`
- Pinned merged bundle: `tests/fixtures/beta-local-runtime-rc-gate.json`

The positive fixture selects `tool-agent-execute-tools` and includes the local command, runtime completion, operator trace envelope, cost estimate, privacy redaction status, rollback stop-first evidence, and explicit mainnet-not-approved language.

## Fail-Closed Fixtures

- Missing enable control
- Missing disable control
- Non-local runtime mode
- Stale readiness evidence
- Missing rollback stop evidence
- Mainnet request

## Boundaries

This gate is local/free/dry-run only. It does not use live runtime activation beyond deterministic local fixture execution, provider APIs, live MCP servers, credentials, wallets, facilitators, payment rails, devnet, production gateways, deployment, npm publishing, external spend, or mainnet. Mainnet deployment, settlement, and runtime execution remain not approved and require separate Nissan signoff.
