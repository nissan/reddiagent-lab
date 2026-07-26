# Microsoft Agent Framework: Landscape and ADL Compatibility Assessment

_Date: 2026-07-26 AEST. Companion to the same-day agent-payments landscape
note. Sources checked live 2026-07-26._

## What MAF is (July 2026)

Microsoft Agent Framework (MAF) is the MIT-licensed convergence of Semantic
Kernel and AutoGen (launched Oct 2025, 1.0 GA April 2026). Current: Python
`agent-framework` 1.12.1 (2026-07-23), .NET GA, Go public preview
(2026-07-10). Ships MCP client + hosting, A2A support (v1.0 "coming soon" at
GA), OpenAPI tools, OpenTelemetry GenAI-semantic instrumentation,
function-approval middleware + workflow human-in-the-loop, and the Foundry
Agent Service / Hosted Agents runtime. Release churn is real: ~10-day minor
cadence with one reported post-GA breaking change (1.9.0).

Two stable declarative YAML surfaces (both Microsoft-proprietary,
Copilot-Studio schema lineage, PowerFx expressions):

- **`kind: Prompt`** declarative agents — name/description/instructions/
  model{id,connection,options}/outputSchema, `=Env.*` interpolation.
- **`kind: Workflow`** declarative workflows — **1.0 on 2026-07-23**:
  control flow, agent invocation, function/MCP/HTTP tools, HITL
  pause-for-approval, checkpointing. The .NET path gravitates toward Foundry
  (`AzureAgentProvider`); the provider-agnostic factory is
  `ChatClientPromptAgentFactory`.

"Agent spec" disambiguation: MAF's YAML ≠ M365 Copilot declarative-agent
manifests ≠ AGNTCY OASF (Linux Foundation) ≠ Open Agent Spec (Oracle
lineage — the one our existing `mappings/AGENT-SPEC.md` targets, now being
absorbed into OASF). MAF adopted none of the open formats.

Payments: MAF has **no x402/AP2 surface**, and Microsoft is absent from the
x402 Foundation's 40-member roster; Microsoft's commerce bet is ACP via
consumer Copilot Checkout (Stripe/PayPal, Jan 2026), not an SDK capability.

## Alternatives at a glance (ranked by momentum)

| Framework | Status | Declarative? | MCP / A2A | Notable for ADL |
|---|---|---|---|---|
| LangGraph | 1.x GA, largest ecosystem | No (code graphs) | ✅ / partial | `interrupt()`+checkpointing = strongest HITL substrate for ADL approval policies |
| OpenAI Agents SDK + AgentKit | maturing fast | No (visual builder is platform-bound) | ✅ / ❌ | Guardrails ≠ authority policies; OpenAI-model gravity |
| **MAF** | 1.12.1 GA | **Yes (GA)** | ✅ / ✅(pre-1.0) | Only GA declarative YAML in a top-tier framework; broadest provider connectors |
| Google ADK | 2.0 GA (5 langs) | Yes (experimental Agent Config) | ✅ / ✅ native | A2A originator; Google is x402 premier member → likeliest first native x402 framework target |
| CrewAI | ~1.14.x | Yes (untyped YAML) | ✅ / partial | Syntactically easiest export, weakest policy semantics |
| AWS Strands | 1.x GA | No | ✅ / ✅ | AgentCore runtime identity/permissions; AWS is x402 premier member |
| PydanticAI | V2 (Jun 2026) | No | ✅ / ✅ | Only in-library eval story (pydantic-evals); approval-required tools |
| SK / AutoGen | maintenance | — | — | Migration sources only, not adapter targets |

## Universal portability pattern

Every framework maps the agent core (model, instructions, function tools,
MCP) cleanly. Every framework loses ADL's **eval-gates-as-completion-
contracts** (evals live in external platforms everywhere). **No framework has
any target for x402 payment authority, receipts, or reputation** — ADL's
payment extension has zero collision as of July 2026. A2A v1.0 signed Agent
Cards are the nearest neighbor to ADL identity/reputation metadata.

## MAF adapter design facts (for the adapter work item)

1. Target `kind: Prompt` YAML as primary export; code-first middleware
   fallback for unsupported fields. Declarative workflows 1.0 (2026-07-23)
   for orchestration-bearing definitions.
2. MCP is a dual surface: ADL MCP tool blocks map "supported", and MAF can
   *expose* an ADL-defined agent as an MCP tool.
3. Compatibility report grades: policies → `degraded` (function-approval
   middleware gates calls but has no budget/scope/rate semantics); eval
   gates → `degraded` (Foundry-external, Azure-coupled); observability
   minimums → advisory; x402/receipts/reputation → `unsupported`.
4. Pin `agent-framework>=1.12,<2` and CI against the ~10-day cadence; prefer
   `ChatClientPromptAgentFactory` over the Foundry-coupled provider path.
5. Payment convergence watch: Google (ADK) and AWS (Strands) sit on the x402
   Foundation premier board — they are the likeliest frameworks where ADL
   x402 blocks eventually map natively; order the adapter roadmap accordingly.

## Competitor or export target?

**Export target — yes, the best-in-class one.** As a spec competitor MAF's
YAML matters only inside the Microsoft estate: single-vendor, PowerFx-bound,
Foundry-gravitating, no capability envelope, no policy language, no eval
contracts, no payment constructs. ADL's real competitive set for *portable*
definitions is **AGNTCY OASF + Open Agent Spec under the Linux Foundation** —
which our existing Agent Spec mapping already targets and must now track
through the OASF absorption.

## Gaps for ADL's next release (v0.3 seeds from this assessment)

1. **First-class agent output schema.** MAF `outputSchema` (and PydanticAI
   typed outputs) have no lossless ADL source — ADL v0.2 only carries a
   boolean `structuredOutput` requirement. Add an optional
   `model.outputSchema` (JSON Schema) slot.
2. **MAF compatibility target + report.** New Level-2 target alongside Agent
   Spec/A2A/Agent Skills, per the design facts above.
3. **Open Agent Spec mapping refresh** to track OASF absorption and LF
   governance (our mapping predates it).
4. **Policy-degradation vocabulary.** The compatibility report's `degraded`
   bucket should standardize loss reasons for policy semantics
   (approval-only, no-budget, no-scope, advisory-observability) so MAF/ADK/
   LangGraph reports stay comparable.
5. Existing v0.3 seeds unchanged and reinforced: charge-side conformance
   enforcement, price-discovery pointers (x402 V2 metadata), session-cap
   concept (MPP adapter prerequisite).

## Boundary

Research/report evidence only. No live invocation, provider calls, or
external mutation occurred.
