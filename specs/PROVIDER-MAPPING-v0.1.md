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
| Agent Spec | model requirements to Agent Spec LLM config | Agent/Flow components, tools, runtime adapter metadata | Reddi policy/payment/reputation/source-boundary semantics may be metadata-only |
| Local Python | SDK/local model client | Direct loop, registry, state, policies | Least managed, easiest to inspect |

## Compatibility-Only Modes

Provider-specific compatibility-only modes are static report artifacts. They do not call providers,
read credentials, activate runtimes, resolve MCP servers, or invoke tools.

- `openai-adapter-compatibility-only` maps ADL instructions, non-MCP function tools, model profile,
  and Reddi metadata-only semantics for an OpenAI-facing review.
- `anthropic-mcp-compatibility-only` maps ADL instructions, Claude-style tool-use schema ids,
  MCP declaration metadata (`id`, `serverRef`, `toolName`), model profile, and Reddi metadata-only
  semantics for an Anthropic/MCP-facing review.
- `gemini-provider-compatibility-only` maps ADL instructions, function declaration ids, model
  profile, structured-output capability, explicit grounding/code-execution diagnostics, and Reddi
  metadata-only semantics for a Gemini-facing review.
- `ollama-local-provider-compatibility-only` maps ADL instructions, local model profile metadata,
  function tool ids, structured-output/tool-calling harness notes, and Reddi metadata-only semantics
  for a local/Ollama-facing review without probing or starting a local model runtime.
- `langgraph-compatibility-report-only` maps ADL model profile metadata to a LangGraph-facing
  review shape with static graph/state/node/edge/checkpoint/interrupt metadata. It does not
  generate, compile, install, or run a graph; Reddi policy, eval, memory, x402, receipt,
  reputation, and MCP semantics remain metadata-only or static-plan-only until a reviewed runtime
  graph enforces them.

MCP declarations remain unsupported for execution in these modes until a separate reviewed runtime
adapter explicitly enables MCP server resolution and invocation.

## Compatibility Result

Every compile/adapter attempt should return:

- supported: true/false
- warnings
- unsupportedFeatures
- requiredSecrets
- requiredHostedServices
- suggestedFallback

Agent Spec mappings must also report:

- lossless: true/false
- metadataOnlyExtensions
- runtimeExecutionAllowed: false until a separate runtime gate exists
