# Tool Execution Fixture Report

_Loops 104-353. Anchor issue: #131._

## Scope

This report covers the first safe local tool execution fixture for ReddiAgent Lab.

It does not authorize or implement:

- network access;
- MCP execution;
- HTTP tool execution;
- shell commands;
- filesystem mutation;
- credentials;
- messaging;
- live x402 payment behavior.

## Fixture

- Example: `examples/tool-agent.yaml`
- Tool: `search_docs`
- Fixture call: `harness.toolFixtures[0]`
- Registry: `scripts/local_tool_registry.py`

## Expected Behavior

Running:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/run_local_agent.py examples/tool-agent.yaml --execute-tools
```

must produce:

- `toolExecution.mode = local-fixture`
- `toolExecution.networkAccess = false`
- `toolExecution.paymentAccess = false`
- one successful `search_docs` result
- a `tool.executed` trace event before `task.dry_run_completed`
- a `source.checked` trace event after `tool.executed`
- one `sourceChecks` result with `status = pass`

Denied fixture cases:

- `examples/unsafe/undeclared-tool-fixture.yaml` references `read_secret`, which is not declared in `harness.tools`.
- `examples/unsafe/unsupported-tool-fixture.yaml` declares `shell_exec`, but the local registry does not implement it.
- `examples/unsafe/unapproved-source-fixture.yaml` declares and successfully executes `unsafe_source_docs`, but its returned title and URL are outside the approved source list.

In strict mode, both are denied with exit code 2. With `--allow-denied-tools`, both return:

- `status = denied`
- `toolExecution.deniedCount = 1`
- `tool.denied` trace event
- no tool output payload
- builder-facing guidance with problem, why it matters, fix, snippet, and reference

Strict denial output is rendered as text:

```text
DENIED examples/unsafe/undeclared-tool-fixture.yaml

1. Tool fixture references undeclared tool: read_secret.
   Tool: read_secret
   Why it matters: ReddiAgent only executes fixture calls that are declared in harness.tools, so a prompt or fixture cannot smuggle in a new capability.
   Fix: Declare the tool in harness.tools if it is a safe local fixture, or remove the fixture call.
```

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_tool_execution.py
```

Current result:

```text
PASS safe local tool execution
```

## Decision

The local runner can now prove one safe fixture-backed tool call and two denial paths with builder-facing guidance. The next loop should add a source-check fixture around approved source titles before any real external tool execution is considered.

## Source Check

Current source-check gate:

- `gateId`: `approved-source-output`
- `toolId`: `search_docs`
- `status`: `pass`
- `title`: `Tool Registry Contract v0.1`
- `url`: `specs/TOOL-REGISTRY-v0.1.md`

Decision: successful local fixture outputs are not considered trusted just because a tool returned them. The runner now checks returned title and URL against the approved in-repo source list.

## Negative Source Check

The unapproved source fixture proves the failing gate path without external retrieval:

- `toolId`: `unsafe_source_docs`
- execution status: `success`
- returned title: `Unapproved External Source`
- returned URL: `https://example.invalid/reddiagent`
- source-check status: `fail`
- source-check message: `Tool output cites a source outside the approved in-repo source list.`

Decision: source checking is independent from local fixture execution success. A future runner must not infer source trust from a successful tool call.

## Source-Check Guidance

Failing source checks now include builder-facing guidance:

- problem: exact unapproved title and URL
- why it matters: execution success is not source trust
- fix: return an approved in-repo source or add a reviewed project-owned source with tests
- snippet: minimal approved source output
- reference: `specs/DATA-SOURCE-CONTRACT-v0.1.md`

Passing source checks remain compact and do not include guidance. Trace events also stay compact; guidance lives in `sourceChecks`, not `source.checked`.

## Completion Semantics

Successful local report generation is not the same as task completion.

Approved source path:

- `completion.transportStatus = pass`
- `completion.requiredGateStatus = pass`
- `completion.status = pass`
- `sourceCheckSummary.requiredFailureCount = 0`
- `task.dry_run_completed.status = pass`

Unapproved source path:

- `completion.transportStatus = pass`
- `completion.requiredGateStatus = fail`
- `completion.status = fail`
- `sourceCheckSummary.requiredFailureCount = 1`
- `task.dry_run_completed.status = fail`

Allowed denied-tool reporting also sets `completion.requiredGateStatus = fail`. The runner can therefore return a JSON report while still making incomplete tasks explicit.

## Required Gate Exit Mode

`--fail-on-required-gate` lets automation turn incomplete required gates into process failure without losing JSON diagnostics.

Expected behavior:

- default allowed-denial/unapproved-source reporting: exit code `0`, JSON has `completion.status = fail`
- with `--fail-on-required-gate`: exit code `3`, JSON still has full diagnostics
- strict denied tools without `--allow-denied-tools`: still exit code `2`

This keeps local development report-first while giving CI a clear incomplete-task signal.

## CLI Usage Matrix

The current CLI contract is documented and tested in `tests/CLI-USAGE-MATRIX.md`.

Covered cases:

- validation guidance exits `1`
- strict denied tools exit `2`
- allowed denied-tool reporting exits `0` with `completion.status = fail`
- source-check failure reporting exits `0` with `completion.status = fail`
- `--fail-on-required-gate` exits `3` while preserving JSON diagnostics

## Readiness Bundle

The local-runner evidence is now packaged in `docs/LOCAL-RUNNER-READINESS-BUNDLE.md`.

That bundle is the gate before any live tool path, MCP execution, network access, shell execution, credential access, messaging, filesystem mutation, or live payment behavior is introduced.

The bundle is checked by `tests/test_readiness_bundle.py` and wired into `tests/smoke-validation.sh`.
