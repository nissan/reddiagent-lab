# ReddiAgent Lab Loop Protocol

_Created: 2026-05-21_

## Purpose

ReddiAgent Lab should move in short development loops. Each loop produces a concrete artifact, reviews what changed, and updates the plan before the next loop begins.

This protects the project from context loss and keeps the research/spec direction honest as we learn from real frameworks, platform docs, and prototype constraints.

## Loop Shape

Each loop has six steps:

1. Select one GitHub issue as the loop anchor.
2. Define the loop objective, planned artifacts, acceptance checks, and known risks.
3. Do the smallest useful research, spec, or prototype pass.
4. Run the smallest meaningful verification gate: source check, schema validation, example run, review checklist, or direct inspection.
5. Write a retrospective using retrospectives/TEMPLATE.md.
6. Update STATUS.md and any changed plans/specs before starting the next loop.

## Loop Size

Default loop size: one to three hours of focused work.

Use a smaller loop when:

- the work is exploratory.
- sources may change the plan.
- the artifact is a first draft.
- the topic touches payment, identity, reputation, or safety.

Use a larger loop only when the output is mechanical and the direction is already settled.

## Required Loop Fields

Every loop should name:

- Anchor issue.
- Objective.
- Planned artifacts.
- Acceptance checks.
- Assumptions.
- Risks.
- Decisions made.
- Retrospective findings.
- Plan changes.
- Next loop recommendation.

## Retrospective Rules

At the end of every loop, ask:

- What did we learn that changes the plan?
- Which assumption was wrong or weaker than expected?
- Which artifact became more important?
- Which artifact became less important?
- Did we find a better comparison dimension?
- Did we find a portability or lock-in risk?
- Did we find a prosumer learning hurdle?
- Does STATUS.md clearly say where to resume?

If the answer changes sequencing, update docs/ULTRA-PLAN.md in the same commit.

If the answer changes the ReddiAgent domain model, update the relevant spec in the same commit.

If the answer creates new work, open or update a GitHub issue before ending the loop.

## Context Continuity

STATUS.md is the fast resume file. It must always include:

- Current loop and anchor issue.
- Next action.
- Waiting on.
- Last decision.
- Newly created or updated artifacts.

GitHub issues are the planning spine. Any meaningful work should be traceable to an issue.

Retrospectives are the adjustment log. They explain why the plan changed.

## Initial Loop Plan

Loop 0: Project setup and loop protocol.

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/9
- Output: docs/LOOP-PROTOCOL.md, retrospectives/TEMPLATE.md, STATUS.md update.
- Acceptance: repo stays private, issue spine exists, local git status clean after push.

Loop 1: Research source map.

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/1
- Output: research/SOURCE-MAP.md.
- Acceptance: targets grouped into deep-dive, scan, and watchlist.

Loop 2: Framework matrix first pass.

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/2
- Output: research/FRAMEWORK-MATRIX.md.
- Acceptance: LangChain/LangGraph, LlamaIndex, Strands Agents, CrewAI, AutoGen, and Semantic Kernel mapped against the taxonomy.

Loop 3: Platform-native matrix first pass.

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/3
- Output: research/PLATFORM-MATRIX.md.
- Acceptance: OpenAI, Anthropic, and Gemini mapped by model boundary, harness boundary, tool model, deployment path, and lock-in risk.

Loop 4: Homebrew/open-source matrix first pass.

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/4
- Output: research/HOMEBREW-OPEN-SOURCE-MATRIX.md.
- Acceptance: Ollama, OpenOnion, OpenClaw, Hermes Agent, pi.dev, solve.it/Answer.AI, and Python tool-calling patterns mapped.

