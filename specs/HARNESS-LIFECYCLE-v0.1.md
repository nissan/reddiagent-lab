# Harness Lifecycle v0.1

_Loop 13. Anchor issue: #14._

## Lifecycle

1. Load ADL.
2. Validate schema.
3. Resolve model profile.
4. Resolve secrets by reference.
5. Register tools/functions.
6. Attach data sources and memory.
7. Load policies.
8. Start trace/session.
9. Execute model/tool loop.
10. Run eval gates.
11. Emit receipts/reputation signals if configured.
12. Persist state.
13. Shutdown or await next task.

## Failure Rules

- Missing required secret: fail closed.
- Unsupported runtime feature: fail compatibility check before execution.
- Tool permission denied: return controlled refusal.
- Eval gate failed: mark task incomplete and emit diagnostic.
- Payment receipt missing when required: task cannot be marked complete.

