# Anthropic Target Mapping

_Loop 30. Anchor issue: #32._

## Mapping

- model.capability maps to Claude model selection.
- harness.tools map to Claude tool-use schemas.
- mcp tools map to MCP declaration metadata for compatibility review: `id`, `serverRef`, and `toolName`.
- policies should enforce tool permission and human approval outside the model call.
- source, receipt, reputation, memory, and payment semantics are preserved as Reddi metadata until
  a reviewed runtime adapter enforces them.

## Notes

Anthropic is a strong reference for explicit tool use and safety boundaries. ReddiAgent should treat MCP as a first-class tool transport option.
The current compatibility mode is report-only and does not call Anthropic, resolve MCP servers, or invoke MCP tools.

## Compatibility Risks

- Full session/runtime behavior must be provided by the ReddiAgent harness or another framework.
- Computer-use style tools need high-friction permissions and audit logs.
- MCP execution is hard unsupported until server resolution, source checks, and capability policy
  enforcement have a separate runtime approval gate.
