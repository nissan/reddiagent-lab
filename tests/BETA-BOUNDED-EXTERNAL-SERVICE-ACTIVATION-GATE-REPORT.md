# Beta Bounded External-Service Activation Gate Report

Issue: #301
Parent epic: #220
Mode: `beta-bounded-external-service-activation-gate`

## Summary

This report records the deterministic local evidence package for the bounded external-service activation gate. The gate consumes merged #299 evidence by pinned path and sha256 from merge `9d6f8d3a2f1a637420808ea60350f578dde0a26f`, verifies #299 consumed #297 by pinned path and sha256, verifies the preserved #295/#293/#291 lineage, and then records a local temporary activation representation that fails closed before real external-service mutation.

## Pinned Inputs

| Artifact | Path | SHA-256 |
|---|---|---|
| #299 fixture | `tests/fixtures/beta-runtime-service-wrapper-operator-run-package.json` | `9e386bed5d3deacc6dc7e75fccae408bcaed62cdb03279c9714d40a52ed6631c` |
| #299 report | `tests/BETA-RUNTIME-SERVICE-WRAPPER-OPERATOR-RUN-PACKAGE-REPORT.md` | `095db81a36cd1c606003c2b9aa7dc3ddc7abe89b8528aec0ea8b9838e8749e73` |

## Evidence Output

Generated fixture: `tests/fixtures/beta-bounded-external-service-activation-gate.json`

The accepted hold scenario records:

- exact run scope: `examples/simple-agent.yaml`, reviewed local command `python scripts/run_local_agent.py examples/simple-agent.yaml`, local ephemeral JSON wrapper, no tool execution, and no network exposure.
- command transcript: `python scripts/beta_bounded_external_service_activation_gate.py --output tests/fixtures/beta-bounded-external-service-activation-gate.json`, exit code `0`, stdout markers for the gate mode and hold verdict.
- trace/eval summary: pinned #299 load, #297 consumption check, #295/#293/#291 lineage check, simple-agent scope confirmation, local temporary activation representation, hold-disable, rollback, and fail-closed boundary.
- service-wrapper state before/after: disabled before, enabled only in local temporary state for the represented activation, disabled after hold, disabled after rollback, and no external process PID at any point.
- activation decision: `hold`, with `liveActionAuthorized: false`.
- rollback/disable verification: dry-run disable and rollback commands, wrapper disabled after rollback, no external process start, and no persistent mutation.
- risk verdict: `hold-fail-closed-before-real-external-service-activation`.
- next-step cue: separate Nissan-approved micro-gate required before any real external service, provider, devnet, or mainnet mutation.

## Fail-Closed Coverage

The fixture includes negative scenarios for stale #299 fixture/report pins, missing current operator approval, wrong ADL/scope, unsafe service-wrapper state, unsafe command transcript, missing trace/eval proof, missing rollback/disable proof, credential-like payloads, live rails requests, and unsafe activation/mainnet completion claims.

## Guardrail Statement

No real external service, host process, Docker, Surfpool, Coolify, hosted deployment, credential access/storage, provider/API product call, live MCP invocation, wallet/payment/facilitator/settlement access, devnet/mainnet run, package/archive publishing, production gateway mutation, external spend, or mainnet action is performed or approved by this gate. Mainnet remains blocked without fresh Nissan approval.
