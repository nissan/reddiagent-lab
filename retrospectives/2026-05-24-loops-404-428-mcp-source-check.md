# Retrospective: Loops 404-428 MCP Source Check

## Scope

Define source-check requirements for hypothetical MCP adapter outputs using deterministic fixtures only.

## Changed

- Added `tests/fixtures/mcp-approved-output.json`.
- Added `tests/fixtures/mcp-unapproved-output.json`.
- Added `scripts/mcp_adapter_source_check.py`.
- Added `tests/test_mcp_adapter_source_check.py`.
- Added `tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md`.
- Wired MCP adapter source checks into `tests/smoke-validation.sh`.
- Updated MCP mapping, data-source contract, eval gates, conformance, readiness bundle, roadmap, and index docs.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_source_check.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Decision

MCP-shaped output is not trusted by adapter type. It must pass `approved-source-output` before completion, and unapproved MCP-shaped output is a required-gate failure.

## Next

Define fail-closed MCP server resolution requirements without resolving or invoking an MCP server.
