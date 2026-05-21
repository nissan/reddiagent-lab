# STATUS: ReddiAgent Lab
_Last updated: 2026-05-21 15:05 AEST by Loki_

## RESUME FROM HERE

- **Next action:** Use GitHub issues as the project spine: complete issue 1 research taxonomy, then issue 2 architecture thesis, then issue 3 Agent Definition Language v0.1.
- **Waiting on:** Nothing blocking. Nissan may later choose whether the repo should remain under reddinft or move to an org/user namespace.
- **Last discussed:** Nissan wants a separate project from Reddi Agent Protocol to research agent-building patterns and design a ReddiAgent abstraction for model plus harness plus x402-compatible payment/reputation extension.

## Current Phase

**Phase:** Phase 0 - Project setup and research framing  
**Status:** Active  
**Target date:** Initial research pack and ADL v0.1 draft by 2026-05-28.

## Key Files

- Project plan: docs/ULTRA-PLAN.md
- Architecture thesis: docs/ARCHITECTURE-THESIS.md
- Research taxonomy: research/RESEARCH-TAXONOMY.md
- Initial SPDD/OAD contract: spdd/prompt/0001-project-kickoff.md
- GitHub: https://github.com/reddinft/reddiagent-lab
- Issues: https://github.com/reddinft/reddiagent-lab/issues

## Key Decisions

- 2026-05-21: Create reddiagent-lab as a private GitHub-backed project separate from Reddi Agent Protocol to avoid mixing protocol settlement work with agent-construction research.
- 2026-05-21: Treat an agent as model definition plus harness definition plus settlement/reputation extension; model and harness abstractions are first-class outputs.
- 2026-05-21: GitHub issues are the task-tracking source of truth for this project; local STATUS.md remains OpenClaw's operational resume truth.
- 2026-05-21: x402/RAP integration belongs in ReddiAgent as an optional harness capability that can resolve to Solana, Base, Stripe, other chains, or any future x402-supported rail.

## Blockers & Flags

- [ ] Confirm final GitHub namespace if reddinft/reddiagent-lab should later move under nissan or another org.
- [ ] Decide whether to add a separate Notion/Plane layer; current user direction is GitHub-first.

## Agent Notes

- Keep RAP terminology precise: product name is Reddi Agent Protocol; user package is reddi-x402.
- Do not turn this repo into a RAP implementation repo. Its primary deliverable is a research-backed agent definition/harness abstraction and prosumer builder journey.

