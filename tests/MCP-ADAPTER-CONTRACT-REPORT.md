# MCP Adapter Contract Report

_Loops 529-553. Anchor issue: #131._

## Scope

This report adds a deterministic static contract check for MCP adapter fixture envelopes and output shape.

The check does not resolve MCP servers, invoke MCP tools, access the network, read credentials, send messages, mutate files outside the test artifacts, or perform live payment behavior.

## Fixtures

| Fixture | Expected | Purpose |
|---|---|---|
| `tests/fixtures/mcp-adapter-contract-approved.json` | pass | Valid MCP fixture envelope with `adapter`, `serverRef`, `toolId`, `toolName`, and source-checkable `output` fields. |
| `tests/fixtures/mcp-adapter-contract-malformed.json` | fail | Negative fixture for empty identity fields, embedded live server URL, access claims, and missing output URL. |

## Guarded Contract

- MCP adapter fixtures must declare `adapter=mcp`.
- MCP adapter fixtures must use non-empty `serverRef`, `toolId`, and `toolName` strings.
- MCP adapter fixtures must not embed `serverUrl`, `command`, `env`, `headers`, or `credentials`.
- MCP adapter fixtures must not claim `networkAccess`, `mcpInvocation`, or `paymentAccess`.
- MCP adapter outputs must include non-empty `title`, `url`, and `snippet` strings so source checks can run deterministically.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_contract.py
```

Expected output:

```text
PASS MCP adapter contract
```

## Boundary

This is adapter-contract validation only. It is not an MCP runtime, server resolver, tool invoker, network client, shell bridge, credential reader, message sender, filesystem mutation path, or payment path.
