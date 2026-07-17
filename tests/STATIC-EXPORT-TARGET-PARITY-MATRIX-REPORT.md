# Static Export Target Parity Matrix Report

_Issue: #196. Scope: deterministic static/report-only export target parity fixtures._

## Summary

- Added `scripts/static_export_target_parity.py`, a local-only parity fixture command derived from the Prosumer Builder export matrix.
- Added `tests/fixtures/static-export-target-parity-matrix.json`, pinning simple/tool/payment/invalid ADL parity rows across current static targets.
- Added Vercel eve to the parity matrix as a planned static/report-only target, linked to the 2026-07-17 eve research lane and follow-up issue anchors.
- Added focused test coverage in `tests/test_static_export_target_parity.py`.

## Targets Covered

- Agent Spec
- A2A Agent Card
- Agent Skills / `SKILL.md`
- Starter manifest
- Provider compatibility
- RAP bridge
- Vercel eve

## Vercel eve State

`vercel-eve` is intentionally not marked ready for export or runtime use yet. It is represented as:

- `status=planned-static-report`
- `readiness=planned-static-report`
- `blockedBy=["eve_compatibility_report_not_implemented"]`
- `authoritativeCheck=planned:tests/test_eve_compatibility.py`

Invalid ADL still wins first: the invalid fixture reports `blocked-by-validation` for eve, matching every other target.

## Static Boundary

Every target summary and row preserves:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

## Coverage

- `examples/simple-agent.yaml` pins report-ready, metadata-only, blocked-before-generation, not-applicable, and planned-static-report states.
- `examples/tool-agent.yaml` pins deterministic local tool/source-check parity without network or payment access.
- `examples/payment-agent.yaml` pins x402/receipt/reputation metadata-only handling and RAP-bridge readiness.
- `examples/invalid/missing-instructions.yaml` pins fail-closed validation blocking for every target, including Vercel eve.

## Validation

- `tests/test_static_export_target_parity.py`
- `python3 scripts/static_export_target_parity.py`
- `tests/smoke-validation.sh`

## Non-Goals

- No Vercel eve runtime install or execution.
- No eve project generation.
- No dependency install, dev server, deployment, provider/model call, local model probe, MCP invocation/resolution, credential lookup, wallet/facilitator/payment rail/settlement access, production gateway mutation, package publishing, external service execution, or paid/model call.
