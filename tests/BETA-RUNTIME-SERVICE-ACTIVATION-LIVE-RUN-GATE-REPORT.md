# Beta Runtime Service Activation Live-Run Gate Report

## Scope

This report covers the deterministic local/free #295 bounded beta runtime service activation live-run gate. The gate consumes the merged #293 evidence fixture and report by pinned path and sha256 from merge `2f956e536cdfa39b443a08709c1d7ea41ab0f8d0`, verifies the preserved #291 approval-packet hash, records current operator approval state, and emits bounded run evidence without starting a service.

## Artifacts

- Script: `scripts/beta_runtime_service_activation_live_run_gate.py`
- Scenarios: `tests/fixtures/beta-runtime-service-activation-live-run-gate-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-service-activation-live-run-gate.json`
- Test: `tests/test_beta_runtime_service_activation_live_run_gate.py`

## Evidence Summary

- Pinned #293 fixture: `tests/fixtures/beta-runtime-service-activation-evidence-gate.json`
- Pinned #293 fixture sha256: `bddc71ddf84bc5b20ecd3dd55d28e7159d87b38d1ecb04c5e66c29e6cc3b6bd9`
- Pinned #293 report: `tests/BETA-RUNTIME-SERVICE-ACTIVATION-EVIDENCE-GATE-REPORT.md`
- Pinned #293 report sha256: `0a90b83e5ef992faa1bba8c898f380066a70e300a42f4589b63feb2ee0129a56`
- Pinned #291 approval packet sha256: `b5bd8232d1cca34387a24b71c412dec7e60a5e53c90d84d1a0737a3eef65227e`
- Runtime scope remains restricted to `examples/simple-agent.yaml` through `python scripts/run_local_agent.py examples/simple-agent.yaml`.
- Decision: hold before actual service activation; rollback is represented only as dry-run verification.
- Risk verdict: `hold-before-actual-service-activation`

## Guardrails

The gate fails closed for stale or missing #293 evidence, stale #293 report hash, missing #291 approval-packet hash preservation, wrong activation scope, missing current operator approval, missing trace/eval evidence, missing rollback/disable evidence, unsafe commands, credential-shaped payloads, hosted fetch/publish instructions, unauthorized Docker/Surfpool/Coolify/service mutation instructions, provider/live MCP access, devnet/mainnet flags, wallet/payment/facilitator/settlement access, package/archive publishing, production/mainnet claims, and ambiguous activation-completed claims.

This is not an actual service activation. Mainnet remains blocked.

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_service_activation_live_run_gate.py --output tests/fixtures/beta-runtime-service-activation-live-run-gate.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_activation_live_run_gate.py
```
