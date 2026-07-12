# MCP Tool Mapping v0.1

_Loop 35. Anchor issue: #37._

## Purpose

MCP is a natural transport for ReddiAgent tools because it separates tool servers from model providers.

## ADL Shape

    tools:
      - id: search_docs
        type: mcp
        description: Search approved documentation
        serverRef: docs-search
        toolName: search

## Rules

- MCP server references must be named, not embedded secrets.
- Runtime must verify the server is available before execution.
- Tool schema should be imported into the compatibility report.
- Permissions still live in harness.policies.
- Local readiness checks are read-only shape checks. They must not invoke MCP servers.
- MCP ADL declarations should use `serverRef` and `toolName`.
- Live execution fields such as `serverUrl`, `command`, `env`, `headers`, `token`, `apiKey`, `secret`, or `credential` fail adapter readiness until a reviewed runtime owns resolution.

## Compatibility

MCP tools should map well to Anthropic and OpenClaw style harnesses, and can be wrapped for OpenAI/Gemini targets when the runtime owns the MCP client.

## Read-Only Adapter Shape

_Loops 379-403. Anchor issue: #131._

Read-only MCP adapter readiness is documented in `tests/MCP-ADAPTER-SHAPE-REPORT.md` and enforced by `tests/test_adapter_readiness.py`.

Positive fixture:

- `examples/mcp-readonly-agent.yaml`
- one MCP tool with named `serverRef` and `toolName`
- no network, MCP invocation, payment, shell, credential, messaging, or filesystem access

Negative fixture:

- `examples/unsafe/mcp-live-server-fixture.yaml`
- fails because it embeds `serverUrl`, `command`, and `env`

This keeps MCP as an adapter shape until a future runtime can prove fail-closed server resolution and source checks.

## Adapter Output Source Checks

_Loops 404-428. Anchor issue: #131._

Hypothetical MCP adapter output must satisfy the same source gate as local fixture tools before task completion.

Deterministic fixtures:

- `tests/fixtures/mcp-approved-output.json` passes `approved-source-output`
- `tests/fixtures/mcp-unapproved-output.json` fails `approved-source-output`

Verification lives in `tests/test_mcp_adapter_source_check.py` and `tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md`.

This still does not resolve or invoke an MCP server. It only checks output-shaped JSON fixtures.

## Static Server Resolution Checks

_Loops 429-453. Anchor issue: #131._

MCP server resolution must fail closed before any runtime can invoke a server.

A valid readiness registry entry must include:

- `resolutionMode = static-reviewed`
- `allowedTools`
- `sourceGate = approved-source-output`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`

Deterministic fixtures:

- `tests/fixtures/mcp-server-registry-approved.json` passes
- `tests/fixtures/mcp-server-registry-empty.json` fails missing `serverRef`
- `tests/fixtures/mcp-server-registry-live.json` fails live resolution fields

Verification lives in `tests/test_mcp_server_resolution.py` and `tests/MCP-SERVER-RESOLUTION-REPORT.md`.

This still does not resolve or invoke an MCP server. It only checks static config.

## Static Capability Policy Checks

_Loops 454-478. Anchor issue: #131._

MCP tools and server refs require an explicit static capability policy before any runtime resolution is considered.

The only allowed capability today is:

- `mcp.adapter.readonly`

Deterministic fixtures:

- `tests/fixtures/mcp-capability-policy-approved.json` passes
- `tests/fixtures/mcp-capability-policy-empty.json` fails missing policy
- `tests/fixtures/mcp-capability-policy-overbroad.json` fails overbroad live capabilities

Verification lives in `tests/test_mcp_capability_policy.py` and `tests/MCP-CAPABILITY-POLICY-REPORT.md`.

This still does not resolve or invoke an MCP server. It only checks static capability policy.

## Static Readiness Evidence Checks

_Loops 479-503. Anchor issue: #131._

MCP readiness evidence must prove every static readiness gate ran before completion is considered:

- adapter shape
- adapter output source check
- static server resolution
- static capability policy
- aggregate readiness completion

Deterministic fixtures:

- `tests/fixtures/mcp-readiness-evidence-pass.json` passes
- `tests/fixtures/mcp-readiness-evidence-fail.json` fails missing server-resolution evidence, live access, and mismatched completion status

Verification lives in `tests/test_mcp_readiness_evidence.py` and `tests/MCP-READINESS-EVIDENCE-REPORT.md`.

This still does not resolve or invoke an MCP server. It only checks static trace/evidence completeness.

## Release Checklist

_Loops 504-528. Anchor issue: #131._

The static MCP readiness evidence is aggregated in `docs/MCP-READINESS-RELEASE-CHECKLIST.md` and guarded by `tests/test_mcp_readiness_release.py`.

The checklist is the review artifact before any future live MCP work is scoped. It keeps adapter shape, source checks, static server registry, capability policy, readiness evidence, smoke validation, and explicit non-goals in one place.
