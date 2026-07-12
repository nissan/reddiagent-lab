# MCP Adapter Error Semantics Report

_Loops 554-578. Anchor issue: #131._

## Scope

This report adds a deterministic static contract for MCP adapter error fixtures before any live MCP server resolution or invocation work.

The check does not resolve MCP servers, invoke MCP tools, access the network, read credentials, send messages, mutate files outside the test artifacts, execute shell commands, or perform live payment behavior.

## Fixtures

| Fixture | Expected | Purpose |
|---|---|---|
| `tests/fixtures/mcp-adapter-error-approved.json` | pass | Bounded timeout-style adapter error: no output payload, explicit retryability, required-gate failure, and no access claims. |
| `tests/fixtures/mcp-adapter-error-leaky.json` | fail | Negative fixture for success-like error status, output payload leakage, live server fields, invocation claims, raw stack leakage, unreviewed error code, and non-boolean retryability. |

## Guarded Contract

- MCP adapter error fixtures must declare `adapter=mcp`.
- MCP adapter error fixtures must use `status=error` or `status=denied`.
- MCP adapter error fixtures must not include output payload data.
- MCP adapter errors must force `completionImpact=required-gate-fail`.
- MCP adapter identity fields must be non-empty `serverRef`, `toolId`, and `toolName` strings.
- MCP adapter error codes must come from the reviewed static allowlist.
- MCP adapter retryability must be explicit.
- MCP adapter error fixtures must not claim `networkAccess`, `mcpInvocation`, or `paymentAccess`.
- MCP adapter error fixtures must not expose raw runtime, server, auth, or environment details.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_error_semantics.py
```

Expected output:

```text
PASS MCP adapter error semantics
```

## Boundary

This is adapter-error validation only. It is not an MCP runtime, server resolver, tool invoker, network client, shell bridge, credential reader, message sender, filesystem mutation path, or payment path.
