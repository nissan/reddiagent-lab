# Adapter Roadmap

_Loop 57. Anchor issue: #58._

## Sequence

1. local-python dry-run adapter.
2. compatibility report generator.
3. Agent Spec compatibility report target.
4. Provider adapter codegen compatibility-only plan.
5. OpenAI adapter skeleton.
6. Anthropic adapter skeleton.
7. Gemini adapter skeleton.
8. LangGraph adapter skeleton.
9. LlamaIndex data-source helper.
10. x402 dry-run receipt adapter.

## Gate

Do not generate provider code until compatibility reports are stable.

Do not emit Agent Spec JSON/YAML until the report identifies lossless vs metadata-only mappings for Reddi extensions.

Current Agent Spec compatibility work now includes a strict `--export-agent-spec` mode. It emits static JSON/YAML review documents only when every input is lossless; otherwise it exits non-zero with diagnostics and emits no mapped document.

Next adapter step: resume the MCP handoff path with static handoff evidence only. Do not resolve or invoke MCP servers.

Current provider adapter codegen plan:

- static planner lives in `scripts/provider_adapter_codegen_plan.py`;
- guard test lives in `tests/test_provider_adapter_codegen_plan.py`;
- current report summary lives in `tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md`;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`,
  `paymentAccess=false`, `mcpInvocation=false`, `writesFiles=false`,
  `installsDependencies=false`, and `generatesRunnableCode=false`.
