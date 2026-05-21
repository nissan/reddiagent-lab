# Trace Events v0.1

_Loop 45. Anchor issue: #46._

## Level 1 Dry-Run Events

The local dry-run runner emits deterministic trace events:

1. session.started
2. model.resolved
3. tools.registered
4. policies.loaded
5. evals.loaded
6. task.dry_run_completed

## Determinism Rule

Trace IDs are deterministic for the same agent name, file name, and dry-run mode. Level 1 tests should not depend on wall-clock timestamps.

## Event Fields

- event
- traceId
- agent or relevant target field
- count/status where relevant

