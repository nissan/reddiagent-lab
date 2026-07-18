# Local Runner Readiness Bundle

_Loops 354-378. Anchor issue: #131._

## Scope

This bundle packages the evidence needed before ReddiAgent Lab moves beyond deterministic local-python runner fixtures.

It is intentionally a rollout gate, not rollout approval for live capabilities. Passing this bundle does not authorize network tools, MCP execution, HTTP calls, shell commands, credentials, messaging, filesystem mutation tools, or live payment behavior.

## Current Capability

The local-python runner can currently prove:

- schema validation for ADL examples;
- deterministic simple and tool dry-runs;
- safe local fixture execution for `search_docs`;
- strict denial for undeclared or unsupported fixture calls;
- report-mode denial diagnostics with builder-facing guidance;
- approved-source pass checks;
- unapproved-source required-gate failure checks;
- completion semantics that separate transport success from task completion;
- optional shell failure with `--fail-on-required-gate`;
- a documented CLI usage matrix for builder and automation behavior;
- static MCP readiness evidence traces for adapter shape, adapter fixture contract, adapter error semantics, adapter-result aggregation, source, server registry, capability policy, and completion status;
- static local runner plugin declarations for deterministic local fixtures only.
- bounded executable local runtime prototype evidence for simple/tool ADL examples and fail-closed unsafe fixtures.
- bounded provider-backed sandbox prototype evidence for fake/local provider budget, eval, and trace gates.
- bounded MCP/devnet payment handoff prototype evidence for reviewed MCP allowlists, devnet-only payment handoff policy, receipt evidence, rollback planning, and mainnet fail-closed semantics.
- beta release readiness evidence for entry/exit criteria, observability, operator controls, rollback, incident notes, and explicit mainnet denial.
- beta local runtime RC gate evidence that merges local runtime execution, operator-control traces, readiness criteria, cost, privacy redaction, rollback stop proof, and mainnet-not-approved language.
- beta operator local dry-run package evidence that binds the RC gate to an operator identity, selected ADL path, operator command transcript, stop/rollback dry-run transcript, and review evidence index.
- local beta review UI evidence that lets an operator inspect runtime package artifacts, traces, metadata, boundary status, rollback cues, and fail-closed findings as a static artifact.
- local beta operator decision package evidence that records approve, hold, and rollback decisions against the selected ADL path, release id, source package, evidence hashes, operator identity, fixture timestamp, rollback cue, and boundary status.

## Evidence Inventory

