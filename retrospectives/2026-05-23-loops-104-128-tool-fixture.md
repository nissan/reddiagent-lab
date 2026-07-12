# Retrospective - Loops 104-128 Tool Fixture Sprint

_Date: 2026-05-23_

## Anchor

- Issue: #131 local tool registry execution fixture.

## Objective

Build the first safe local tool execution path for ReddiAgent without adding external network tools, MCP execution, shell commands, live payments, credentials, messaging, or workflow side effects.

## What Changed

- Added `scripts/local_tool_registry.py` with a deterministic `search_docs` fixture over approved in-repo docs.
- Added `--execute-tools` to `scripts/run_local_agent.py`.
- Added `harness.toolFixtures` to `examples/tool-agent.yaml`.
- Added `tests/test_tool_execution.py`.
- Added `tests/TOOL-EXECUTION-FIXTURE-REPORT.md`.
- Updated `specs/TOOL-REGISTRY-v0.1.md` with safe local fixture execution rules.

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

- Fixture execution stays opt-in through `--execute-tools`.
- Existing Level 1 dry-run snapshots stay unchanged unless tool execution is explicitly enabled.
- Fixture calls must reference declared ADL tools.
- Local fixture execution returns hashes and emits `tool.executed` trace events.
- Network, payment, credential, shell, and messaging paths remain blocked.

## Retrospective Findings

- The runner needed a second mode rather than changing default dry-run behavior; keeping defaults stable avoided breaking existing snapshots.
- `harness.toolFixtures` is useful as a test-only execution lane while the core ADL tool contract stays stable.
- The next risk is denial behavior: ReddiAgent should prove unsafe or undeclared tool calls are rejected clearly before broadening fixture types.

## Plan Changes

- Next loop should start a source-check/denied-tool fixture sprint.
- A later loop can add candidate provider adapter execution only after denied-tool and source-check behavior are covered.

## Next Loop Recommendation

Open or continue the next implementation issue for a denied local tool fixture and source-check fixture:

- undeclared tool ID should fail with a builder-readable denial;
- fixture result should include `status=denied` once denial reporting is formalized;
- tests should prove no network, payment, shell, or credential path is reachable.
