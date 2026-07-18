# Beta Release Candidate Bundle Report

Issue: #273
Parent: #220
Follows: #269, #271
Related: #247

`scripts/beta_release_candidate_bundle.py` builds a deterministic local/free/dry-run release-candidate manifest before any live runtime activation, package publishing, or hosted deployment. It consumes the pinned #269 verifier output and #271 public demo/video package evidence, treats public demo URLs as metadata only, and emits source commit, release id, release-candidate id, artifact inventory, evidence hashes, included/excluded files, verdict, and operator next-step text.

## Evidence

- Scenario source: `tests/fixtures/beta-release-candidate-bundle-scenarios.json`
- Generated manifest: `tests/fixtures/beta-release-candidate-bundle.json`
- Focused test: `tests/test_beta_release_candidate_bundle.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guardrail Coverage

- Positive fixture: accepted local release-candidate bundle with full #269 verifier evidence plus #271 demo/video metadata.
- Negative fixtures: missing verifier evidence, stale verifier hash, missing demo plan, missing video evidence, unsafe activation/deployment/publishing claims, credential-like leakage, unsafe env values, wallet/payment/facilitator/settlement requests, devnet/mainnet/live-network flags, and reject verdict for unsafe deployment claims.
- Boundary assertions: no service start, network access, credential access, wallet/payment/facilitator/settlement access, devnet/mainnet, live runtime activation, hosted deployment, package publishing, public publishing, or spend.

Current outcome: #273 is review-ready as a local release-candidate packaging gate. It does not activate runtime, contact providers, access credentials, start Docker/Surfpool/Coolify, deploy, publish, settle payments, or approve mainnet.