| Evidence | File | Required signal |
|---|---|---|
| Example schema validation | `scripts/validate_examples.py` | Valid examples pass, invalid examples stay invalid. |
| Tool fixture report | `tests/TOOL-EXECUTION-FIXTURE-REPORT.md` | Local fixture execution, denial, source-check, and completion semantics are documented. |
| Tool fixture assertions | `tests/test_tool_execution.py` | Approved, denied, unapproved source, and fail-on-required-gate paths pass. |
| CLI usage matrix | `tests/CLI-USAGE-MATRIX.md` | Exit codes and diagnostics are documented. |
| CLI usage assertions | `tests/test_cli_usage_matrix.py` | Validation, denial, report-mode, source failure, and required-gate shell failure paths pass. |
| Level 1 report | `tests/LEVEL-1-CONFORMANCE-REPORT.md` | Level 1 includes fixture gate completion evidence. |
| MCP adapter shape report | `tests/MCP-ADAPTER-SHAPE-REPORT.md` | Read-only MCP adapter shape passes and live execution fields fail. |
| MCP adapter contract report | `tests/MCP-ADAPTER-CONTRACT-REPORT.md` | Deterministic MCP fixture envelopes and source-checkable output shape pass/fail before source checks run. |
| MCP adapter error semantics report | `tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md` | Deterministic MCP adapter errors fail closed without output payloads or raw runtime/auth details. |
| MCP adapter aggregation report | `tests/MCP-ADAPTER-AGGREGATION-REPORT.md` | Deterministic MCP adapter result packages pass/fail unique IDs, per-result semantics, and aggregate completion counts before runtime handoff. |
| MCP adapter source-check report | `tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md` | MCP-shaped output fixtures pass/fail approved-source gates deterministically. |
| MCP server resolution report | `tests/MCP-SERVER-RESOLUTION-REPORT.md` | Static server registry fixtures pass/fail fail-closed resolution checks. |
| MCP capability policy report | `tests/MCP-CAPABILITY-POLICY-REPORT.md` | Static capability-policy fixtures pass/fail readonly MCP grants. |
| MCP readiness evidence report | `tests/MCP-READINESS-EVIDENCE-REPORT.md` | Static readiness trace fixtures prove required MCP gates and aggregate completion status. |
| MCP readiness release checklist | `docs/MCP-READINESS-RELEASE-CHECKLIST.md` | Review-ready aggregate checklist keeps MCP evidence and boundaries together. |
| Local runner plugin interface report | `tests/LOCAL-RUNNER-PLUGIN-INTERFACE-REPORT.md` | Static plugin declaration fixtures pass/fail fail-closed capability checks without loading or invoking plugins. |
| Local executable runtime prototype report | `tests/LOCAL-EXECUTABLE-RUNTIME-PROTOTYPE-REPORT.md` | Simple/tool examples execute locally with explicit traces; invalid/unsafe examples fail closed. |
| Provider sandbox prototype report | `tests/PROVIDER-SANDBOX-PROTOTYPE-REPORT.md` | Fake/local provider-backed scenarios record model, prompt, budget, eval, cost, and trace evidence with no hosted provider call. |
| Provider adapter generated-code sandbox beta report | `tests/PROVIDER-ADAPTER-GENERATED-CODE-SANDBOX-BETA-REPORT.md`; `tests/test_provider_adapter_generated_code_sandbox_beta.py` | Local-only adapter stub materialization records manifest, prompt/model placeholders, budget/eval gates, file index, cleanup transcript, and fail-closed provider boundaries. |
| RAP bridge local dry-run report | `tests/RAP-BRIDGE-LOCAL-DRY-RUN-REPORT.md`; `tests/test_rap_bridge_local_dry_run.py` | Local executable RAP bridge prototype binds one run id across trace, receipt, payment handoff, operator transcript, source, budget, rollback, and reputation evidence while fail-closing live rails. |
| Live MCP/devnet handoff prototype report | `tests/LIVE-MCP-DEVNET-HANDOFF-PROTOTYPE-REPORT.md` | Reviewed MCP allowlist and simulated devnet payment handoff scenarios pass while mainnet and unreviewed MCP server refs fail closed. |
| Beta operator-control harness report | `tests/BETA-OPERATOR-CONTROL-HARNESS-REPORT.md` | Local-only enable, disable, pause, local-only, rollback, cost, privacy, and mainnet-denial controls are exercised with fail-closed fixtures. |
| Beta release readiness runbook | `docs/BETA-RELEASE-READINESS-RUNBOOK.md` | Operator-facing beta entry/exit, observability, controls, rollback, cost, safety, privacy, incident, and mainnet denial runbook. |
| Beta release readiness report | `tests/BETA-RELEASE-READINESS-REPORT.md` | Beta entry/exit criteria, observability schema, operator controls, rollback, incident notes, and mainnet denial are machine-checked. |
| Beta local runtime RC gate report | `tests/BETA-LOCAL-RUNTIME-RC-GATE-REPORT.md` | Local runtime execution, operator-control traces, readiness evidence, cost, privacy, rollback, and mainnet denial are merged before a selected ADL path can pass. |
| Beta operator local dry-run package report | `tests/BETA-OPERATOR-DRY-RUN-PACKAGE-REPORT.md` | Operator-facing dry-run package verifies RC evidence, selected ADL path, command transcripts, stop/rollback transcript, and fail-closed beta boundaries. |
| Beta review UI report | `tests/BETA-REVIEW-UI-REPORT.md`; `docs/beta-review-ui.html` | Static local UI renders package metadata, traces/transcripts, evidence hashes, boundary status, rollback cues, and fail-closed findings without live runtime calls. |
| Beta operator decision package report | `tests/BETA-OPERATOR-DECISION-PACKAGE-REPORT.md` | Local operator decision package records approve, hold, and rollback decisions against pinned review/package evidence and fail-closes live, devnet, mainnet, production, and credential-like payload requests. |
| Smoke gate | `tests/smoke-validation.sh` | Readiness-critical checks run together. |

## Verification Commands

