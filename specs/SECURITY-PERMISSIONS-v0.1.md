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

