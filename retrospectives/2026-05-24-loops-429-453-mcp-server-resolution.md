# Retrospective: Loops 429-453 MCP Server Resolution

## Scope

Define fail-closed MCP server resolution requirements using static config fixtures only.

## Changed

- Added `tests/fixtures/mcp-server-registry-approved.json`.
- Added `tests/fixtures/mcp-server-registry-empty.json`.
- Added `tests/fixtures/mcp-server-registry-live.json`.
- Added `scripts/mcp_server_resolution_check.py`.
- Added `tests/test_mcp_server_resolution.py`.
- Added `tests/MCP-SERVER-RESOLUTION-REPORT.md`.
- Wired MCP server resolution checks into `tests/smoke-validation.sh`.
- Updated MCP mapping, security, conformance, readiness bundle, roadmap, and index docs.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_server_resolution.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Decision

MCP server resolution must fail closed before invocation. A named ADL `serverRef` must exist in a static reviewed registry that keeps `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`; missing refs and live resolution fields fail readiness.

## Next

Define capability-policy checks for MCP tools and server refs using deterministic fixtures only. Do not resolve or invoke MCP servers yet.
