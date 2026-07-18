# Surfpool Validator Lane Report

_Issue: #248. Parent: #247. Related: #220._

## Scope

This report adds deterministic local-only evidence for a Surfpool-backed Solana validator testing lane before any live devnet use.

Surfpool is the preferred path when RAP/payment/receipt prototypes need validator behavior. Plain `solana-test-validator` is allowed only as an explicit fallback when Surfpool is unavailable or the task only needs baseline validator semantics.

## Evidence

- Script: `scripts/surfpool_validator_lane.py`
- Scenario fixture: `tests/fixtures/surfpool-validator-lane-scenarios.json`
- Pinned evidence fixture: `tests/fixtures/surfpool-validator-lane.json`
- Test: `tests/test_surfpool_validator_lane.py`
- Smoke gate: `tests/smoke-validation.sh`

## Scenarios

| Scenario | Expected result | Evidence |
|---|---:|---|
| `surfpool-local-receipt-pass` | pass | Surfpool local mode, loopback localnet, local account/program state, lamport/token deltas, receipt, teardown, rollback, and mainnet denial. |
| `solana-test-validator-fallback-pass` | pass | Explicit fallback rationale, loopback localnet, local account/program state, deltas, teardown, rollback, and no Surfpool evidence claim. |
| `missing-surfpool-evidence-denied` | fail closed | Surfpool mode cannot pass without Surfpool evidence. |
| `fallback-without-rationale-denied` | fail closed | Fallback mode requires a rationale. |
| `unsafe-cluster-selection-denied` | fail closed | Non-local cluster/mainnet selection is denied. |
| `missing-teardown-denied` | fail closed | Missing validator teardown and ledger cleanup are denied. |
| `credential-like-payload-denied` | fail closed | Credential-like payload keys/values are denied. |
| `wallet-request-denied` | fail closed | Wallet access is denied. |
| `payment-facilitator-request-denied` | fail closed | Standalone payment, payment rail, payment access, facilitator, settlement request, and settlement claim fields are denied. |
| `devnet-request-denied` | fail closed | Devnet is denied by default for this local lane. |
| `missing-state-deltas-denied` | fail closed | Lamport and token before/after evidence is required. |

## Boundary

- This script does not install Surfpool or any dependency.
- This script does not start a validator.
- Evidence is deterministic and local-only.
- No credential, wallet, facilitator, payment rail, settlement, MCP, provider/API, devnet, mainnet, deployment, package publishing, or external spend is used.
- Mainnet remains blocked without fresh Nissan approval.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/surfpool_validator_lane.py --output tests/fixtures/surfpool-validator-lane.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_surfpool_validator_lane.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
