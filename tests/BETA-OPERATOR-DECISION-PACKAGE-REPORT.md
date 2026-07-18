# Beta Operator Decision Package Report

Issue: #256

`scripts/beta_operator_decision_package.py` builds a deterministic local-only operator decision package from the #246 review UI/package artifacts. It records approve, hold, and rollback decisions while binding each decision to the selected ADL path, release id, source package path, evidence hashes, operator identity, fixture timestamp, rollback cue, and beta boundary status.

## Evidence

- Decision package script: `scripts/beta_operator_decision_package.py`
- Decision scenario fixture: `tests/fixtures/beta-operator-decision-package-scenarios.json`
- Pinned decision output: `tests/fixtures/beta-operator-decision-package.json`
- Source review artifact: `tests/fixtures/beta-review-ui.json`
- Source package artifact: `tests/fixtures/beta-operator-dry-run-package.json`
- Focused test: `tests/test_beta_operator_decision_package.py`

## Decisions Covered

| Scenario | Expected result |
|---|---|
| `operator-approve-decision-pass` | Approve is recorded against pinned local evidence only. |
| `operator-hold-decision-pass` | Hold is recorded without enabling a runtime path. |
| `operator-rollback-decision-pass` | Rollback is recorded only with an explicit rollback cue. |

## Fail-Closed Coverage

- Missing operator identity
- Missing rollback cue for rollback
- Stale release/review package binding
- Live runtime request
- Devnet request
- Mainnet or production enablement claim
- Credential-like payload leakage

## Boundary

The package is fixture-only and performs no live runtime call, MCP invocation, provider/model/API call, credential access, wallet/facilitator/payment rail/settlement access, devnet/mainnet action, deployment, package publishing, or external spend. Production and mainnet enablement remain not approved.
