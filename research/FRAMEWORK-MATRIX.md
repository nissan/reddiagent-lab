# Framework Matrix

_Loop 2. Anchor issue: #2._

## Summary

Frameworks differ mostly in where they draw the harness boundary. ReddiAgent should not copy any single framework. It should extract the common harness concepts and keep provider/runtime choices replaceable.

## Matrix

| Framework | Model boundary | Harness boundary | Strength | Risk | ReddiAgent implication |
|---|---|---|---|---|---|
| LangChain / LangGraph | Provider adapters and chat model interfaces | Graph/state/runtime, persistence, interrupts, streaming, tools, observability via LangSmith | Most explicit durable harness model | Ecosystem complexity and LangSmith gravity | Adopt graph/state/eval concepts; avoid requiring one runtime |
| LlamaIndex | LLM adapters plus data/query engines | Data agents, indexes, tools, query workflows | Best data-source/RAG mental model | Can overfit agents to retrieval workflows | Treat data sources and indexes as first-class harness resources |
| AWS Strands Agents | Model/provider selectable through SDK, Bedrock-friendly | Agent loop, tools, callbacks, deployment in AWS ecosystem | Strong production/cloud story | AWS/Bedrock gravitational lock-in | Use as production harness reference, not schema source of truth |
| CrewAI | LLM per agent/crew | Role, task, crew, process, tools | Easy multi-agent teaching model | Role-play can hide real runtime/eval details | Borrow workflow language for prosumers; require explicit harness contracts |
| AutoGen | LLM config per conversable agent/team | Multi-agent conversations, tools, human participation | Strong collaboration pattern | Conversation abstraction can obscure state and authority | Model multi-agent coordination separately from core single-agent ADL |
| Semantic Kernel | Services and connectors | Plugins/functions, planners, memory, enterprise orchestration | Clear plugin/skill lineage | Enterprise shape may feel heavy to prosumers | Skills/plugins should be portable and typed |

## Findings

- LangGraph is the strongest reference for durable harness concerns.
- LlamaIndex is the strongest reference for data-source/harness integration.
- CrewAI is easiest to explain but weakest as a rigorous harness model.
- AutoGen is useful for multi-agent collaboration but should not define the base ReddiAgent abstraction.
- Semantic Kernel reinforces that tools/skills/plugins need stable contracts.

## Plan Adjustment

ReddiAgent ADL should separate model profile, harness runtime, tool/function contracts, data/memory resources, coordination mode, and observability/eval gates.

