# MCP Adapter Aggregation Report

_Loops 579-603. Anchor issue: #131._

## Scope

This report adds a deterministic static contract for MCP adapter result packages before any runtime handoff, live MCP server resolution, or invocation work.

The check does not resolve MCP servers, invoke MCP tools, access the network, read credentials, send messages, mutate files outside the test artifacts, execute shell commands, or perform live payment behavior.

## Fixtures

| Fixture | Expected | Purpose |
|---|---|---|
| `tests/fixtures/mcp-adapter-aggregation-approved.json` | pass | Static reviewed package with one source-checkable pass result, one bounded error result, and fail-closed aggregate completion. |
| `tests/fixtures/mcp-adapter-aggregation-leaky.json` | fail | Negative fixture for live aggregation mode, access claims, duplicated IDs, payload/error mixing, raw runtime leakage, and mismatched aggregate completion. |

## Guarded Contract

- MCP adapter aggregation packages must declare `adapter=mcp`.
- MCP adapter aggregation packages must use `aggregationMode=static-reviewed`.
- Aggregated results must use unique non-empty `resultId` values.
- Aggregated result identity fields must include non-empty `serverRef`, `toolId`, and `toolName`.
- Passing results must include source-checkable `output.title`, `output.url`, and `output.snippet` strings.
- Passing results must not include error objects.
- Failed results must not include output payload data.
- Failed results must use reviewed static error codes and explicit retryability.
- Aggregate completion counts and required-gate status must match result statuses.
- Packages, results, and completion objects must not claim `networkAccess`, `mcpInvocation`, or `paymentAccess`.
- Packages must not expose raw runtime, server, auth, or environment details.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_aggregation.py
```

Expected output:

```text
PASS MCP adapter aggregation
```

## Boundary

This is static adapter-result aggregation only. It is not an MCP runtime, server resolver, tool invoker, network client, shell bridge, credential reader, message sender, filesystem mutation path, or payment path.
