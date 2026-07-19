# Beta Runtime Service-Wrapper Operator Run Package Report

Issue: #299
Parent: #220
Mode: deterministic local evidence only

## Scope

This package consumes the merged #297 service-wrapper activation smoke evidence by pinned path and sha256 from merge `e3ba3b4d51145a45f70e5bc0785f97665bc9cbdb`, then records the next bounded local operator-run package for `examples/simple-agent.yaml`.

The package proves only local, ephemeral wrapper state and operator evidence:

- exact simple-agent scope
- bounded local command transcript
- trace/eval summary
- before/enable/disable/rollback wrapper state
- hold or rollback operator decision
- rollback/disable verification
- risk verdict and next-step cue

## Guardrails

The fixture fails closed for stale #297 evidence, stale #297 report evidence, missing current operator approvals, wrong ADL scope, unsafe wrapper state, unsafe transcript commands, missing trace/eval evidence, missing rollback/disable proof, credential-like payloads, live service/container/hosted/provider/MCP/payment/devnet/mainnet requests, package/archive publishing requests, and activation-completed claims.

No external service, host process, Docker container, Surfpool validator, Coolify app, hosted deployment, provider API, live MCP server, wallet, payment rail, facilitator, settlement flow, devnet, mainnet, package publish, archive publish, or public publish is started or mutated.

## Evidence

- Scenario fixture: `tests/fixtures/beta-runtime-service-wrapper-operator-run-package-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-service-wrapper-operator-run-package.json`
- Focused test: `tests/test_beta_runtime_service_wrapper_operator_run_package.py`
- Builder: `scripts/beta_runtime_service_wrapper_operator_run_package.py`

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_service_wrapper_operator_run_package.py --output tests/fixtures/beta-runtime-service-wrapper-operator-run-package.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_wrapper_operator_run_package.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_wrapper_activation_smoke.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/beta_runtime_service_wrapper_operator_run_package.py tests/test_beta_runtime_service_wrapper_operator_run_package.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```

## Next Step

Hold after this local service-wrapper operator run package. A separate bounded external-service activation run is still required before any real service mutation, provider access, devnet run, or mainnet action. Mainnet remains blocked without fresh Nissan approval.
