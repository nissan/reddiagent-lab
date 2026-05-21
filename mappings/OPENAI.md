# OpenAI Target Mapping

_Loop 29. Anchor issue: #31._

## Mapping

- model.capability maps to a selected OpenAI model family.
- model.requirements.toolCalling maps to tool support.
- harness.tools map to Agents SDK tools or Responses API tool definitions.
- harness.evalGates map to guardrails or post-run checks.
- observability maps to OpenAI tracing where available plus ReddiAgent run summary.

## Notes

OpenAI is the likely easiest prosumer entry point, but ReddiAgent should avoid assuming OpenAI-hosted tracing or hosted tools are always present.

## Compatibility Risks

- Hosted tools may not port to other providers.
- Handoffs are useful but should not define the base ADL.
- File/vector-store behavior can become implicit harness state.

