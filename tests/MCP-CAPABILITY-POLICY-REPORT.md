# MCP Capability Policy Report

_Loops 454-478. Anchor issue: #131._

## Scope

This report defines static capability-policy checks for MCP tools and server refs.

It does not authorize or implement MCP server invocation, network access, HTTP calls, shell commands, credentials, messaging, filesystem mutation, or live payment behavior.

## Static Policy Contract

Every MCP ADL tool must have a matching static capability policy keyed by:

- `serverRef`
- `toolId`
- `toolName`

The only currently allowed capability is:

- `mcp.adapter.readonly`

The policy must also declare:

- `sourceGate = approved-source-output`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`

## Fixtures

Positive fixture:

- `tests/fixtures/mcp-capability-policy-approved.json`
- result: pass

Negative fixtures:

- `tests/fixtures/mcp-capability-policy-empty.json`
- result: fail because the MCP tool has no matching static capability policy

- `tests/fixtures/mcp-capability-policy-overbroad.json`
- result: fail because the policy grants `network.fetch`, `payment.spend`, disables the required source gate, and enables live access flags

## Decision

MCP capability policy must be explicit before any runtime can resolve or invoke a server. Tool shape, source checks, and server registry entries are not enough by themselves; the capability grant must be narrow and readonly.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_mcp_capability_policy.py
```

Current expected result:

```text
PASS MCP capability policy
```
