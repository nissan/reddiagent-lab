# Security and Permissions v0.1

_Loop 16. Anchor issue: #17._

## Principles

- Secrets are references, never literal values.
- Tools are denied unless explicitly granted.
- Network access is scoped.
- Payments require budget policy.
- External sends/posts require explicit permission.
- Dangerous file, shell, or account operations require separate capabilities.

## Permission Types

| Type | Example |
|---|---|
| tool | use search_docs |
| data | read approved docs collection |
| network | fetch allowlisted domains |
| filesystem | read workspace path |
| payment | spend up to task budget |
| messaging | send to approved channel |
| humanApproval | require approval above threshold |

## Fail-Closed Rules

- Unknown permission type: fail.
- Missing policy for payment: fail.
- Missing secret reference: fail.
- Runtime cannot enforce permission: fail compatibility check.
- MCP declarations with embedded live server URLs, commands, environment variables, headers, tokens, API keys, secrets, or credentials: fail adapter readiness.
- Read-only adapter checks must report `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`.
- MCP server references absent from the reviewed static registry: fail server resolution readiness.
- MCP static registry entries with live URLs, commands, environment variables, headers, tokens, API keys, secrets, or credentials: fail server resolution readiness.
- MCP tools without matching static capability policies: fail capability readiness.
- MCP capability policies that grant network, invocation, payment, or capabilities beyond `mcp.adapter.readonly`: fail capability readiness.
- MCP readiness evidence with missing required gate events, live-access claims, or completion status that does not match required-gate status: fail readiness evidence.
