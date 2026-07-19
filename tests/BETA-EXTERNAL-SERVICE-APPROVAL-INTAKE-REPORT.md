# Beta External-Service Approval Intake Report

Issue: #305
Parent epic: #220
Mode: `beta-external-service-approval-intake`

## Summary

This report records the deterministic local approval-intake package for the ReddiAgent external-service activation scope. The package consumes merged #303 evidence by pinned path and sha256 from merge `d0e7b7968ef9c9e7086cbb1a9dfef5a104be6a24`, verifies #303 consumed #301 by pinned path and sha256, verifies the preserved #299/#297/#295/#293/#291 lineage, and emits explicit approve-or-hold evidence without performing any real mutation.

## Pinned Inputs

| Artifact | Path | SHA-256 |
|---|---|---|
| #303 fixture | `tests/fixtures/beta-external-service-activation-micro-gate.json` | `b8bb3f00c0d1b723513e13a556f61c4b59c916736e08df3dea1f2c1014146d8d` |
| #303 report | `tests/BETA-EXTERNAL-SERVICE-ACTIVATION-MICRO-GATE-REPORT.md` | `ff96d3c6c0a8177625e4e44b2e027ca2135bbe57ab4155a0ccb22d545d7082aa` |

## Evidence Output

Generated fixture: `tests/fixtures/beta-external-service-approval-intake.json`

The accepted current-intake scenario records:

- exact approval prompt: `Approve exactly this local/free bounded external-service activation scope for examples/simple-agent.yaml, with no provider/devnet/mainnet escalation?`
- Nissan response fields: status, approver, response text, timestamp, source, freshness, prompt echo, scope, and provider/production/devnet/mainnet/cost/privacy/legal escalation flags.
- current response state: absent, with no timestamp or source, producing `hold-fail-closed`. No passing synthetic approval is included.
- approval behavior: this deterministic package cannot self-certify approval; any constructed `approved` response fails closed until a future task captures fresh external Nissan approval.
- bounded scope echo: #303 source issue, `examples/simple-agent.yaml`, local/free/bounded approval only, no provider/devnet/mainnet escalation, and estimated cost `0.00`.
- precondition echo: pinned #303 evidence present and hash-matched, #301 consumed, lineage preserved, mainnet blocked, and no real mutation.
- risk verdict: `hold-fail-closed-without-fresh-nissan-approval`.
- approve-or-hold decision: hold, live action unauthorized, and stop before mutation.

## Fail-Closed Coverage

The fixture includes negative scenarios for stale #303 evidence, ambiguous responses, stale approvals, broader-than-#303 scope, provider/production escalation, devnet/mainnet escalation, cost/privacy/legal escalation, wrong approval prompts, unsafe boundary flags, credential-like payloads, and unsafe local command substitutions.

## Guardrail Statement

No real external service, host process, Docker, Surfpool, Coolify, hosted deployment, credential access/storage, provider/API product call, live MCP invocation, wallet/payment/facilitator/settlement access, devnet/mainnet run, package/archive publishing, production gateway mutation, external spend, or mainnet action is performed or approved by this approval-intake package. Mainnet remains blocked without fresh Nissan approval.
