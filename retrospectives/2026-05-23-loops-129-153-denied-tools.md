# Retrospective - Loops 129-153 Denied Tool Sprint

_Date: 2026-05-23_

## Anchor

- Issue: #131 local tool registry execution fixture.

## Objective

Prove ReddiAgent denies unsafe or unsupported local tool fixture calls before any real external tool path exists.

## What Changed

- Added denied fixture result support to `scripts/local_tool_registry.py`.
- Added `--allow-denied-tools` to `scripts/run_local_agent.py`.
- Added `tool.denied` trace events for allowed denial-reporting mode.
- Added unsafe runtime fixtures:
  - `examples/unsafe/undeclared-tool-fixture.yaml`
  - `examples/unsafe/unsupported-tool-fixture.yaml`
- Expanded `tests/test_tool_execution.py` to cover:
  - successful local `search_docs` execution;
  - undeclared tool denial;
  - declared but unsupported tool denial;
  - strict-mode failure on denied tool calls.
- Updated `tests/smoke-validation.sh` to include tool execution checks.
- Updated Tool Registry and Trace Events specs.
- Updated `tests/TOOL-EXECUTION-FIXTURE-REPORT.md`.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_validation_guidance.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_level1.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_snapshots.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_tool_execution.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

Result: all passed.

## Decisions

- Denial reporting is explicit and opt-in via `--allow-denied-tools`.
- Strict mode still fails denied fixture calls with exit code 2.
- Denied fixture results include hashes and error text, but no output payload.
- `tool.denied` is now a Level 1 trace event when fixture denial is allowed for testing.

## Retrospective Findings

- Denial as a structured result is more useful than only raising an exception; it lets conformance tests prove safety boundaries.
- Strict mode still matters because real runners should not silently continue after denied tool intent.
- Unsafe examples belong under `examples/unsafe/`, not `examples/invalid/`, because they are schema-valid but runtime-denied.

## Plan Changes

- Next loop should make denial messages builder-facing, similar to schema validation guidance.
- After that, add a source-check fixture that verifies returned source titles against approved in-repo docs.

## Next Loop Recommendation

Start builder-facing denied-tool guidance:

- render denial reason, why it matters, and a safe repair;
- cover undeclared tool and unsupported local fixture tool separately;
- keep strict mode failure unchanged for CI and runtime safety.
