# STATUS: ReddiAgent Lab
_Last updated: 2026-05-21 16:47 AEST by Loki_

## RESUME FROM HERE

- **Next action:** Start Loop 1 on issue #1 and create research/SOURCE-MAP.md before detailed framework/platform notes.
- **Waiting on:** Nissan to accept the admin collaborator invite if GitHub requires acceptance. Nissan may later choose whether the repo should remain under reddinft or move to an org/user namespace.
- **Last discussed:** Nissan wants iterative development loops with retrospective reviews at the end of each loop, updating plans as needed so context can be recovered quickly.

## Current Phase

**Phase:** Phase 0 - Project setup and research framing  
**Status:** Active  
**Target date:** Initial research pack and ADL v0.1 draft by 2026-05-28.

## Key Files

- Project plan: docs/ULTRA-PLAN.md
- Architecture thesis: docs/ARCHITECTURE-THESIS.md
- Research taxonomy: research/RESEARCH-TAXONOMY.md
- Initial SPDD/OAD contract: spdd/prompt/0001-project-kickoff.md
- Loop protocol: docs/LOOP-PROTOCOL.md
- Retrospective template: retrospectives/TEMPLATE.md
- Loop 0 retrospective: retrospectives/2026-05-21-loop-0-project-setup.md
- GitHub: https://github.com/reddinft/reddiagent-lab
- Issues: https://github.com/reddinft/reddiagent-lab/issues
- Issue #1 planning/source map: https://github.com/reddinft/reddiagent-lab/issues/1
- Issue #2 framework research: https://github.com/reddinft/reddiagent-lab/issues/2
- Issue #3 platform research: https://github.com/reddinft/reddiagent-lab/issues/3
- Issue #4 homebrew/open-source research: https://github.com/reddinft/reddiagent-lab/issues/4
- Issue #5 domain model: https://github.com/reddinft/reddiagent-lab/issues/5
- Issue #6 ADL v0.1: https://github.com/reddinft/reddiagent-lab/issues/6
- Issue #7 payment/reputation extension: https://github.com/reddinft/reddiagent-lab/issues/7
- Issue #8 builder journey: https://github.com/reddinft/reddiagent-lab/issues/8
- Issue #9 loop protocol: https://github.com/reddinft/reddiagent-lab/issues/9

## Key Decisions

- 2026-05-21: Create reddiagent-lab as a private GitHub-backed project separate from Reddi Agent Protocol to avoid mixing protocol settlement work with agent-construction research.
- 2026-05-21: Treat an agent as model definition plus harness definition plus settlement/reputation extension; model and harness abstractions are first-class outputs.
- 2026-05-21: GitHub issues are the task-tracking source of truth for this project; local STATUS.md remains OpenClaw's operational resume truth.
- 2026-05-21: x402/RAP integration belongs in ReddiAgent as an optional harness capability that can resolve to Solana, Base, Stripe, other chains, or any future x402-supported rail.
- 2026-05-21: Initial private GitHub repo created at reddinft/reddiagent-lab with eight seed issues and Nissan invited as admin collaborator.
- 2026-05-21: Work will proceed in issue-anchored loops; every loop closes with a retrospective, STATUS.md update, and plan/spec adjustments if assumptions changed.

## Blockers & Flags

- [ ] Nissan admin collaborator invite is pending acceptance if GitHub requires it.
- [ ] Confirm final GitHub namespace if reddinft/reddiagent-lab should later move under nissan or another org.
- [ ] Decide whether to add a separate Notion/Plane layer; current user direction is GitHub-first.

## Agent Notes

- Keep RAP terminology precise: product name is Reddi Agent Protocol; user package is reddi-x402.
- Do not turn this repo into a RAP implementation repo. Its primary deliverable is a research-backed agent definition/harness abstraction and prosumer builder journey.
