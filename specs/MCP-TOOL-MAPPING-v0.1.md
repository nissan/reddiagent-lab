# MCP Tool Mapping v0.1

_Loop 35. Anchor issue: #37._

## Purpose

MCP is a natural transport for ReddiAgent tools because it separates tool servers from model providers.

## ADL Shape

    tools:
      - id: search_docs
        type: mcp
        description: Search approved documentation
        serverRef: docs-search
        toolName: search

## Rules

- MCP server references must be named, not embedded secrets.
- Runtime must verify the server is available before execution.
- Tool schema should be imported into the compatibility report.
- Permissions still live in harness.policies.

## Compatibility

MCP tools should map well to Anthropic and OpenClaw style harnesses, and can be wrapped for OpenAI/Gemini targets when the runtime owns the MCP client.

