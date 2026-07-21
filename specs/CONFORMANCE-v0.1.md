# Conformance Checklist v0.1

_Loop 18. Anchor issue: #19._

## Goal

Before implementation, define what a ReddiAgent validator or adapter must prove.

## Checklist

- [ ] Required ADL fields exist.
- [ ] Model requirements are valid.
- [ ] Provider mapping is possible or incompatibility is reported.
- [ ] Tool schemas are typed.
- [ ] Secret values are not embedded.
- [ ] Policies cover every risky capability.
- [ ] Payment extension has a budget policy when enabled.
- [ ] Required eval gates are known.
- [ ] Required eval gates are blocking and warning gates are non-blocking.
- [ ] Runtime target is known.
- [ ] Unsupported runtime features are reported before execution.
- [ ] Receipt requirements are enforceable if enabled.
- [ ] Observability minimum events are configured.

## Conformance Levels

- Level 0: schema-valid.
- Level 1: local-python runnable.
- Level 2: provider-adapter compatible.
- Level 3: payment/reputation extension compatible.
- Level 4: production deployment compatible.

## Agent Spec Compatibility Gate

_Added 2026-05-31._

Agent Spec compatibility is a Level 2 report-only target until a separate runtime gate is approved.

Minimum evidence:

- ADL-to-Agent-Spec mapping is documented in `specs/AGENT-SPEC-COMPATIBILITY-v0.1.md`.
- Compatibility reports distinguish `supported` from `lossless`.
- Reddi-only policy, source-boundary, MCP, x402, receipt, and reputation fields are either preserved as namespaced metadata or reported as unsupported.
- Reports include `runtimeExecutionAllowed=false`, `networkAccess=false`, `paymentAccess=false`, and `mcpInvocation=false`.
- No Agent Spec runtime, adapter, MCP server, external tool, or payment rail is executed as part of compatibility checking.

## Level 1 Local Fixture Gate Completion

_Loops 279-303. Anchor issue: #131._

Level 1 local-python conformance now includes local fixture gate completion evidence:

- approved local fixture source output must produce `completion.requiredGateStatus = pass`
- failed required source checks must produce `completion.requiredGateStatus = fail`
- allowed denied-tool reporting must produce `completion.requiredGateStatus = fail`
- `completion.transportStatus = pass` means the runner produced a deterministic report, not that the task completed

The active evidence lives in `tests/LEVEL-1-CONFORMANCE-REPORT.md` and is enforced by `tests/test_level1.py`.

## ADL v0.2 Eval-Gate Completion Contract

_Anchor issue: #313._

Conformance must distinguish blocking required gates from visible warning
gates before any runtime or adapter marks a task complete:

- required gate missing/fail/warn/skipped/mismatched evidence => `completion.requiredGateStatus = fail`
- required gate pass evidence => may contribute to `completion.requiredGateStatus = pass`
- warning gate missing/fail/warn/skipped/mismatched evidence => visible warning evidence only
- `completion.status` mirrors `completion.requiredGateStatus`
- `completion.transportStatus = pass` does not override required-gate failure

The active ADL v0.2 schema and fixtures are enforced by
`tests/test_adl_v02_eval_gate_completion.py`.

## ADL v0.2 Conformance Profile Field Sets

_Anchor issue: #315._

ADL v0.2 conformance levels now map to deterministic required field sets and
evidence outputs. Validators must report `requestedLevel`, `achievedLevel`,
`missingFieldsByLevel`, and `forbiddenCapabilitiesByLevel` without activating a
runtime, provider, MCP server, payment rail, or hosted deployment.

Level inheritance is fail-closed:

- Level 0 requires schema-valid ADL v0.2 top-level, metadata, model, and harness
  shape.
- Level 1 adds local-python runnable fields: instructions, declared runtime target,
  eval gates, local trace evidence, `completion.requiredGateStatus`, and
  required `trace.started`, `trace.completed`, `task.completed`, and
  `task.failed` observability events.
- Level 2 adds provider-adapter compatibility fields: model capability,
  preferred provider, requirements, policies, eval gates, provider report, and
  unsupported-execution boundary evidence, plus `model.called`,
  `policy.checked`, and `eval.checked` observability events.
- Level 3 adds payment/reputation extension fields: enabled x402 intents with
  policy refs, required receipts, reputation signals, and payment-policy
  evidence, plus `payment.intent.created`, `receipt.emitted`, and
  `reputation.signal.emitted` observability events.
- Level 4 adds production deployment fields: production runtime target,
  deployment environment, rollback, observability events, recovery disable, and
  deployment readiness evidence. Level 4 observability must also include
  `deployment.health.checked` and `adapter.loss.reported` so adapter/export
  loss is explicit before review. Mainnet remains separately approval-gated.

Payment/reputation declarations are forbidden before Level 3. Production
deployment descriptors and production runtime targets are forbidden before Level
4. Schema-valid ADLs that request a higher level but omit that level's required
fields must fail conformance with clear missing-field diagnostics. Lower levels
do not imply permission to use capabilities gated by higher levels, and higher
levels cannot skip missing lower-level requirements.

The active ADL v0.2 conformance matrix is documented in `specs/ADL-v0.2.md` and
enforced by `tests/test_adl_v02_conformance_profiles.py`.

## ADL v0.2 Observability Minimums

_Anchor issue: #318._

