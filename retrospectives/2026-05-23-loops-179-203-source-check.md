# Retrospective - Loops 179-203 Source-Check Sprint

_Date: 2026-05-23_

## Anchor

- Issue: #131 local tool registry execution fixture.

## Objective

Prove successful local tool fixture outputs cite only approved in-repo sources before any real external retrieval path exists.

## What Changed

- Added approved source title/URL sets to `scripts/local_tool_registry.py`.
- Added `scripts/source_check.py`.
- Added `sourceChecks` summary output to `scripts/run_local_agent.py`.
- Added `source.checked` trace events after successful fixture execution.
- Expanded `tests/test_tool_execution.py` to assert source-check pass output.
- Updated `specs/EVAL-GATES-v0.1.md`.
- Updated `specs/DATA-SOURCE-CONTRACT-v0.1.md`.
- Updated `specs/TRACE-EVENTS-v0.1.md`.
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

- A successful local tool fixture output still requires a source-check result.
- Source-check pass requires both title and URL to match the approved in-repo source list.
- `source.checked` is now part of the opt-in tool fixture trace path.
- No external search, network, MCP, HTTP, credential, shell, or payment path was added.

## Retrospective Findings

- Source checks should live beside eval gates, not inside the tool implementation, so future tools can share the same gate pattern.
- The current approved source list is intentionally tiny; expanding it should be explicit and reviewed.
- The next missing safety proof is a failing source-check fixture, proving unapproved successful outputs are caught.

## Plan Changes

- Next loop should add a tampered/unapproved source fixture or test seam that proves `sourceChecks.status=fail`.
- After that, source-check guidance can mirror denied-tool guidance.

## Next Loop Recommendation

Implement negative source-check coverage:

- simulate a successful local tool result with an unapproved title/url;
- assert `source.checked` reports `fail`;
- keep normal `search_docs` fixture passing.
