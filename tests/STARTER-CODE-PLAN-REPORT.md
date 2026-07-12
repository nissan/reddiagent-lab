# Starter Code Plan Report

_Issue: #168. Scope: static/report-only starter code generator plan._

## Summary

- Added `scripts/starter_code_plan.py`, a deterministic manifest command that maps ADL examples to a starter-code review artifact.
- The command emits planned file paths, target layout metadata, model/tool summaries, validation status, blocked pre-generation gates, and explicit non-goals.
- The manifest is intentionally not a generator: it does not write files, install dependencies, run providers, resolve MCP servers, activate runtimes, or touch payment rails.

## Static Boundary

Every manifest preserves:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `writesFiles=false`
- `installsDependencies=false`

## Coverage

- `examples/simple-agent.yaml` proves a minimal local Python starter manifest can be reviewed without tools or payments.
- `examples/tool-agent.yaml` proves deterministic local tool fixtures are represented as review-only fixture files.
- `examples/payment-agent.yaml` proves non-local runtime and x402/payment semantics are blocked behind explicit review gates.
- `examples/invalid/missing-instructions.yaml` proves invalid ADL fails closed and produces no planned starter files.

## Validation

- `tests/test_starter_code_plan.py`
- `python3 scripts/starter_code_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml`
- `python3 scripts/starter_code_plan.py --single examples/invalid/missing-instructions.yaml` returns exit `1`
- `tests/smoke-validation.sh`

## Non-Goals

- No runnable starter project generation.
- No dependency install or framework scaffold.
- No provider/model call, local model probe, MCP invocation/resolution, credential lookup, wallet/facilitator/payment rail/settlement, deployment, or paid/model test call.
