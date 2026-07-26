# ReddiAgent ADR Register

_Issue #207. Parent epic: #206._

This register records architectural decisions that shape ReddiAgent Lab. Each decision record uses the same shape:

- **Status**: proposed, accepted, superseded, or deprecated.
- **Context**: the pressure or prior work behind the decision.
- **Decision**: the direction ReddiAgent will follow.
- **Consequences**: what the decision enables, constrains, or requires next.

## Current Decisions

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-adl-is-the-canonical-source-of-truth.md) | Accepted | ADL is the canonical ReddiAgent definition. |
| [0002](0002-static-compatibility-before-runtime-execution.md) | Accepted | Compatibility targets start as static/report-only reviews before runtime execution. |
| [0003](0003-harness-is-a-first-class-product-surface.md) | Accepted | The harness is a first-class product and review surface. |
| [0004](0004-mcp-and-payment-boundaries-fail-closed.md) | Accepted | MCP, tool, payment, and settlement boundaries fail closed by default. |
| [0005](0005-receipts-and-reputation-layer-above-payment-evidence.md) | Accepted | Reddi receipts and reputation sit above x402/AP2-style payment evidence. |
| [0006](0006-provider-adapters-start-as-compatibility-reports.md) | Accepted | Provider and framework adapters start as deterministic compatibility reports. |
| [0007](0007-vercel-eve-is-a-static-export-target.md) | Accepted | Vercel eve is a static/export target, not an ADL replacement. |

## Reading Path

Start with the product and architecture spine, then use these ADRs when a decision needs rationale:

- `docs/REDDIAGENT-VISION-ROADMAP.md`
- `docs/REDDIAGENT-ARCHITECTURE.md`
- `docs/ARCHITECTURE-THESIS.md`
- `specs/ADL-v0.2.md` (canonical; v0.1 retained for history)
- `specs/HARNESS-LIFECYCLE-v0.1.md`
- `specs/PROVIDER-COMPATIBILITY-REPORT-v0.1.md`
- `specs/RAP-BRIDGE-v0.1.md`
