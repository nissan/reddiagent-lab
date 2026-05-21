# ReddiAgent Lab Source Map

_Created: 2026-05-21_

## Purpose

This source map decides what deserves deep research versus lighter scanning before ReddiAgent Lab writes detailed comparison matrices.

The goal is not to list every agent framework. The goal is to study the systems that reveal useful design patterns for ReddiAgent: model abstraction, harness definition, tool contracts, runtime/deployment, evaluation, observability, and payment/reputation extensibility.

## Research Tiers

### Tier 1 - Deep Dive

These targets should get dedicated notes and matrix entries.

| Target | Category | Why it matters | Starting source |
|---|---|---|---|
| LangChain / LangGraph | Framework | Dominant agent framework ecosystem; LangGraph makes harness concerns explicit: state, graph control, persistence, human-in-loop, durable execution, observability. | https://docs.langchain.com/oss/python/langgraph/overview |
| LlamaIndex | Framework | Strong data/RAG-native agent patterns; useful for data-source and tool abstractions. | https://docs.llamaindex.ai/ |
| AWS Strands Agents | Framework | New serious agent SDK backed by AWS; likely useful for production/runtime and Bedrock-adjacent patterns. | https://strandsagents.com/ |
| OpenAI Agents SDK / Responses | Platform-native | OpenAI is likely the default mental model for many prosumers; tool calling, hosted tools, tracing, and agent SDK patterns matter. | https://openai.github.io/openai-agents-python/ |
| Anthropic Claude tool use / computer use | Platform-native | Anthropic has strong patterns around tool use, computer use, MCP, and safety boundaries. | https://docs.anthropic.com/ |
| Google Gemini function calling / agent docs | Platform-native | Gemini is a major platform-native option; useful for function calling and Google ecosystem deployment patterns. | https://ai.google.dev/gemini-api/docs/function-calling |
| OpenClaw | Homebrew/open-source | Internal lived system for agent harnesses, skills, memory, tools, subagents, and session continuity. | Local workspace and OpenClaw docs |
| Regular Python tool-calling agents | Homebrew | The lowest-friction prosumer path; establishes the minimum viable harness abstraction. | Python examples and provider SDK docs |

### Tier 2 - Scan

These should be scanned and added to matrices, but only deep-dived if they reveal distinctive patterns.

| Target | Category | Why scan | Starting source |
|---|---|---|---|
| CrewAI | Framework | Popular role/task/crew abstraction; useful for multi-agent workflow language. | https://docs.crewai.com/ |
| Microsoft AutoGen | Framework | Important multi-agent conversation/workflow heritage; check current direction and portability. | https://microsoft.github.io/autogen/ |
| Microsoft Semantic Kernel | Framework | Enterprise-oriented skills/plugins/planners; useful for skill abstraction history. | https://learn.microsoft.com/semantic-kernel/ |
| AWS Bedrock Agents | Platform-native | Managed enterprise agent product; useful for hosted runtime constraints. | https://docs.aws.amazon.com/bedrock/ |
| Ollama local agents | Homebrew | Common local-model path; useful for model abstraction and offline constraints. | https://ollama.com/ |
| Hermes Agent | Homebrew/open-source | Relevant prior research; useful for self-improving skills and serverless agent economics. | Existing project notes plus current upstream docs |
| pi.dev | Homebrew/emergent | Mentioned by Nissan; scan for builder philosophy and agent creation model. | Current public docs/site |
| OpenOnion | Homebrew/emergent | Mentioned by Nissan; scan for scaffold/runtime assumptions. | Current public docs/site |
| solve.it / Answer.AI | Homebrew/emergent | Jeremy Howard/Answer.AI work may reveal pragmatic software-agent patterns. | Current public docs/site |

### Tier 3 - Watchlist

Track these only if they become clearly relevant.

| Target | Category | Why watch |
|---|---|---|
| Haystack | Framework | Mature pipeline/RAG tooling; may matter for data-heavy agents. |
| DSPy | Framework | Strong optimization/eval/programming model, less directly agent-harness oriented. |
| Pydantic AI | Framework | Pythonic structured agent abstraction; may be useful for schema-first ADL design. |
| Mastra | Framework | TypeScript agent framework; worth watching for developer-experience patterns. |
| VoltAgent | Framework | Emerging TypeScript agent framework; scan only if it appears in popularity checks. |
| Vercel AI SDK agents | Platform/framework-adjacent | Important for prosumer web-app builders, but likely more UI/app-streaming than full harness. |

## Deep-Dive Order

Recommended order:

1. LangChain / LangGraph.
2. OpenAI Agents SDK / Responses.
3. LlamaIndex.
4. AWS Strands Agents.
5. Anthropic Claude tool use / computer use / MCP.
6. Google Gemini function calling / agent patterns.
7. OpenClaw internal harness patterns.
8. Regular Python tool-calling agents.

Reasoning:

- Start with the most influential explicit harness models.
- Pair framework-native and platform-native views early.
- Keep one simple Python baseline so ReddiAgent does not overfit to heavy frameworks.
- Use OpenClaw as the lived counterexample: a real harness with memory, tools, skills, sessions, and multi-agent delegation.

## Matrix Questions

Every target should answer:

- What is the model boundary?
- What is the harness boundary?
- How are tools/functions represented?
- How are skills or reusable capabilities represented?
- How are memory and data sources represented?
- What is the runtime/deployment story?
- What is observable, debuggable, and testable?
- What is stateful or durable?
- Where does lock-in appear?
- What does a prosumer need to learn first?
- What should ReddiAgent adopt, abstract, or avoid?

## Immediate Next Artifacts

- research/FRAMEWORK-MATRIX.md for issue #2.
- research/PLATFORM-MATRIX.md for issue #3.
- research/HOMEBREW-OPEN-SOURCE-MATRIX.md for issue #4.

