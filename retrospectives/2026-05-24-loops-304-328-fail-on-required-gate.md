# Retrospective: Loops 304-328 - Fail On Required Gate

Date: 2026-05-24
Anchor issue: #131

## Shipped

- Added `--fail-on-required-gate` to `scripts/run_local_agent.py`.
- The flag preserves JSON diagnostics on stdout.
- The flag returns exit code `3` when `completion.status = fail`.
- Default behavior remains report-first and backwards-compatible.
- Extended tool execution tests for unapproved source and allowed denied-tool reporting with shell-level failure.
- Updated runtime, conformance, Level 1, and fixture reports.

## Validation

- `python3 tests/test_tool_execution.py`

Full suite was run after STATUS and memory updates for this batch.

## Decision

Shell-level failure should be opt-in. Builders get readable JSON by default; automation can request a failing process when required gates fail.

## Next

Add a small CLI usage matrix covering validation errors, strict denied tools, allowed denied tools, source-check failures, and required-gate shell failure.
