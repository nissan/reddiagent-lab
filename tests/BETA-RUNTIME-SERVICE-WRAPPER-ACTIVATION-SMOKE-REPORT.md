# Beta Runtime Service-Wrapper Activation Smoke Report

Issue: #297
Parent: #220
Mode: deterministic local evidence only

## Scope

This package consumes the merged #295 bounded live-run gate evidence by pinned path and sha256 from merge `b759ae7ef0742a65baa9a8e18e7fe88d920ee16c`, then records a local ephemeral service-wrapper state smoke for `examples/simple-agent.yaml`.

The smoke proves only local JSON-like wrapper state transitions:

- before: disabled
- enable: local wrapper state flips to enabled, with no external process PID
- disable: local wrapper state returns to disabled
- rollback: local wrapper state remains disabled

## Guardrails

The fixture fails closed for stale #295 evidence, stale #295 report evidence, missing current operator approvals, wrong ADL scope, unsafe wrapper state, unsafe transcript commands, missing trace/eval evidence, missing rollback/disable proof, credential-like payloads, live service/container/hosted/provider/MCP/payment/devnet/mainnet requests, package/archive publishing requests, and activation-completed claims.

No external service, host process, Docker container, Surfpool validator, Coolify app, hosted deployment, provider API, live MCP server, wallet, payment rail, facilitator, settlement flow, devnet, mainnet, package publish, archive publish, or public publish is started or mutated.

## Evidence

- Scenario fixture: `tests/fixtures/beta-runtime-service-wrapper-activation-smoke-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-service-wrapper-activation-smoke.json`
- Focused test: `tests/test_beta_runtime_service_wrapper_activation_smoke.py`
- Builder: `scripts/beta_runtime_service_wrapper_activation_smoke.py`

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_service_wrapper_activation_smoke.py --output tests/fixtures/beta-runtime-service-wrapper-activation-smoke.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_wrapper_activation_smoke.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_activation_live_run_gate.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/beta_runtime_service_wrapper_activation_smoke.py tests/test_beta_runtime_service_wrapper_activation_smoke.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```

## Next Step

Hold after this local service-wrapper activation smoke. A separate bounded operator run is still required before any external service mutation, provider access, devnet run, or mainnet action. Mainnet remains blocked without fresh Nissan approval.
