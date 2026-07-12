# Trace Events v0.1

_Loop 45. Anchor issue: #46._

## Level 1 Dry-Run Events

The local dry-run runner emits deterministic trace events:

1. session.started
2. model.resolved
3. tools.registered
4. policies.loaded
5. evals.loaded
6. tool.executed or tool.denied, when `--execute-tools` is enabled and fixtures are present
7. task.dry_run_completed

## Determinism Rule

Trace IDs are deterministic for the same agent name, file name, and dry-run mode. Level 1 tests should not depend on wall-clock timestamps.

## Event Fields

- event
- traceId
- agent or relevant target field
- count/status where relevant
- toolId, inputHash, and outputHash for local fixture tool events

## Tool Fixture Events

_Loop 129-153. Anchor issue: #131._

Tool fixture execution is opt-in and local-only.

- `tool.executed`: emitted for deterministic local fixture success.
- `tool.denied`: emitted for undeclared or unsupported fixture calls when `--allow-denied-tools` is used.
- `source.checked`: emitted after successful local fixture outputs are checked against approved in-repo sources.

Strict mode fails denied fixture calls before producing a dry-run summary.

## Source Guidance Boundary

_Loop 229-253. Anchor issue: #131._

`source.checked` trace events stay compact and record gate identity plus pass/fail status. Builder-facing source repair guidance lives in the `sourceChecks[*].guidance` summary payload, not in the trace event.

## Completion Event Status

_Loop 254-278. Anchor issue: #131._

`task.dry_run_completed` uses `completion.status`, not only transport success:

- `status = pass`: dry-run transport completed and required gates passed.
- `status = fail`: dry-run transport completed but at least one required gate failed.

The reason field explains which case occurred. Detailed source counts live in `sourceCheckSummary`.

## MCP Readiness Evidence Events

_Loops 479-503. Anchor issue: #131._

MCP readiness uses static evidence events before any runtime MCP path exists:

- `mcp.adapter_shape_checked`
- `mcp.adapter_source_checked`
- `mcp.server_resolution_checked`
- `mcp.capability_policy_checked`
- `mcp.readiness_completed`

Every event must report `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`.

`mcp.readiness_completed.status` and `requiredGateStatus` must match the aggregate required-gate result. Missing readiness gate events or live-access claims are required-gate failures.
