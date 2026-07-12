# Retrospective - Loops 154-178 Denial Guidance Sprint

_Date: 2026-05-23_

## Anchor

- Issue: #131 local tool registry execution fixture.

## Objective

Make runtime-denied local tool fixture calls understandable to builders without weakening strict denial behavior.

## What Changed

- Added `scripts/tool_denial_guidance.py`.
- Strict denied tool calls now print builder-facing guidance to stderr and exit with code 2.
- Allowed denial-reporting mode now includes a `guidance` object inside each denied result.
- Added stable path-label handling for relative ADL paths in `scripts/run_local_agent.py`.
- Expanded `tests/test_tool_execution.py` to assert denial guidance contracts.
- Updated `specs/VALIDATION-GUIDANCE-v0.1.md`.
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

Result: all passed after fixing relative path rendering in strict denial output.

## Decisions

- Runtime denial guidance stays separate from JSON Schema validation guidance.
- Strict denied calls still fail; guidance explains the repair but does not continue execution.
- `--allow-denied-tools` remains a conformance/testing mode, not normal runner behavior.

## Retrospective Findings

- Relative ADL paths are part of the builder workflow and must be handled in every error renderer.
- Denial guidance should be contract-tested by fields and key phrases, not brittle full text.
- The next useful safety layer is source-checking successful local tool outputs, not adding more denied cases.

## Plan Changes

- Next loop should add a source-check fixture around `search_docs` output title/url constraints.
- Keep external tool execution blocked until source-check and denied-tool behavior both have reports.

## Next Loop Recommendation

Implement source-check fixture coverage:

- assert `search_docs` returns only approved in-repo docs;
- emit or report source-check status;
- add a failing source-check fixture if the registry output is tampered with or a title is outside the approved list.
