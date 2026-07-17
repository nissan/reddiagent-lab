# ReddiAgent Lab Roadmap

_Loop 20. Anchor issue: #21._

## Now

- Stabilize ADL v0.1 prose.
- Turn examples into schema fixtures.
- Define JSON Schema for Level 0 conformance.
- Do deeper official-doc research for Tier 1 targets.
- Add Agent Spec compatibility as a report-only Level 2 target while keeping ADL canonical.
- Add A2A Agent Card compatibility as a report-only Level 2 export target while keeping ADL canonical.
- Add Vercel eve as a report-only Level 2 target while keeping ADL canonical.

## Next

- Build the static x402/MCP-to-RAP bridge report first after the current spec slice, so a builder implementing paid MCP service metadata can see the next step into Reddi Agent Protocol.
- Build a local validator.
- Build a local-python runner for simple/tool examples.
- Build provider mapping reports for OpenAI, Anthropic, Gemini, Ollama, and LangGraph.
- Build an Agent Spec compatibility report for simple/payment examples with explicit metadata-only warnings for Reddi extensions.
- Build an A2A Agent Card report/export for lossless ADL inputs with explicit metadata-only warnings for Reddi extensions.
- Add a paid-agent dry-run receipt flow with no real settlement.

## Later

- Generate starter code from one ADL file.
- Add framework adapters.
- Add ADL-to-Agent-Spec JSON/YAML export after compatibility reports are stable.
- Add RAP bridge prototype.
- Publish a prosumer guide.

## Decision Gate

Do not build payment execution until:

- ADL core is stable enough to validate.
- receipt shape is agreed.
- budget/human approval policy is enforceable.
- RAP boundary is explicit.

Do not build live external tool execution until:

- `docs/LOCAL-RUNNER-READINESS-BUNDLE.md` is green.
- the capability has a deterministic negative fixture.
- denied or failed required-gate paths are fail-closed.
- the security boundary is documented before implementation.

Next safe MCP step:

- define the static MCP runtime handoff package or connect adapter aggregation evidence into readiness traces;
- include paid MCP declarations as static metadata only, with x402 payment objects and AP2-like authority constraints preserved for RAP bridge review;
- keep all examples local and deterministic until that contract is tested;
- do not resolve or invoke MCP servers yet.

Next safe RAP bridge step:

- prioritize this as the first build immediately after the current spec slice;
- add a report-only `specs/RAP-BRIDGE-v0.1.md` driven checker and fixtures;
- preserve x402 payment challenge/proof/response vocabulary, AP2-like mandate metadata, receipts, and reputation signals;
- mark live wallet, facilitator, MCP URL, credential, command, or unrestricted spend fields as unsafe;
- keep `runtimeExecutionAllowed=false`, `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`.

Next safe Agent Spec step:

- define a static mapping from ADL to Agent Spec;
- produce compatibility reports before any export/codegen;
- preserve x402, receipt, reputation, source-boundary, and MCP fields as Reddi namespaced metadata unless the target can enforce them;
- do not install or run Agent Spec runtimes/adapters yet.

Current Agent Spec slice:

- static mapping lives in `mappings/AGENT-SPEC.md`;
- report-only checker lives in `scripts/agent_spec_compatibility.py`;
- strict fail-on-loss export mode is available with `--export-agent-spec`;
- guard test lives in `tests/test_agent_spec_compatibility.py`;
- current report summary lives in `tests/AGENT-SPEC-COMPATIBILITY-REPORT.md`.

Next safe A2A Agent Card step:

- keep ADL canonical and treat A2A Agent Card as a static discovery/export target;
- map identity, capabilities, skills, security, and supported interfaces into a report-only Agent Card;
- preserve Reddi policy, evaluation, memory, x402, receipt, reputation, source-boundary, and MCP fields as namespaced metadata unless the target can enforce them;
- fail strict export when those sections would become lossy;
- keep `runtimeExecutionAllowed=false`, `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`;
- do not install or run A2A runtimes/adapters yet.

Current A2A Agent Card slice:

- static mapping lives in `mappings/A2A-AGENT-CARD.md`;
- report-only checker lives in `scripts/adl_to_a2a_agent_card.py`;
- strict fail-on-loss export mode is available with `--export-agent-card`;
- guard test lives in `tests/test_a2a_agent_card_export.py`;
- current report summary lives in `tests/A2A-AGENT-CARD-EXPORT-REPORT.md`.

Current MCP runtime handoff slice:

- package schema lives in `specs/MCP-RUNTIME-HANDOFF-PACKAGE.schema.json`;
- report-only checker lives in `scripts/mcp_runtime_handoff_package.py`;
- ready/unsafe fixtures live in `tests/fixtures/mcp-runtime-handoff-ready.json` and `tests/fixtures/mcp-runtime-handoff-unsafe.json`;
- guard test lives in `tests/test_mcp_runtime_handoff_package.py`;
- current report summary lives in `tests/MCP-RUNTIME-HANDOFF-PACKAGE-REPORT.md`;
- readiness traces now require adapter aggregation evidence before completion;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`.

Current Agent Skills / SKILL.md slice:

- static mapping lives in `mappings/AGENT-SKILL.md`;
- report-only checker lives in `scripts/adl_to_agent_skill.py`;
- strict fail-on-loss export mode is available with `--export-skill-package`;
- guard test lives in `tests/test_agent_skill_export.py`;
- current report summary lives in `tests/AGENT-SKILL-EXPORT-REPORT.md`;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`.

Next safe Vercel eve step:

- keep ADL canonical and treat eve as a static filesystem-first compatibility/export target;
- add `mappings/EVE.md` and `scripts/eve_compatibility.py` before any strict export;
- preserve Reddi policy, evaluation, memory, x402, receipt, reputation, source-boundary, MCP, and deployment semantics as metadata-only or unsupported unless the target can enforce them;
- keep `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, `mcpInvocation=false`, and deployment disabled;
- do not install or run eve, scaffold projects, install dependencies, start a dev server, call providers/models, resolve MCP servers, access credentials, or deploy.

Current Vercel eve slice:

- research note lives in `research/2026-07-17-vercel-eve-impact.md`;
- static parity row is included in Prosumer Builder and `tests/fixtures/static-export-target-parity-matrix.json`;
- full mapping/report work is tracked by issue #202 under epic #201;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`.

Current Prosumer Builder MVP skeleton:

- static builder plan CLI lives in `scripts/prosumer_builder_plan.py`;
- it maps the eight-step MVP flow from `docs/PROSUMER-MVP.md` onto existing ADL examples, validator, local dry-run trace shape, and report-only exports;
- guard test lives in `tests/test_prosumer_builder_plan.py`;
- current report summary lives in `tests/PROSUMER-BUILDER-MVP-REPORT.md`;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`.

Current starter code generator plan:

- static starter-code review manifest CLI lives in `scripts/starter_code_plan.py`;
- it maps existing ADL examples to planned starter file paths, dry-run file manifest fixture summaries, template contract fixture summaries, blocked gates, validation state, and non-goals without writing files or rendering templates;
- guard test lives in `tests/test_starter_code_plan.py`;
- current report summary lives in `tests/STARTER-CODE-PLAN-REPORT.md`;
- static boundary remains `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, `mcpInvocation=false`, `writesFiles=false`, and `installsDependencies=false`.
