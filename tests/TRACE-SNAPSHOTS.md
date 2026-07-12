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

## tool-agent with local fixture execution

Command:

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/run_local_agent.py examples/tool-agent.yaml --execute-tools

Events:

- session.started
- model.resolved
- tools.registered
- policies.loaded
- evals.loaded
- tool.executed
- source.checked
- task.dry_run_completed

Boundary:

- networkAccess=false
- paymentAccess=false
- sourceCheckSummary.status=pass

## Rule

Snapshots intentionally exclude timestamps so they are deterministic.
