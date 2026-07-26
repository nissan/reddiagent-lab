> **Archived.** This planning document is superseded; current sequencing lives in [docs/ROADMAP.md](../ROADMAP.md).

# Implementation Backlog

_Loop 62. Anchor issue: #65._

## Next

- Keep the Prosumer Builder MVP skeleton aligned with validator, local dry-run traces, and report-only exports.
- Level 1 deterministic trace tests.
- Provider compatibility report snapshots.
- ADL schema tightening.
- Local runner plugin interface.
- OpenAI adapter compatibility-only mode.
- Anthropic MCP compatibility-only mode.
- Payment dry-run receipt fixture. Done in issue #157: refreshed deterministic positive/negative receipt reports with AP2/x402/RAP bridge boundaries.

## Later

- Real local tool execution.
- Starter code generator. First report-only manifest slice drafted in issue #168; dry-run file manifest fixtures added in issue #174; template contract fixtures added in issue #184; no runnable generation yet.
- Optional ADL-to-Agent-Spec exporter expansion only for lossless ADL inputs.
- Optional A2A runtime adapter only after Agent Card export semantics are stable and reviewed.
- Optional Agent Skills client/runtime adapter only after `SKILL.md` export semantics are stable and reviewed.
- Vercel eve compatibility. First research note added in `research/2026-07-17-vercel-eve-impact.md`; static parity row added in issue #196; full mapping/report tracked by issue #202 under epic #201. No eve runtime/install/deployment is approved.
- Provider adapter codegen. First compatibility-only plan drafted in issue #177; no runnable adapter code generation yet.
- RAP dry-run bridge.
- Prosumer UI.
