# Beta Runtime Activation Canary Runner Report

Issue: #289

This report covers the deterministic local/free beta runtime activation canary runner. The runner consumes the accepted #287 activation evidence fixture by pinned path and sha256, selects the same reviewed local in-process simple ADL runtime path (`examples/simple-agent.yaml` through `scripts/run_local_agent.py`), and emits one canary evidence artifact before any live runtime or service activation.

## Evidence

- Script: `scripts/beta_runtime_activation_canary_runner.py`
- Scenarios: `tests/fixtures/beta-runtime-activation-canary-runner-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-activation-canary-runner.json`
- Test: `tests/test_beta_runtime_activation_canary_runner.py`

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
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_activation_canary_runner.py --output tests/fixtures/beta-runtime-activation-canary-runner.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_activation_canary_runner.py
```

Mainnet remains blocked until fresh Nissan approval.
