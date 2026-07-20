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

- required gate missing/fail/warn/skipped evidence => `completion.requiredGateStatus = fail`
- required gate pass evidence => may contribute to `completion.requiredGateStatus = pass`
- warning gate missing/fail/warn/skipped evidence => visible warning evidence only
- `completion.status` mirrors `completion.requiredGateStatus`
- `completion.transportStatus = pass` does not override required-gate failure

The active ADL v0.2 schema and fixtures are enforced by
`tests/test_adl_v02_eval_gate_completion.py`.

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
