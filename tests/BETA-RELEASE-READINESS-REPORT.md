# Beta Release Readiness Report

_Issue: #223._

## Scope

This report covers the first ReddiAgent beta readiness, observability, and operator runbook gate for executable prototypes.

The gate does not approve mainnet. It defines what evidence must exist before an executable prototype can be treated as beta-ready, what traces and logs must show, how operators enable and disable runtime paths, and how rollback or incident handling proceeds.

## Evidence

- Runbook: `docs/BETA-RELEASE-READINESS-RUNBOOK.md`
- Checker: `scripts/beta_release_readiness.py`
- Pinned fixture: `tests/fixtures/beta-release-readiness.json`
- Test: `tests/test_beta_release_readiness.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guarded Criteria

| Area | Required signal |
|---|---|
| Entry criteria | Smoke validation, current prototype evidence, negative fixtures, reviewed operator controls, and explicit mainnet denial. |
| Exit criteria | Incident-free observation, operator stop drill, cost/privacy review, and current rollback evidence. |
| Observability | Required beta events, required trace fields, raw secret denial, and redacted raw prompts by default. |
| Operator controls | Enable, disable, pause provider, pause MCP, pause payment handoff, and local-only fallback controls. |
| Rollback | Stop-first procedure, bounded disable window, evidence preservation, negative fixture rerun, and review before re-enable. |
| Incident notes | Cost, safety, privacy, and incident response notes. |

## Boundary

- Devnet may be used only when a queued beta task needs it and has bounded evidence.
- Mainnet deployment, settlement, and runs remain not approved until separate signoff.
- Secret material, raw payment proof, and raw prompts must not be logged in beta evidence.
- Operators can force local-only mode while keeping deterministic validation and reports available.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_release_readiness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_release_readiness.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
