# MCP Readiness Release Checklist

_Loops 504-528. Anchor issue: #131._

## Scope

This checklist aggregates the static MCP readiness evidence produced for the local runner readiness bundle.

It is a review artifact only. Passing this checklist does not authorize MCP server invocation, network access, HTTP calls, shell commands, credentials, messaging, filesystem mutation, or live payment behavior.

## Evidence Set

| Gate | Evidence | Test |
|---|---|---|
| Adapter shape | `tests/MCP-ADAPTER-SHAPE-REPORT.md` | `tests/test_adapter_readiness.py` |
| Adapter fixture contract | `tests/MCP-ADAPTER-CONTRACT-REPORT.md` | `tests/test_mcp_adapter_contract.py` |
| Adapter error semantics | `tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md` | `tests/test_mcp_adapter_error_semantics.py` |
| Adapter result aggregation | `tests/MCP-ADAPTER-AGGREGATION-REPORT.md` | `tests/test_mcp_adapter_aggregation.py` |
| Adapter output source check | `tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md` | `tests/test_mcp_adapter_source_check.py` |
| Static server resolution | `tests/MCP-SERVER-RESOLUTION-REPORT.md` | `tests/test_mcp_server_resolution.py` |
| Static capability policy | `tests/MCP-CAPABILITY-POLICY-REPORT.md` | `tests/test_mcp_capability_policy.py` |
| Static readiness trace evidence | `tests/MCP-READINESS-EVIDENCE-REPORT.md` | `tests/test_mcp_readiness_evidence.py` |
| Bundle guard | `docs/LOCAL-RUNNER-READINESS-BUNDLE.md` | `tests/test_readiness_bundle.py` |
| Smoke gate | `tests/smoke-validation.sh` | `bash tests/smoke-validation.sh` |

## Required Review Checks

- [ ] Every MCP ADL declaration uses `serverRef` and `toolName`, not embedded live server fields.
- [ ] Every deterministic MCP adapter fixture has a valid static envelope and source-checkable output shape.
- [ ] MCP adapter errors fail closed with bounded diagnostics, no output payload, and no raw runtime/auth details.
- [ ] MCP adapter aggregation packages use unique result IDs, per-result semantics, and aggregate completion counts before runtime handoff is considered.
- [ ] MCP-shaped outputs pass approved-source checks before task completion can pass.
- [ ] MCP server refs pass static reviewed registry checks before runtime resolution is considered.
- [ ] MCP capability policies grant only `mcp.adapter.readonly`.
- [ ] MCP readiness evidence includes adapter shape, adapter source, server resolution, capability policy, and aggregate completion events.
- [ ] All readiness evidence reports `networkAccess=false`, `mcpInvocation=false`, and `paymentAccess=false`.
- [ ] `tests/smoke-validation.sh` passes.
- [ ] No live MCP server resolution or invocation has been implemented.

## Verification Command

Run this from the repository root:

```bash
bash tests/smoke-validation.sh
```

For a full local review pass, also run:

```bash
python3 -m py_compile scripts/*.py tests/*.py
```

## Review Outcome

Current outcome: static MCP readiness evidence is complete enough for human review of the next implementation boundary.

Next allowed work: define the static MCP runtime handoff package or connect adapter aggregation evidence into readiness traces. Do not resolve or invoke MCP servers yet.
