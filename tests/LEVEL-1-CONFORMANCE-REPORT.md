# Level 1 Conformance Report

_Loops 44, 46, 47. Issues: #44, #47, #48._

_Fixture gate completion section added in loops 279-303. Issue: #131._

_Required gate shell-failure mode added in loops 304-328. Issue: #131._

## Commands

    /Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py
    /Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_level1.py

## Expected Result

    PASS examples/simple-agent.yaml
    PASS examples/tool-agent.yaml
    PASS examples/payment-agent.yaml
    PASS Level 1 simple-agent.yaml
    PASS Level 1 tool-agent.yaml
    PASS Level 1 fixture gate completion

## Interpretation

simple-agent and tool-agent satisfy Level 1 local dry-run conformance. payment-agent remains Level 0 plus payment dry-run only.

## Local Fixture Gate Completion

The Level 1 runner now reports local fixture gate completion separately from transport success.

Approved source fixture:

- command: `scripts/run_local_agent.py examples/tool-agent.yaml --execute-tools`
- `completion.transportStatus = pass`
- `completion.requiredGateStatus = pass`
- `sourceCheckSummary.requiredFailureCount = 0`
- `task.dry_run_completed.status = pass`

Unapproved source fixture:

- command: `scripts/run_local_agent.py examples/unsafe/unapproved-source-fixture.yaml --execute-tools --allow-denied-tools`
- `completion.transportStatus = pass`
- `completion.requiredGateStatus = fail`
- `sourceCheckSummary.requiredFailureCount = 1`
- `task.dry_run_completed.status = fail`

Denied tool reporting fixture:

- command: `scripts/run_local_agent.py examples/unsafe/undeclared-tool-fixture.yaml --execute-tools --allow-denied-tools`
- `completion.transportStatus = pass`
- `completion.requiredGateStatus = fail`
- `toolExecution.deniedCount = 1`

Interpretation: a local runner can produce a deterministic JSON report while still marking the task incomplete when required tool/source gates fail.

## Required Gate Shell Failure

Automation can opt into shell-level failure with `--fail-on-required-gate`.

Unapproved source fixture:

- command: `scripts/run_local_agent.py examples/unsafe/unapproved-source-fixture.yaml --execute-tools --allow-denied-tools --fail-on-required-gate`
- expected exit code: `3`
- stdout: same JSON report, with `completion.requiredGateStatus = fail`

Denied tool reporting fixture:

- command: `scripts/run_local_agent.py examples/unsafe/undeclared-tool-fixture.yaml --execute-tools --allow-denied-tools --fail-on-required-gate`
- expected exit code: `3`
- stdout: same JSON report, with `toolExecution.deniedCount = 1`

Default behavior remains report-first: without `--fail-on-required-gate`, these allowed reporting paths return exit code `0` while marking `completion.status = fail` in JSON.
