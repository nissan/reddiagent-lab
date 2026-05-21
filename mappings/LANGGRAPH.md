# LangGraph Target Mapping

_Loop 32. Anchor issue: #34._

## Mapping

- harness.runtime target can compile to a LangGraph graph.
- tools become graph-callable tools.
- memory maps to checkpointing/persistence.
- eval gates map to terminal nodes or post-run checks.
- policies map to conditional edges or pre-tool guards.

## Notes

LangGraph is the best reference for durable execution, state, interruptions, and graph-shaped control. ReddiAgent should learn from this without requiring every agent to be graph-authored.

## Compatibility Risks

- Complex graphs may not round-trip back into simple ADL.
- LangSmith observability should be optional, not required.

