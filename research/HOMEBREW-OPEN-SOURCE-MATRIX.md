# Homebrew and Open-Source Matrix

_Loop 4. Anchor issue: #4._

## Summary

Homebrew systems show what prosumers can actually understand and modify. They are the antidote to over-designed ADL.

## Matrix

| System | Model boundary | Harness boundary | Strength | Risk | ReddiAgent implication |
|---|---|---|---|---|---|
| Regular Python tool calling | SDK client or local model call | Prompt loop, tool registry, state, retries, output parsing | Clearest minimum viable harness | Easy to build unsafe or unobservable loops | ADL must compile to a simple Python baseline |
| Ollama local agents | Local model endpoint | External script/app owns tools and state | Offline/private/cheap | Weak native tool/runtime discipline | ModelProfile must support local endpoints and weaker capability guarantees |
| OpenClaw | Model routing plus session runtime | Tools, skills, memory, subagents, channels, persistence, policies | Lived example of robust harness operations | Internal complexity, not prosumer-simple | Extract concepts, not implementation details |
| Hermes Agent | Model plus serverless harness ideas | Skills, persistent user modeling, self-improvement | Useful self-improving skill direction | May depend on cloud/serverless assumptions | Skills and memory should be explicit and reviewable |
| OpenOnion | To scan | To scan | Potential scaffold/runtime ideas | Unclear maturity | Keep as scan target |
| pi.dev | To scan | To scan | Mentioned by Nissan; may reveal product philosophy | Unclear maturity | Keep as scan target |
| solve.it / Answer.AI | To scan | To scan | Pragmatic software-agent patterns likely | Unclear current public shape | Keep as scan target |

## Findings

- The simplest agent is a loop with a model, tool registry, state, and stop condition.
- A useful harness becomes serious when it adds permissions, evals, observability, persistence, and recovery.
- ReddiAgent must stay teachable: every high-level concept should degrade to a Python loop explanation.

## Plan Adjustment

Examples should include a minimal Python-compatible ADL profile before payment or multi-agent examples.

