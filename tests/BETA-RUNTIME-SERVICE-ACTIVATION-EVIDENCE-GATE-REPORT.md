# Beta Runtime Service Activation Evidence Gate Report

## Scope

This report covers the deterministic local/free post-#291 beta runtime service activation evidence gate. The gate consumes the accepted #291 approval packet by pinned path and sha256, validates its preserved #289/#287/#285 source hashes, records operator approvals and preflight checks, and emits bounded dry-run substitute evidence before any real service activation.

## Artifacts

- Script: `scripts/beta_runtime_service_activation_evidence_gate.py`
- Scenarios: `tests/fixtures/beta-runtime-service-activation-evidence-gate-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-service-activation-evidence-gate.json`
- Test: `tests/test_beta_runtime_service_activation_evidence_gate.py`

## Evidence Summary

- Pinned #291 approval packet fixture: `tests/fixtures/beta-runtime-service-activation-approval-packet.json`
- Pinned #291 approval packet sha256: `b5bd8232d1cca34387a24b71c412dec7e60a5e53c90d84d1a0737a3eef65227e`
- Preserved upstream evidence: #289 canary fixture, #287 activation evidence fixture, and #285 E2E smoke fixture all require `hashMatches: true`.
- Runtime path remains restricted to `examples/simple-agent.yaml` through `python scripts/run_local_agent.py examples/simple-agent.yaml`.
- Operator approvals recorded: runtime owner, rollback owner, security reviewer, and separate live activation run approval.
- Decision: hold for a separate live run; rollback is represented only as dry-run verification.
- Risk verdict: `hold-for-separate-live-run`

## Guardrails

The gate fails closed for missing, copied, or stale #291 evidence; missing upstream hash bindings; unsafe commands; credential-shaped payloads; hosted fetch/publish instructions; unauthorized Docker/Surfpool/Coolify/service mutation instructions; provider/live MCP access; devnet/mainnet flags; wallet/payment/facilitator/settlement access; package/archive publishing; production/mainnet claims; missing operator approval; missing rollback/disable evidence; missing trace/eval evidence; and ambiguous activation-completed claims.

This is not a live service activation. Mainnet remains blocked.

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_service_activation_evidence_gate.py --output tests/fixtures/beta-runtime-service-activation-evidence-gate.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_activation_evidence_gate.py
```
