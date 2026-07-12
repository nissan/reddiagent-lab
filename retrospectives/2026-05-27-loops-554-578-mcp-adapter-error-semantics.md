# Retrospective: Loops 554-578 MCP Adapter Error Semantics

## Summary

Added a static MCP adapter error-semantics contract before any live MCP server resolution or invocation work.

## Changed

- Added `scripts/mcp_adapter_error_semantics_check.py`.
- Added approved and leaky MCP adapter error fixtures under `tests/fixtures/`.
- Added `tests/test_mcp_adapter_error_semantics.py`.
- Added `tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md`.
- Wired the error-semantics test into `tests/smoke-validation.sh`.
- Updated the readiness bundle, MCP release checklist, roadmap, index, and STATUS resume point.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_error_semantics.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_readiness_release.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Decisions

- MCP adapter errors must use `status=error` or `status=denied`.
- MCP adapter errors must not include output payload data.
- MCP adapter errors must force `completionImpact=required-gate-fail`.
- MCP adapter errors must use reviewed static error codes and explicit retryability.
- MCP adapter errors must not expose raw runtime, server, auth, or environment details.
- MCP remains static-review-only. No MCP server resolution, MCP invocation, network access, credential access, messaging, filesystem mutation, shell bridge, or payment path was added.

## Next

Define the next static MCP contract layer, likely runtime handoff packaging or reviewed adapter-result aggregation. Do not resolve or invoke MCP servers yet.
