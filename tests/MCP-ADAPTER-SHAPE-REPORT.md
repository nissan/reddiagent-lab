# MCP Adapter Shape Report

_Loops 379-403. Anchor issue: #131._

## Scope

This report covers read-only MCP adapter shape checks.

It does not authorize or implement MCP server invocation, network access, HTTP calls, shell commands, credentials, messaging, filesystem mutation, or live payment behavior.

## Positive Fixture

- Example: `examples/mcp-readonly-agent.yaml`
- Tool: `docs_search`
- Type: `mcp`
- Required shape: named `serverRef` plus `toolName`
- Result: pass

Expected report:

- `mode = read-only-adapter-shape`
- `adapter = mcp`
- `status = pass`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`

## Negative Fixture

- Example: `examples/unsafe/mcp-live-server-fixture.yaml`
- Tool: `live_docs_search`
- Type: `mcp`
- Unsafe fields: `serverUrl`, `command`, `env`
- Result: fail

Decision: ADL adapter compatibility may inspect MCP declarations, but local readiness checks must reject embedded live server, command, environment, credential, token, header, or URL fields. MCP tools should point at named `serverRef` values only until a reviewed runtime owns server resolution.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_adapter_readiness.py
```

Current expected result:

```text
PASS adapter readiness
```
