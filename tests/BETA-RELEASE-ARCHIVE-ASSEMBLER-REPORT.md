# Beta Release Archive Assembler Report

Issue: #275
Parent: #220
Follows: #273
Related: #247

`scripts/beta_release_archive_assembler.py` consumes the #273 release-candidate manifest and builds deterministic local/free/dry-run archive assembly metadata before any package publishing, hosted deployment, archive publishing, or live runtime activation. Default output is manifest-first/stdout only. A local manifest/checksum archive package is written only when an explicit `--archive-output-dir` is supplied.

## Evidence

- Scenario source: `tests/fixtures/beta-release-archive-assembler-scenarios.json`
- Generated manifest: `tests/fixtures/beta-release-archive-assembler.json`
- Focused test: `tests/test_beta_release_archive_assembler.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guardrail Coverage

- Positive fixture: accepted local archive assembly from the pinned #273 release-candidate manifest, including deterministic archive path/name metadata, manifest checksum, content-addressed inventory, evidence hashes, source commit, release id, release-candidate id, verdict, and operator next-step text.
- Negative fixtures: missing/stale RC manifest, stale included-file hashes, unexpected extra artifacts, missing demo/verifier evidence, unsafe activation/deployment/publishing/archive-publishing claims, credential-like leakage, unsafe env values, wallet/payment/facilitator/settlement requests, devnet/mainnet/live-network flags, and reject verdict for unsafe archive publishing.
- Regression coverage: explicit `archiveFiles` overrides are constrained to the accepted #273 release-candidate included files plus the RC manifest itself; matching-hash extra files fail closed, including credential-shaped extra content.
- Boundary assertions: dry-run by default, archive writing requires an explicit local output directory, and no service start, network access, credential access, wallet/payment/facilitator/settlement access, devnet/mainnet, live runtime activation, hosted deployment, package publishing, archive publishing, public publishing, or spend occurs.

Current outcome: #275 is review-ready as a local archive manifest/checksum assembly gate. It does not activate runtime, contact providers, access credentials, start Docker/Surfpool/Coolify, deploy, publish packages or archives, settle payments, or approve mainnet.
