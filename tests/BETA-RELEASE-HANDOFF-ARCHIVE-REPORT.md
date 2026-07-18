# Beta Release Handoff Archive Report

Issue: #264
Parent epic: #220

## Scope

`scripts/beta_release_handoff_archive.py` builds a deterministic local-only release handoff archive from the pinned #262 activation acceptance bundle. It emits accepted, hold, and rollback-required handoff archives for `reddiagent-beta-0` without enabling runtime paths, deploying, publishing packages, using devnet/mainnet, calling providers, invoking MCP, touching credentials, or claiming activation occurred.

## Evidence

- Positive fixture coverage: accepted, hold, rollback-required handoff archives.
- Negative fixture coverage: missing/stale acceptance evidence, mismatched release id, mismatched ADL path, missing operator identity, missing reviewer or approval fixture, missing handoff timestamp, missing accepted activation cue, missing rollback cue/evidence, live runtime request, credential-like payload, devnet/mainnet request, production/mainnet enablement claim, deployment request/claim, activation occurred claim, live runtime enablement claim, incomplete handoff boundary text, contradictory activation handoff, and contradictory deployment handoff.
- Source package binding: acceptance, rehearsal, preflight, operator decision, review UI, runtime package, and inherited evidence hashes.
- Operator transcript/checklist: every path uses `--dry-run`, sets `liveRuntimeEnabled=false`, sets `deploymentPublished=false`, and carries next-step text that says no live runtime enablement, no deployment, and no activation is claimed.

## Validation

Run:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_release_handoff_archive.py > tests/fixtures/beta-release-handoff.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_release_handoff_archive.py
```
