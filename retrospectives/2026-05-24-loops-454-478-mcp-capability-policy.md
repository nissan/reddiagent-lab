# Retrospective: Loops 454-478 MCP Capability Policy

## Scope

Define capability-policy checks for MCP tools and server refs using deterministic fixtures only.

## Changed

- Added `tests/fixtures/mcp-capability-policy-approved.json`.
- Added `tests/fixtures/mcp-capability-policy-empty.json`.
- Added `tests/fixtures/mcp-capability-policy-overbroad.json`.
- Added `scripts/mcp_capability_policy_check.py`.
- Added `tests/test_mcp_capability_policy.py`.
- Added `tests/MCP-CAPABILITY-POLICY-REPORT.md`.
- Wired MCP capability-policy checks into `tests/smoke-validation.sh`.
- Updated MCP mapping, security, conformance, readiness bundle, roadmap, and index docs.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_capability_policy.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_readiness_bundle.py
bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
```

## Decision

MCP tool shape, source checks, and static server registry entries are not enough by themselves. A matching static capability policy must grant only `mcp.adapter.readonly`, require `approved-source-output`, and keep network, invocation, and payment access false.

## Next

Define trace/evidence requirements for MCP readiness gates using deterministic fixtures only. Do not resolve or invoke MCP servers yet.
