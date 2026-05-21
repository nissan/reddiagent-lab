# REASONS-LITE - ReddiAgent Lab Project Kickoff

_Status: draft | Owner: Loki | Project: reddiagent-lab | Issue/PR: TBD_

## R - Requirements / Definition of Done

- Create a separate project from Reddi Agent Protocol for agent-construction research and ReddiAgent abstraction design.
- Use private GitHub repo versioning.
- Use GitHub issues as the initial planning and tracking system.
- Preserve local STATUS.md for OpenClaw continuity.

DoD checklist:

- [x] Local project scaffold exists.
- [x] Initial research and architecture artifacts exist.
- [ ] Private GitHub repo exists.
- [ ] Initial GitHub issues exist.
- [ ] Repo pushed and local git status clean.

## E - Entities / Handoff Objects

| Entity / object | Purpose | Key states/fields | Existing or new? |
|---|---|---|---|
| ReddiAgent Lab | Separate workspace for agent-building research | private repo, issues, research/spec docs | New |
| Agent Definition Language | Portable model/harness schema | model, harness, extensions | New |
| Harness Definition | Defines executable agent environment | tools, skills, data, runtime, evals, deployment | New |
| Payment/Reputation Extension | x402/RAP bridge | payment intents, rails, receipts, reputation | New |

## A - Approach / Key Decisions

- Chosen approach: start with a documentation/spec repo, not implementation code.
- Alternatives rejected: putting this inside RAP repo, because it would blur protocol implementation with builder education and framework research.
- Why this is safe/simple enough: the first milestone is research/specification; no production code or external service runtime is introduced.
- Known tradeoffs: GitHub-first tracking means Notion/Plane are deferred unless Nissan asks to add them.

## S - Structure / Files Touched

| Surface | Expected change | Owner |
|---|---|---|
| README.md | Project overview and operating model | Loki |
| STATUS.md | OpenClaw continuity file | Loki |
| docs/ULTRA-PLAN.md | Full plan | Loki |
| docs/ARCHITECTURE-THESIS.md | Initial model/harness/payment thesis | Loki |
| research/RESEARCH-TAXONOMY.md | Comparison taxonomy | Loki |
| GitHub issues | First backlog | Loki |

## O - Operations / Ordered Tasks

1. Scaffold local project.
2. Write initial plan/research/architecture artifacts.
3. Initialize git and commit.
4. Create private GitHub repo.
5. Push initial commit.
6. Create GitHub issues.
7. Update STATUS.md and memory with links.

## N - Norms

- Use existing OpenClaw project continuity rules.
- Keep RAP implementation work in RAP repos.
- Keep secrets out of code, logs, and artifacts.
- Treat GitHub issues as the public project spine for this repo.
- Update STATUS.md after significant changes.

## S - Safeguards / Acceptance Checklist

- [x] Privacy boundary: repo is private.
- [x] Product boundary: RAP remains separate.
- [ ] GitHub collaborator policy checked.
- [ ] Repo pushed successfully.
- [ ] Initial issue links recorded in STATUS.md.

## Prompt/Code Sync Log

| Date | Divergence | Artifact update | Code/test update |
|---|---|---|---|
| 2026-05-21 | Initial scaffold before GitHub repo exists | This artifact marks GitHub tasks pending | N/A |

