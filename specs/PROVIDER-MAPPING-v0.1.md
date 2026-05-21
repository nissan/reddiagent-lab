# Provider Mapping v0.1

_Loop 12. Anchor issue: #13._

## Purpose

Provider mapping explains how one ADL file can target different model providers and harness runtimes.

## Mapping Table

| Target | Model mapping | Harness mapping | Compatibility risk |
|---|---|---|---|
| OpenAI Agents SDK | model.providers preferred/fallback to model selector | Agent, tools, handoffs, guardrails, tracing | Hosted/OpenAI-native tracing and tools may not port |
| Anthropic Claude | model requirements to Claude model/tool-use support | Tool schemas, MCP servers, safety policies | Full agent/session runtime must be external |
| Gemini | model requirements to Gemini model and function declarations | Function calling, code execution, grounding where supported | Google-specific deployment and grounding surfaces |
| Ollama | local endpoint/model id | External harness owns tools, state, evals | Tool calling may need custom parser/runtime |
| LangGraph | model node/provider adapter | Graph nodes, state, persistence, interrupts | Graph shape may exceed generic ADL |
| Local Python | SDK/local model client | Direct loop, registry, state, policies | Least managed, easiest to inspect |

## Compatibility Result

Every compile/adapter attempt should return:

- supported: true/false
- warnings
- unsupportedFeatures
- requiredSecrets
- requiredHostedServices
- suggestedFallback

