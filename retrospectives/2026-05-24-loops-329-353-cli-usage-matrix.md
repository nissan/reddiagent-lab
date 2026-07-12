# Retrospective: Loops 329-353 - CLI Usage Matrix

Date: 2026-05-24
Anchor issue: #131

## Shipped

- Added `tests/CLI-USAGE-MATRIX.md`.
- Added `tests/test_cli_usage_matrix.py`.
- Wired the CLI usage matrix test into `tests/smoke-validation.sh`.
- Updated runtime and conformance specs with the matrix contract.
- Updated the tool execution fixture report through loops 353.

## Validation

- `python3 tests/test_cli_usage_matrix.py`
- `python3 tests/test_tool_execution.py`
- `python3 scripts/validate_examples.py`
- `python3 tests/test_validation_guidance.py`
- `python3 tests/test_level1.py`
- `python3 tests/test_snapshots.py`
- `bash tests/smoke-validation.sh`
- `python3 -m py_compile scripts/*.py tests/*.py`

## Decision

The local runner now has five distinct, tested CLI outcomes: validation failure, strict runtime denial, report-mode denied tool, report-mode source failure, and required-gate shell failure.

`completion.status` remains the semantic task-completion signal. Process exit is a transport/automation signal.

## Next

Package the local runner evidence into a readiness bundle and explicit rollout gate checklist before any real external tool path, MCP execution, network access, shell execution, or payment behavior is introduced.
