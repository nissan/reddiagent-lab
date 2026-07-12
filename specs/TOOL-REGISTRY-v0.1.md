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

## Safe Local Fixture Execution

_Loop 104-128. Anchor issue: #131._

Before ReddiAgent supports real external tools, the local runner may execute only deterministic local fixtures.

Rules:

- Fixture execution is opt-in with `--execute-tools`.
- Fixture calls must reference tools declared in `harness.tools`.
- Fixture tools must be implemented in the project-owned local registry.
- Fixture tools must not use network access, filesystem mutation, shell commands, payments, credentials, or messaging.
- Fixture results must include `toolId`, `status`, `inputHash`, `outputHash`, and `output`.
- Denied fixture results must include `toolId`, `status=denied`, `inputHash`, `outputHash`, and `error`, and must not include tool output.
- Dry-run traces must emit `tool.executed` or `tool.denied` before `task.dry_run_completed`.
- Strict execution fails on denied tools. `--allow-denied-tools` reports denied results for fixture testing only.

Current fixture registry:

- `search_docs`: searches a tiny approved in-repo documentation list and returns one source record.

Denied fixture coverage:

- undeclared fixture tool IDs are denied before registry dispatch.
- declared but unsupported fixture tool IDs are denied by the local registry.