ADL v0.2 observability is structured trace/export configuration. Validators
must inspect event declarations, summaries, destinations, evidence refs,
retention, redaction, and receipt/export relationships without activating a
runtime or writing to a live collector.

Minimum events are cumulative:

- Level 1: `trace.started`, `trace.completed`, `task.completed`, `task.failed`
- Level 2: `model.called`, `policy.checked`, `eval.checked`
- Level 3: `payment.intent.created`, `receipt.emitted`, `reputation.signal.emitted`
- Level 4: `deployment.health.checked`, `adapter.loss.reported`

A schema-valid ADL that requests a level but omits a required event must fail
conformance with `harness.observability.events.<event-name>` diagnostics.
`local-only` destinations are allowed for local trace output. Adapter-managed or
external-reviewed destinations remain static metadata until a separately
reviewed adapter/export gate is approved.

## Required Gate Shell Failure

_Loops 304-328. Anchor issue: #131._

`--fail-on-required-gate` is an optional Level 1 automation mode. It must preserve JSON diagnostics while returning exit code `3` when required gates fail.

This mode is not a new tool capability. It only changes process exit behavior after local fixture evaluation has already produced a report.

## CLI Usage Evidence

_Loops 329-353. Anchor issue: #131._

Level 1 conformance now includes a CLI usage matrix for local-python runner outcomes. The matrix is documented in `tests/CLI-USAGE-MATRIX.md` and enforced by `tests/test_cli_usage_matrix.py`.

The matrix proves validation errors, strict denied tools, allowed denied-tool reporting, source-check failure reporting, and required-gate shell failure keep distinct exit codes and diagnostics.

Level 1 rollout readiness is packaged in `docs/LOCAL-RUNNER-READINESS-BUNDLE.md` and guarded by `tests/test_readiness_bundle.py`.

That bundle is not a live-capability approval. It is the required evidence checklist before any real external tool path, MCP execution, network access, shell execution, credential access, messaging, filesystem mutation, or live payment behavior is considered.

## MCP Adapter Shape Evidence

_Loops 379-403. Anchor issue: #131._

Level 1 readiness now includes read-only MCP adapter shape evidence:

- `examples/mcp-readonly-agent.yaml` declares an MCP tool with `serverRef` and `toolName`
- `examples/unsafe/mcp-live-server-fixture.yaml` proves embedded live execution fields fail readiness
- `scripts/adapter_readiness.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`
- `tests/test_adapter_readiness.py` enforces both the pass and fail paths

This is compatibility evidence only. It does not execute MCP tools or resolve MCP servers.

## MCP Adapter Source-Check Evidence

_Loops 404-428. Anchor issue: #131._

Level 1 readiness now includes deterministic source-check evidence for MCP-shaped adapter outputs:

- `tests/fixtures/mcp-approved-output.json` passes approved-source checking
- `tests/fixtures/mcp-unapproved-output.json` fails approved-source checking with repair guidance
- `scripts/mcp_adapter_source_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`
- `tests/test_mcp_adapter_source_check.py` enforces both paths

This is output-shape evidence only. It does not execute MCP tools, resolve MCP servers, or call a network.

## MCP Server Resolution Evidence

_Loops 429-453. Anchor issue: #131._

Level 1 readiness now includes static MCP server-resolution evidence:

- `tests/fixtures/mcp-server-registry-approved.json` passes
- `tests/fixtures/mcp-server-registry-empty.json` fails missing serverRef
- `tests/fixtures/mcp-server-registry-live.json` fails live resolution fields
- `scripts/mcp_server_resolution_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`
- `tests/test_mcp_server_resolution.py` enforces all three paths

This is static config evidence only. It does not resolve or invoke MCP servers.

## MCP Capability Policy Evidence

_Loops 454-478. Anchor issue: #131._

Level 1 readiness now includes static MCP capability-policy evidence:

- `tests/fixtures/mcp-capability-policy-approved.json` passes
- `tests/fixtures/mcp-capability-policy-empty.json` fails missing static policy
- `tests/fixtures/mcp-capability-policy-overbroad.json` fails overbroad live capability grants
- `scripts/mcp_capability_policy_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`
- `tests/test_mcp_capability_policy.py` enforces all three paths

This is static policy evidence only. It does not resolve or invoke MCP servers.

## MCP Readiness Trace Evidence

_Loops 479-503. Anchor issue: #131._

Level 1 readiness now includes static MCP trace/evidence requirements:

- `tests/fixtures/mcp-readiness-evidence-pass.json` proves all required MCP readiness events pass
- `tests/fixtures/mcp-readiness-evidence-fail.json` fails missing server-resolution evidence, live-access claims, and bad aggregate completion status
- `scripts/mcp_readiness_evidence_check.py` reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`
- `tests/test_mcp_readiness_evidence.py` enforces both paths

This is static evidence validation only. It does not resolve or invoke MCP servers.

## MCP Readiness Release Checklist

_Loops 504-528. Anchor issue: #131._

Level 1 readiness now includes a review-ready MCP readiness release checklist:

- `docs/MCP-READINESS-RELEASE-CHECKLIST.md` aggregates the static MCP evidence set
- `tests/test_mcp_readiness_release.py` guards required evidence links and boundary language
- `tests/smoke-validation.sh` runs the checklist drift test

This is a review artifact only. It does not resolve or invoke MCP servers.
