# Beta External-Service Activation Micro-Gate Report

Issue: #303
Parent epic: #220
Mode: `beta-external-service-activation-micro-gate`

## Summary

This report records the deterministic local approval micro-gate package for the next ReddiAgent external-service activation step. The package consumes merged #301 evidence by pinned path and sha256 from merge `290af941f49bdfc219b14c0f805b25f8b553954e`, verifies #301 consumed #299 by pinned path and sha256, verifies the preserved #297/#295/#293/#291 lineage, and emits an explicit Nissan ask/hold decision before any real mutation.

## Pinned Inputs

| Artifact | Path | SHA-256 |
|---|---|---|
| #301 fixture | `tests/fixtures/beta-bounded-external-service-activation-gate.json` | `695ecd9c1ea08c939cfd9b49cac7699c6cfb7704175da4f85555ff5858e87856` |
| #301 report | `tests/BETA-BOUNDED-EXTERNAL-SERVICE-ACTIVATION-GATE-REPORT.md` | `cf19f0f1464100ee607ee5d19b4618ecdee716da492a187f06a48c31ea46499c` |

## Evidence Output

Generated fixture: `tests/fixtures/beta-external-service-activation-micro-gate.json`

The accepted ask/hold scenario records:

- proposed run scope: `examples/simple-agent.yaml`, reviewed local command `python scripts/run_local_agent.py examples/simple-agent.yaml`, local ephemeral JSON wrapper, no tool execution, no network exposure, and estimated cost `0.00`.
- preconditions: pinned #301 evidence present and hash-matched, lineage preserved, mainnet blocked, credentials not required, and no external service running.
- Nissan approval fields: approval required, status pending, not approved, no approver, no approval timestamp, and the exact approval prompt.
- command transcript template: `python scripts/beta_external_service_activation_micro_gate.py --output tests/fixtures/beta-external-service-activation-micro-gate.json`, expected exit code `0`, and stdout markers for the mode and ask/hold verdict.
- trace/eval requirements: local pass, no tool execution, lineage verification, credential-payload rejection, and mainnet rejection.
- service-wrapper before/after expectations: disabled before, disabled after, no external process PID, and no persistent mutation.
- rollback/disable plan: dry-run disable and rollback commands, no real service stop requirement, and verified no persistence.
- risk verdict: `hold-fail-closed-until-nissan-approval`.
- decision: `ask-nissan-and-hold`, with `liveActionAuthorized: false`.

## Fail-Closed Coverage

The fixture includes negative scenarios for stale #301 evidence, missing or prematurely approved Nissan approval fields, broad run scope, unsafe commands, missing trace/eval requirements, unsafe wrapper expectations, missing rollback/disable proof, credential-like payloads, live rails requests, and unsafe activation decisions.

## Guardrail Statement

No real external service, host process, Docker, Surfpool, Coolify, hosted deployment, credential access/storage, provider/API product call, live MCP invocation, wallet/payment/facilitator/settlement access, devnet/mainnet run, package/archive publishing, production gateway mutation, external spend, or mainnet action is performed or approved by this micro-gate. Mainnet remains blocked without fresh Nissan approval.
