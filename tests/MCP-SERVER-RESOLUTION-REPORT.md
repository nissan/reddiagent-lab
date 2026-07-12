# MCP Server Resolution Report

_Loops 429-453. Anchor issue: #131._

## Scope

This report defines fail-closed requirements for MCP server resolution using static config fixtures only.

It does not authorize or implement MCP server invocation, network access, HTTP calls, shell commands, credentials, messaging, filesystem mutation, or live payment behavior.

## Static Registry Contract

Reviewed MCP server references must be declared in a static registry with:

- `id`
- `resolutionMode = static-reviewed`
- `allowedTools`
- `sourceGate = approved-source-output`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`

Live resolution fields are not allowed in this registry:

- `url`
- `serverUrl`
- `command`
- `args`
- `env`
- `headers`
- `token`
- `apiKey`
- `secret`
- `credential`

## Fixtures

Positive fixture:

- `tests/fixtures/mcp-server-registry-approved.json`
- result: pass

Negative fixtures:

- `tests/fixtures/mcp-server-registry-empty.json`
- result: fail because `serverRef` is missing from the static registry

- `tests/fixtures/mcp-server-registry-live.json`
- result: fail because the registry embeds live resolution fields and is not `static-reviewed`

## Decision

MCP server resolution must fail closed before any runtime can invoke a server. A named `serverRef` in ADL is necessary but not sufficient; it must also appear in a reviewed static registry that keeps network and invocation disabled for readiness checks.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_server_resolution.py
```

Current expected result:

```text
PASS MCP server resolution
```
