# Agent Skills / SKILL.md Export Report

_Issue: #134; expanded by #176. Generated from `scripts/adl_to_agent_skill.py` fixtures._

## Summary

ReddiAgent can emit a static Agent Skills package review for ADL inputs while keeping ADL canonical. Strict package export is allowed only for lossless inputs that do not rely on ReddiAgent runtime, payment, MCP, memory, policy, eval, receipt, or reputation semantics that `SKILL.md` clients cannot enforce.

## Evidence

- `examples/simple-agent.yaml` maps to a static `simple-research-helper/SKILL.md` review package, but strict export is lossy because model, memory, policy, eval, and runtime semantics become metadata/body notes.
- `examples/payment-agent.yaml` maps to a static `paid-specialist-researcher/SKILL.md` review package, but strict export is refused because x402 payment, receipt, reputation, hosted runtime, and Reddi policy/eval semantics are metadata-only or unsupported for execution.
- `tests/fixtures/agent-skill-lossless-agent.yaml` exports a lossless static package with required `name` and `description`, optional `license`, `compatibility`, `allowed-tools`, static tool declarations, usage notes, constraints, progressive-disclosure references, script declarations, and asset declarations.
- `tests/fixtures/agent-skill-lossy-agent.yaml` fails strict export with exit code 3 and diagnostics for live payment, MCP invocation, non-local runtime, and metadata-only ReddiAgent sections.
- Strict package export frontmatter now includes a deterministic `reddiagent.agentSkillsPackage` metadata summary pinning safe package declarations without activating an Agent Skills client.

## Static Boundary

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

No Agent Skills client is installed or invoked. No `SKILL.md` package is activated. No script, MCP server, wallet, facilitator, payment rail, settlement, credential, network, or runtime path is executed.
