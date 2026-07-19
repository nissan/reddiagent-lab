# Beta Runtime Activation Evidence Gate Report

Issue: #287

This report covers the deterministic local/free beta runtime activation evidence gate. The gate consumes the accepted #285 E2E acceptance smoke fixture by pinned path and sha256, selects the smallest reviewed local in-process runtime path (`examples/simple-agent.yaml` through `scripts/run_local_agent.py`), and emits one operator/reviewer activation evidence artifact before any live runtime or service activation.

## Evidence

- Script: `scripts/beta_runtime_activation_evidence_gate.py`
- Scenarios: `tests/fixtures/beta-runtime-activation-evidence-gate-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-activation-evidence-gate.json`
- Test: `tests/test_beta_runtime_activation_evidence_gate.py`

## Local Boundaries

- No external network or hosted demo fetch.
- No service start or live runtime activation.
- No Docker, Surfpool, Coolify, gateway, or production mutation.
- No credential access or storage.
- No provider/model API call or live MCP invocation.
- No wallet, payment, facilitator, or settlement rail access.
- No devnet or mainnet transaction.
- No package or archive publishing.

## Validation

Run from the repository root:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_activation_evidence_gate.py --output tests/fixtures/beta-runtime-activation-evidence-gate.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_activation_evidence_gate.py
```

Mainnet remains blocked until fresh Nissan approval.
