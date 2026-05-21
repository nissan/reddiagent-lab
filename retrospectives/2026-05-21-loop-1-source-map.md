# Retrospective - Loop 1 Source Map

_Date: 2026-05-21_

## Loop

- Anchor issue: https://github.com/reddinft/reddiagent-lab/issues/1
- Objective: Create the initial source map and classify research targets before detailed matrices.
- Planned artifacts: research/SOURCE-MAP.md.
- Actual artifacts: research/SOURCE-MAP.md.

## Acceptance Checks

- [x] Source map exists.
- [x] Targets grouped into deep-dive, scan, and watchlist.
- [x] Deep-dive order defined.
- [x] STATUS.md updated.
- [x] GitHub issue updated.

## What Changed

- LangChain/LangGraph and OpenAI Agents SDK should be studied first because they make influential but different assumptions about the harness boundary.
- Regular Python tool-calling should be a first-class baseline, not an afterthought, because it shows the minimum viable harness a prosumer can understand.
- OpenClaw should be treated as a lived reference harness, not just another external framework.

## Decisions

- Use three research tiers: deep dive, scan, watchlist.
- Start matrix work with frameworks, then platform-native systems, then homebrew/open-source systems.
- Keep source mapping separate from matrix writing to avoid scope creep.

## Assumptions Tested

- Assumption: We can compare all systems with one taxonomy.
- Result: Mostly valid, but platform-native systems need extra attention to hosted tool/runtime lock-in.
- Impact: Platform matrix should explicitly include lock-in and portability risk.

## Risks Found

- Emerging tools may have weak or changing docs; watchlist should stay flexible.
- Some systems overlap categories, especially hosted platform SDKs that look like frameworks.
- The research can become too broad unless every target is tied back to ReddiAgent implications.

## Plan Adjustments

- Added Tier 3 watchlist so we can track emerging tools without blocking core research.
- Added deep-dive order to reduce decision overhead in the next loop.

## Next Loop Recommendation

- Start issue #2 and create research/FRAMEWORK-MATRIX.md.
- Begin with LangChain/LangGraph, LlamaIndex, and Strands Agents before scanning CrewAI, AutoGen, and Semantic Kernel.

