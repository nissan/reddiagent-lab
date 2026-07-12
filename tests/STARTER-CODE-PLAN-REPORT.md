# Starter Code Plan Report

_Issues: #168 and #174. Scope: static/report-only starter code generator plan and dry-run file manifest fixtures._

## Summary

- Added `scripts/starter_code_plan.py`, a deterministic manifest command that maps ADL examples to a starter-code review artifact.
- The command emits planned file paths, target layout metadata, model/tool summaries, validation status, blocked pre-generation gates, and explicit non-goals.
- Added `dryRunFileManifest` fixture summaries plus `tests/fixtures/starter-code-dry-run-file-manifest.json` so the simple/tool/payment dry-run file manifests are losslessly pinned for review.
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
- `tests/fixtures/starter-code-dry-run-file-manifest.json` pins dry-run file path lists, status counts, validation status, blocked gate ids, and non-goal ids for the simple/tool/payment examples.

## Validation

- `tests/test_starter_code_plan.py`
- `python3 scripts/starter_code_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml`
- `python3 scripts/starter_code_plan.py --single examples/invalid/missing-instructions.yaml` returns exit `1`
- `tests/smoke-validation.sh`

## Non-Goals

- No runnable starter project generation.
- No dependency install or framework scaffold.
- No provider/model call, local model probe, MCP invocation/resolution, credential lookup, wallet/facilitator/payment rail/settlement, deployment, or paid/model test call.
