# Trace Snapshots

_Loop 58. Anchor issue: #59._

## simple-agent

Events:

- session.started
- model.resolved
- tools.registered
- policies.loaded
- evals.loaded
- task.dry_run_completed

## tool-agent

Events:

- session.started
- model.resolved
- tools.registered
- policies.loaded
- evals.loaded
- task.dry_run_completed

## Rule

Snapshots intentionally exclude timestamps so they are deterministic.

