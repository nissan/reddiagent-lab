# Evaluation Gates v0.1

_Loop 14. Anchor issue: #15._

## Purpose

Eval gates decide whether the harness can mark work complete.

## Gate Types

| Type | Purpose | Example |
|---|---|---|
| output-check | Validate response shape or content | Must include answer and uncertainty note |
| source-check | Validate citations or source use | Must cite approved source |
| tool-check | Validate tool behavior | Tool call stayed within allowed domain |
| budget-check | Validate spend | Spend <= 0.25 USDC |
| receipt-check | Validate economic/evidence metadata | Receipt exists and hashes match |
| human-review | Require human approval | Approval required above threshold |

## Gate Result

Each gate returns:

- id
- status: pass, fail, warn, skipped
- evidence
- message
- retryable

## Completion Rule

Required gates must pass before task completion. Warning gates can complete but should be visible in traces and receipts.

## ADL v0.2 Completion Contract

_Anchor issue: #313._

ADL v0.2 makes the completion rule machine-checkable. Each eval gate declares
whether it is `required`, its `severity`, the scoped `appliesTo` target, an
`evidence` reference plus schema, `retryable`, and `onFailure` completion
behavior.

Required gates are fail-closed:

- `required: true`
- `severity: error` or `critical`
- `onFailure.completion: block`
- `onFailure.defaultStatus: fail`

Warning gates are visible but non-blocking:

- `required: false`
- `severity: info` or `warning`
- `onFailure.completion: warn`

If required gate evidence is missing, does not match the gate's declared
evidence reference, or the gate result is not `pass`,
`completion.requiredGateStatus` and `completion.status` must be `fail` even
when `completion.transportStatus` is `pass`. A warning gate result of `warn`,
`fail`, mismatched evidence, or missing evidence remains trace/receipt evidence
but does not block task completion.

## Local Source-Check Fixture

_Loop 179-203. Anchor issue: #131._

The local runner can attach source-check results to successful fixture tool outputs.

Current gate:

- id: `approved-source-output`
- type: `source-check`
- applies to: successful local fixture tool outputs with `title` and `url`
- pass condition: `title` and `url` are in the project-owned approved in-repo source list
- trace event: `source.checked`

This gate is local-only. It does not call external search, network APIs, MCP servers, or live retrievers.

## Negative Source-Check Fixture

_Loop 204-228. Anchor issue: #131._

`examples/unsafe/unapproved-source-fixture.yaml` proves that a successful local fixture tool result does not automatically satisfy source policy. The fixture calls `unsafe_source_docs`, which is deterministic and local-only, but returns a title and URL outside the approved source list.

Expected result:

- tool execution: `status = success`
- source gate: `status = fail`
- trace event: `source.checked`
- failure message: `Tool output cites a source outside the approved in-repo source list.`

## Source-Check Failure Guidance

_Loop 229-253. Anchor issue: #131._

Failing source-check results include builder-facing `guidance` with:

- `problem`: the unapproved title and URL returned by the fixture
- `why_it_matters`: why successful tool execution is not equivalent to source trust
- `fix`: return an approved in-repo source or add a reviewed project-owned source
- `snippet`: a minimal approved output shape
- `reference`: `specs/DATA-SOURCE-CONTRACT-v0.1.md`

Passing source checks do not include guidance.

## Completion Semantics

_Loop 254-278. Anchor issue: #131._

The local runner separates dry-run transport success from required gate completion.

Summary fields:

- `completion.transportStatus`: whether the runner completed validation/execution/reporting
- `completion.requiredGateStatus`: whether required tool/source gates passed
- `completion.status`: the task completion status, currently equal to `requiredGateStatus`
- `sourceCheckSummary.requiredFailureCount`: number of failed required source checks

Examples:

- Approved `search_docs` output: `transportStatus = pass`, `requiredGateStatus = pass`, `sourceCheckSummary.requiredFailureCount = 0`.
- Unapproved `unsafe_source_docs` output: `transportStatus = pass`, `requiredGateStatus = fail`, `sourceCheckSummary.requiredFailureCount = 1`.

This lets the harness produce a useful JSON report while still marking the task incomplete when required gates fail.

## MCP Adapter Source Gate

_Loops 404-428. Anchor issue: #131._

The `approved-source-output` gate also applies to hypothetical MCP adapter output fixtures.

Expected report fields:

- `mode = deterministic-adapter-output-source-check`
- `adapter = mcp`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`
- `sourceCheckSummary.status = pass|fail`

Failing MCP-shaped outputs are required-gate failures, not warnings.
