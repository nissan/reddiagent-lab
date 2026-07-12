# Retrospective: Loops 379-403 MCP Adapter Shape

## Scope

Add the first post-readiness capability shape without introducing live behavior: read-only MCP adapter readiness plus a deterministic negative fixture.

## Changed

- Added `examples/mcp-readonly-agent.yaml`.
- Added `examples/unsafe/mcp-live-server-fixture.yaml`.
- Added `scripts/adapter_readiness.py`.
- Added `tests/test_adapter_readiness.py`.
- Added `tests/MCP-ADAPTER-SHAPE-REPORT.md`.
- Wired adapter readiness into `tests/smoke-validation.sh`.
- Updated MCP, adapter, security, conformance, readiness, roadmap, and index docs.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_adapter_readiness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py examples/mcp-readonly-agent.yaml
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Decision

MCP starts as an adapter shape, not an executable tool path. ADL may name `serverRef` and `toolName`, but embedded live fields such as `serverUrl`, `command`, and `env` fail readiness before any server resolution can occur.

## Next

Define source-check requirements for hypothetical MCP adapter outputs using deterministic fixtures only. Do not resolve or invoke MCP servers yet.
