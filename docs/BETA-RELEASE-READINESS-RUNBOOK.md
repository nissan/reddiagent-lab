# Beta Release Readiness and Operator Runbook

_Issue: #223._

## Purpose

Executable ReddiAgent prototypes should become beta releases only when their runtime evidence, operator controls, observability, rollback path, and incident boundaries are reviewable.

This runbook applies to local runtime prototypes, provider-backed sandbox prototypes, live MCP handoff prototypes, and devnet payment handoff prototypes. Mainnet deployment, settlement, and runs remain not approved until separate signoff.

## Beta Entry Criteria

A prototype can enter beta only when all entry criteria are true:

| Criterion | Required evidence |
|---|---|
| Smoke validation is green | `tests/smoke-validation.sh` passes on the release candidate. |
| Prototype evidence is current | Local runtime, provider sandbox, and MCP/devnet handoff reports match pinned fixtures. |
| Negative fixtures are green | Unsafe local, provider, MCP, payment, devnet, and mainnet scenarios fail closed. |
| Operator controls are reviewed | Enable, disable, pause, and local-only controls have owners and audit evidence. |
| Mainnet denial is explicit | `mainnetApproved=false` appears in release evidence and mainnet requires separate signoff. |

## Beta Exit Criteria

A beta can exit toward a stronger release only after:

- no unresolved severity-1 or severity-2 incident remains open for the beta observation window;
- an operator stop and rollback drill has been completed from evidence;
- cost ceilings, privacy redaction, retention, and access-review evidence are accepted;
- rollback evidence is current for each enabled runtime path;
- every newly enabled capability has a deterministic negative fixture and smoke coverage.

## Required Release Evidence

- `docs/LOCAL-RUNNER-READINESS-BUNDLE.md`
- `tests/LOCAL-EXECUTABLE-RUNTIME-PROTOTYPE-REPORT.md`
- `tests/PROVIDER-SANDBOX-PROTOTYPE-REPORT.md`
- `tests/LIVE-MCP-DEVNET-HANDOFF-PROTOTYPE-REPORT.md`
- `tests/BETA-RELEASE-READINESS-REPORT.md`
- `tests/fixtures/beta-release-readiness.json`
- `tests/smoke-validation.sh`

## Observability Expectations

Every beta run must emit a trace with:

- `traceId`, `agentId`, `taskId`, `releaseId`, `operatorId`, `runtimeMode`, and `environment`;
- `policyResults`, `evalResults`, `costEstimate`, `privacyRedactions`, and `mainnetAllowed`;
- `rollbackReference` when rollback is started or completed;
- `incidentReference` when an incident is opened or attached.

Required events:

- `session.started`
- `policy.checked`
- `eval.checked`
- `cost.estimated`
- `runtime.enabled`
- `runtime.disabled`
- `rollback.started`
- `rollback.completed`
- `incident.opened`
- `task.completed`
- `task.failed`

Raw secrets must never be logged. Raw prompt logging defaults to redacted evidence, and payment evidence should store reviewed references rather than sensitive payloads.

## Operator Controls

| Control | Use |
|---|---|
| Enable runtime path | Turn on one named beta runtime path after linked readiness evidence passes. |
| Disable runtime path | Turn off one named runtime path immediately while preserving evidence. |
| Pause provider calls | Return provider-backed execution to fake/local sandbox mode. |
| Pause MCP invocation | Deny MCP invocation while keeping static MCP checks available. |
| Pause payment handoff | Deny wallet, facilitator, rail, settlement, and devnet handoff access. |
| Force local-only mode | Keep validation, local fixtures, and reports available while all live paths are off. |

Every control change needs an operator, timestamp, affected release, affected environment, reason, and follow-up owner.

## Rollback and Stop Procedure

1. Disable the named runtime path first.
2. Pause provider, MCP, and payment handoff controls for the affected environment.
3. Preserve trace, cost, privacy, and incident evidence without exposing secrets.
4. Re-run deterministic negative fixtures and smoke validation.
5. Record the operator decision, owner, timestamp, next allowed runtime mode, and reviewer.
6. Re-enable only after a fresh readiness check and review.

Runtime disable should complete within 15 minutes for beta paths. Mainnet rollback is not applicable because mainnet is not approved.

## Cost, Safety, Privacy, and Incidents

- Cost: define per-run and per-window ceilings before live beta use; stop or downgrade to local-only mode when estimates exceed the ceiling.
- Safety: required gates fail closed; unsafe fixtures remain in smoke validation.
- Privacy: redact secrets, raw prompts, raw payment proof, credentials, wallet handles, and sensitive payloads from logs and fixtures.
- Incidents: preserve traces, disable the affected path, attach owner and severity, then require explicit restart approval.

## Machine Check

`scripts/beta_release_readiness.py` validates the pinned beta readiness fixture and exits `3` when required criteria, controls, observability, rollback, incident notes, or mainnet denial are missing.
