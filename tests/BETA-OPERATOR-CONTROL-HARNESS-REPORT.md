# Beta Operator-Control Harness Report

_Issue: #235._

This report covers the first executable local-only beta operator-control harness for ReddiAgent prototype runtime paths.

The harness does not approve mainnet. It proves that local beta runtime controls can be evaluated deterministically, that required beta observability events are emitted, and that unsafe control requests fail closed before any external side effect.

## Evidence

- Harness: `scripts/beta_operator_control_harness.py`
- Scenario fixture: `tests/fixtures/beta-operator-control-scenarios.json`
- Pinned output fixture: `tests/fixtures/beta-operator-control-harness.json`
- Test: `tests/test_beta_operator_control_harness.py`
- Smoke validation: `tests/smoke-validation.sh`

## Covered Controls

| Control | Evidence |
|---|---|
| Enable runtime path | Positive local-only drill enables `local-runtime-prototype` after policy and cost checks pass. |
| Disable runtime path | Positive and negative scenarios emit `runtime.disabled` before rollback or denial completion. |
| Pause provider calls | Required control is present before the local-only drill can pass. |
| Pause MCP invocation | Required control is present before the local-only drill can pass. |
| Pause payment handoff | Required control is present before the local-only drill can pass. |
| Force local-only mode | Every scenario returns `nextRuntimeMode=local-only`; live paths stay off. |

## Fail-Closed Fixtures

| Scenario | Boundary |
|---|---|
| `mainnet-enable-denied` | Mainnet runtime enable is denied because mainnet remains not approved. |
| `rollback-stop-missing` | Runtime activation fails if stop-first rollback evidence is missing. |
| `cost-ceiling-forces-local-only` | Runtime activation fails when estimated cost exceeds the local ceiling. |
| `privacy-payload-denied` | Runtime activation fails if raw prompt or other sensitive payload fields appear. |

## Boundaries

- Local-only deterministic evidence only.
- No network access, provider API call, credential lookup, MCP invocation, payment rail, wallet, facilitator, devnet run, mainnet run, deployment, or external spend.
- Mainnet deployment, settlement, and runs remain not approved and require separate signoff.

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_operator_control_harness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_operator_control_harness.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