Run these from the repository root:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_validation_guidance.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_level1.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_snapshots.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_tool_execution.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_cli_usage_matrix.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_adapter_readiness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_contract.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_error_semantics.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_aggregation.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_adapter_source_check.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_server_resolution.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_capability_policy.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_readiness_evidence.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_readiness_release.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_local_runner_plugin_interface.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_local_runtime_prototype.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_sandbox_prototype.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_rap_bridge_local_dry_run.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_live_mcp_devnet_handoff_prototype.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_operator_control_harness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_release_readiness.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_local_runtime_rc_gate.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_operator_dry_run_package.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_review_ui.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_beta_operator_decision_package.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Rollout Gate Checklist

Before adding any real external tool path, MCP execution, network access, shell execution, or payment behavior, all of these must be true:

- [ ] `tests/smoke-validation.sh` passes.
- [ ] `tests/test_readiness_bundle.py` passes.
- [ ] `--fail-on-required-gate` preserves JSON diagnostics and exits `3` for required gate failure.
- [ ] `completion.status` remains the task-completion signal in every report-mode path.
- [ ] Denied tool paths cannot return payload data.
- [ ] Failed source checks cannot produce `task.dry_run_completed.status = pass`.
- [ ] The new capability has a deterministic negative fixture before any live integration.
- [ ] The new capability documents its boundary in `specs/SECURITY-PERMISSIONS-v0.1.md` or the relevant capability spec.
- [ ] The new capability has a retrospective and STATUS.md resume update.
- [ ] MCP adapter declarations pass read-only shape checks before any server resolution is considered.
- [ ] MCP adapter fixtures pass static envelope and output-shape checks before source checks run.
- [ ] MCP adapter error fixtures fail closed with bounded diagnostics and no output payload data before source checks run.
- [ ] MCP adapter aggregation packages use unique result IDs, per-result pass/error semantics, and aggregate completion counts before runtime handoff is considered.
- [ ] MCP-shaped adapter outputs pass approved-source checks before any task completion path is considered.
- [ ] MCP server references pass static reviewed registry checks before any runtime resolution is considered.
- [ ] MCP tools and server refs pass static readonly capability-policy checks before any runtime resolution is considered.
- [ ] MCP readiness evidence includes all required static gate events and matching aggregate completion status.
- [ ] MCP readiness release checklist has been reviewed before any live MCP work is scoped.
- [ ] RAP bridge local dry-run evidence binds trace, receipt, payment handoff, operator transcript, source, budget, rollback, and reputation to one run id before any live RAP bridge path is scoped.
- [ ] MCP/devnet handoff prototype evidence keeps reviewed allowlists, rollback/cleanup, devnet/mainnet distinction, and secret-redaction assertions green before live infrastructure is touched.
- [ ] Beta operator-control harness evidence proves enable, disable, pause, local-only, rollback, cost, privacy, and mainnet-denial paths before beta runtime use.
- [ ] Beta release readiness evidence covers entry/exit criteria, observability events, operator controls, rollback, incident notes, and explicit `mainnetApproved=false` before any beta runtime is enabled.
- [ ] Beta local runtime RC gate evidence links the selected ADL runtime path to current readiness, operator traces, cost/privacy review, rollback stop evidence, and mainnet-denial proof.
- [ ] Beta operator local dry-run package evidence binds an operator identity, selected ADL path, operator command transcript, stop/rollback dry-run transcript, and artifact evidence index before any beta runtime path is enabled.
- [ ] Beta review UI evidence renders package metadata, local traces/transcripts, evidence hashes, fail-closed findings, and rollback cues from static artifacts only.
- [ ] Beta operator decision package evidence records approve, hold, and rollback decisions with operator identity, fixture timestamp, rollback cue, evidence hashes, and local-only boundary status.

## Explicit Non-Goals

- No live retriever.
- No hosted model call.
- No external HTTP call.
- No MCP server invocation.
- No shell command execution.
- No credential lookup.
- No messaging or filesystem mutation tool.
- No live x402 payment or settlement.
- No mainnet deployment, settlement, or run without separate signoff.

## Next Safe Step

The next implementation step should enable only the smallest reviewed beta runtime path whose readiness fixture, operator dry-run package, negative fixtures, operator controls, and rollback evidence are green. Mainnet remains blocked.
