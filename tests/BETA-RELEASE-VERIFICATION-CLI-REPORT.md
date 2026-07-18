# Beta Release Verification CLI Report

Issue: #269
Parent: #220
Related: #247

`scripts/beta_release_verification_cli.py` builds a deterministic, local/free/dry-run verification bundle before any beta runtime activation or hosted deployment. It consumes the pinned beta handoff archive plus local readiness/runtime/package evidence, then requires Surfpool, Docker, and Coolify evidence only when the selected profile asks for those environments.

## Evidence

- Scenario source: `tests/fixtures/beta-release-verification-scenarios.json`
- Generated evidence: `tests/fixtures/beta-release-verification.json`
- Focused test: `tests/test_beta_release_verification_cli.py`
- Smoke gate: `tests/smoke-validation.sh`

## Profiles

- `local-only`: handoff archive plus beta readiness, runtime RC, operator package, review UI, decision, preflight, rehearsal, and acceptance evidence.
- `local-validator`: local-only evidence plus Surfpool/local validator lane evidence.
- `docker`: local-only evidence plus Docker local/VPS lane evidence.
- `coolify`: local-only evidence plus Coolify staging/operator UI lane evidence.
- `full`: all local-only, Surfpool, Docker, and Coolify evidence.

## Guardrail Coverage

- Positive fixtures: local-only, local-validator, Docker, Coolify, and full-profile accept verdicts.
- Negative fixtures: missing handoff, stale handoff hash, missing profile-required rollback/teardown evidence, unsafe activation/deployment claims, unsafe network/payment/credential/mainnet flags, and reject verdicts for unsafe deployment claims.
- Boundary assertions: no service start, network access, credential access, wallet/payment/facilitator/settlement access, devnet/mainnet, live runtime activation, hosted deployment, package publishing, or spend.

Current outcome: #269 is ready for review as a local beta evidence verifier. It does not activate runtime, contact providers, access credentials, start Docker/Surfpool/Coolify, deploy, publish, settle payments, or approve mainnet.
