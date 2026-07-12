# MCP Adapter Source-Check Report

_Loops 404-428. Anchor issue: #131._

## Scope

This report defines source-check requirements for hypothetical MCP adapter outputs.

It does not authorize or implement MCP server invocation, network access, HTTP calls, shell commands, credentials, messaging, filesystem mutation, or live payment behavior.

## Fixture Contract

MCP adapter output fixtures are deterministic JSON files with:

- `adapter = mcp`
- `serverRef`
- `toolId`
- `toolName`
- `output.title`
- `output.url`
- `output.snippet`

The source gate is the same required gate used by local tool fixtures: `approved-source-output`.

## Positive Fixture

- Fixture: `tests/fixtures/mcp-approved-output.json`
- Source: `Tool Registry Contract v0.1` -> `specs/TOOL-REGISTRY-v0.1.md`
- Expected result: pass

The report must include:

- `mode = deterministic-adapter-output-source-check`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`
- `sourceCheckSummary.status = pass`

## Negative Fixture

- Fixture: `tests/fixtures/mcp-unapproved-output.json`
- Source: `Unreviewed MCP Source` -> `https://example.invalid/mcp-source`
- Expected result: fail

The failure must include builder-facing source-check guidance and `sourceCheckSummary.requiredFailureCount = 1`.

## Decision

MCP adapter output is not trusted because it is MCP-shaped. Future MCP execution must satisfy the same approved-source gate before task completion.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_source_check.py
```

Current expected result:

```text
PASS MCP adapter source checks
```
