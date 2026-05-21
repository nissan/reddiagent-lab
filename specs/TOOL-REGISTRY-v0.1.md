# Tool Registry Contract v0.1

_Loop 26. Anchor issue: #28._

## Purpose

Tools are the main way the harness changes the world. The registry must make them typed, permissioned, observable, and replaceable.

## Tool Fields

- id
- type: function, mcp, http, native
- description
- inputSchema
- outputSchema
- permissions
- timeout
- retryPolicy
- sideEffects
- auditLevel

## Registration Rules

- Tool IDs must be unique inside a harness.
- Tools must have descriptions.
- Risky tools require an explicit policy.
- Tools that mutate external state must declare sideEffects.
- Runtime adapters must report unsupported tool types before execution.

## Invocation Result

Every tool call should return:

- toolId
- status: success, failure, denied, timeout
- inputHash
- outputHash
- startedAt
- finishedAt
- error
- traceRef

