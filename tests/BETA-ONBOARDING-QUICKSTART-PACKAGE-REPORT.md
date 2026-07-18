# Beta Onboarding Quickstart Package Report

Issue: #279
Parent: #220
Follows: #275, #277
Related: #247

`scripts/beta_onboarding_quickstart_package.py` builds a deterministic local/free/dry-run onboarding quickstart manifest that connects the #275 release archive evidence, #277 pitch demo refresh metadata, selected example ADLs, readiness fixtures, and reviewer commands into one local entrypoint before any runtime activation or publishing step.

## Evidence

- Scenario source: `tests/fixtures/beta-onboarding-quickstart-scenarios.json`
- Generated manifest: `tests/fixtures/beta-onboarding-quickstart.json`
- Focused test: `tests/test_beta_onboarding_quickstart_package.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guardrail Coverage

- Positive fixture: accepted local quickstart metadata for `reddiagent-beta-0`, release candidate `reddiagent-beta-0-rc-local-1`, archive manifest `tests/fixtures/beta-release-archive-assembler.json`, refreshed public demo proof links, three selected example ADLs, readiness/testing fixtures, local reviewer commands, expected outputs, and an operator next step.
- Local entrypoint: default command writes JSON to stdout only. The HTML and manifest entrypoint are written only when an explicit `--quickstart-output-dir` is supplied.
- Negative fixtures: missing/stale archive manifest, missing pitch page, stale pitch video script, missing/stale selected ADLs, unsafe activation/deployment/publishing claims, credential-like leakage, unsafe env values, wallet/payment/facilitator/settlement requests, devnet/mainnet/live-network flags, commands that start services or publish/fetch, and public demo fetch/publish mutation claims.
- Boundary assertions: dry-run by default, quickstart writes require an explicit local output directory, and no service start, network access, credential access, provider/API access, Docker/Surfpool/Coolify runtime, wallet/payment/facilitator/settlement access, devnet/mainnet, live runtime activation, hosted deployment, package publishing, archive publishing, public publishing, or spend occurs.

Current outcome: #279 is review-ready as a local onboarding quickstart package. Public demo URLs are metadata/proof links only; hosted content is not fetched, republished, or mutated by this lane. Mainnet remains blocked.
