# Adapter Roadmap

_Loop 57. Anchor issue: #58._

## Sequence

1. local-python dry-run adapter.
2. compatibility report generator.
3. Agent Spec compatibility report target.
4. OpenAI adapter skeleton.
5. Anthropic adapter skeleton.
6. Gemini adapter skeleton.
7. LangGraph adapter skeleton.
8. LlamaIndex data-source helper.
9. x402 dry-run receipt adapter.

## Gate

Do not generate provider code until compatibility reports are stable.

Do not emit Agent Spec JSON/YAML until the report identifies lossless vs metadata-only mappings for Reddi extensions.

Current Agent Spec compatibility work now includes a strict `--export-agent-spec` mode. It emits static JSON/YAML review documents only when every input is lossless; otherwise it exits non-zero with diagnostics and emits no mapped document.

Next adapter step: resume the MCP handoff path with static handoff evidence only. Do not resolve or invoke MCP servers.
