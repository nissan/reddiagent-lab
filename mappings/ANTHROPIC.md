# Anthropic Target Mapping

_Loop 30. Anchor issue: #32._

## Mapping

- model.capability maps to Claude model selection.
- harness.tools map to Claude tool-use schemas.
- mcp tools map naturally to Anthropic's MCP-oriented workflows.
- policies should enforce tool permission and human approval outside the model call.

## Notes

Anthropic is a strong reference for explicit tool use and safety boundaries. ReddiAgent should treat MCP as a first-class tool transport option.

## Compatibility Risks

- Full session/runtime behavior must be provided by the ReddiAgent harness or another framework.
- Computer-use style tools need high-friction permissions and audit logs.

