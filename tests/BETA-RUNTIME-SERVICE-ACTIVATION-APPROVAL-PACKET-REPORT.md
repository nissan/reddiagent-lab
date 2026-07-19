# Beta Runtime Service Activation Approval Packet Report

## Scope

This report covers the deterministic local/free beta runtime service activation approval packet. The packet consumes the accepted #289 canary runner fixture by pinned path and sha256, confirms it selected only the reviewed simple local ADL runtime path, and emits approval evidence before any live runtime or service activation.

## Artifacts

- Script: `scripts/beta_runtime_service_activation_approval_packet.py`
- Scenarios: `tests/fixtures/beta-runtime-service-activation-approval-packet-scenarios.json`
- Generated fixture: `tests/fixtures/beta-runtime-service-activation-approval-packet.json`
- Test: `tests/test_beta_runtime_service_activation_approval_packet.py`

## Evidence Summary

- Pinned #289 canary fixture: `tests/fixtures/beta-runtime-activation-canary-runner.json`
- Pinned #289 canary fixture sha256: `221cae416825b64b41a1b117d311bfc4ded3d0e53a9d49ef43f50faea26cb8dd`
- Required operator approvals: runtime owner, rollback owner, security reviewer, and separate live activation run approval.
- Env/secret requirements are emitted by name only with redacted values.
- Risk verdict: `approval-packet-ready`
- Stop cue: separate explicit live activation gate required before any service, runtime, Docker, Coolify, devnet, payment, package, or mainnet action.

## Guardrails

The packet fails closed for missing, copied, or stale canary evidence; missing #287/#285 upstream hashes; unsafe commands; credential-shaped payloads; hosted fetch/publish instructions; Docker/Surfpool/Coolify/service mutation instructions; provider/live MCP access; devnet/mainnet flags; wallet/payment/facilitator/settlement access; package/archive publishing; production/mainnet claims; and ambiguous activation-completed claims.

This is not a live service activation. Mainnet remains blocked.

## Validation

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/beta_runtime_service_activation_approval_packet.py --output tests/fixtures/beta-runtime-service-activation-approval-packet.json
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_runtime_service_activation_approval_packet.py
```
