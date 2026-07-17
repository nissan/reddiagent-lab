# ADR 0004: MCP and Payment Boundaries Fail Closed

## Status

Accepted.

## Context

MCP tools, live provider calls, wallets, facilitator access, payment rails, settlement, credentials, devnet, mainnet, and deployment actions can cross privacy, cost, security, or irreversibility boundaries. The current ReddiAgent repo therefore models those surfaces through declarations, dry-run receipts, handoff packages, and static reports before any live action.

Relevant references:

- `docs/REDDIAGENT-ARCHITECTURE.md`
- `docs/PAYMENT-SAFETY.md`
- `specs/MCP-TOOL-MAPPING-v0.1.md`
- `specs/MCP-RUNTIME-HANDOFF-PACKAGE.schema.json`
- `specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md`
- `specs/X402-DRY-RUN-RECEIPT-v0.1.md`
- `specs/RUNTIME-DEPLOYMENT-v0.1.md`
- `tests/MCP-CAPABILITY-POLICY-REPORT.md`
- `tests/PAYMENT-DRY-RUN-RECEIPT-REPORT.md`

## Decision

MCP, tool, payment, wallet, settlement, provider, credential, and deployment boundaries fail closed by default.

An artifact that cannot prove a live action is bounded, approved, and auditable must remain static/report-only. Mainnet deployment and mainnet runs require fresh explicit approval.

## Consequences

- Static reports should reject or warn on live URLs, unbounded actions, missing authority, raw secret leakage, unsafe payment configuration, or ambiguous runtime behavior.
- Live capability use must be issue-scoped, least-privilege, validated, and recorded in project status and memory.
- Docs and fixtures should keep safety vocabulary visible to prevent readers from mistaking review artifacts for execution approval.
- Future live lanes must add evidence that distinguishes dry-run review from actual external action.
