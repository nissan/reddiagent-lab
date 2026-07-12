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
- static MCP readiness evidence traces for adapter shape, adapter fixture contract, adapter error semantics, adapter-result aggregation, source, server registry, capability policy, and completion status.

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

## Explicit Non-Goals

- No live retriever.
- No hosted model call.
- No external HTTP call.
- No MCP server invocation.
- No shell command execution.
- No credential lookup.
- No messaging or filesystem mutation tool.
- No live x402 payment or settlement.

## Next Safe Step

The next implementation step should define the static MCP runtime handoff package or connect adapter aggregation evidence into readiness traces. The first live path should only follow after the checklist above is green and the capability has an isolated fail-closed test path.
