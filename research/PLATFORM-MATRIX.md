# Platform-Native Matrix

_Loop 3. Anchor issue: #3._

## Summary

Platform-native systems are useful because they define what prosumers will see first. They also reveal lock-in risks: hosted tools, tracing, files, evals, and deployment often become implicit harness dependencies.

## Matrix

| Platform | Model boundary | Harness boundary | Strength | Risk | ReddiAgent implication |
|---|---|---|---|---|---|
| OpenAI Agents SDK / Responses | OpenAI model plus SDK model abstraction | Agent, tools, handoffs, tracing, guardrails, sessions | Strong beginner path and hosted model/tool integration | OpenAI-native tracing/tool assumptions | ReddiAgent needs adapter mapping to OpenAI agents but cannot become OpenAI-specific |
| Anthropic Claude | Claude model plus tool-use schema | Tool use, computer use, MCP, safety guidance | Strong explicit tool-call and MCP ecosystem fit | Less full-stack hosted agent runtime than OpenAI | Treat MCP and tool safety as key harness primitives |
| Google Gemini | Gemini model plus function calling / code execution / grounding | Function calling, Google ecosystem APIs, Vertex deployment paths | Strong multimodal and Google cloud integration | Google ecosystem lock-in and multiple product surfaces | Map Gemini function declarations to ReddiAgent tool contracts |
| AWS Bedrock Agents | Bedrock model choice | Managed agents, action groups, knowledge bases, guardrails | Enterprise managed runtime | Managed service lock-in | Useful deployment target, not canonical ADL shape |

## Findings

- Platform docs usually begin at model/tool calling, then gradually reveal harness concerns.
- OpenAI makes an agent object approachable; Anthropic makes tool safety and MCP salient; Gemini makes function declarations and ecosystem integration salient.
- ReddiAgent should be able to compile down to platform-native agents where possible.

## Plan Adjustment

ADL needs explicit portability fields: native target compatibility, unsupported features, required hosted services, and fallback strategy.

