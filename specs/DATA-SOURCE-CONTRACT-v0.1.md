# Data Source Contract v0.1

_Loop 75. Anchor issues: #88/#89._

## Purpose

Data sources describe what the harness can read or retrieve.

## Fields

- id
- type: file, url, api, database, vector-index, mcp
- description
- accessPolicy
- freshness
- citationRequired
- persistence

## Rule

Data sources are harness resources. They should not be hidden inside prompt text.

## Approved Local Fixture Sources

_Loop 179-203. Anchor issue: #131._

The first local source-check fixture uses a project-owned approved source list inside `scripts/local_tool_registry.py`.

Current approved sources:

- `ReddiAgent ADL v0.1` -> `specs/ADL-v0.1.md`
- `Tool Registry Contract v0.1` -> `specs/TOOL-REGISTRY-v0.1.md`
- `Harness Lifecycle v0.1` -> `specs/HARNESS-LIFECYCLE-v0.1.md`

Runner source checks must not treat arbitrary tool output as trusted. A fixture output passes only when both title and URL match this approved in-repo list.

## Unapproved Local Fixture Source

_Loop 204-228. Anchor issue: #131._

`unsafe_source_docs` is a deterministic local fixture used only to prove the negative path. It returns:

- `Unapproved External Source` -> `https://example.invalid/reddiagent`

This source is intentionally absent from the approved list, so the runner must report `sourceChecks.status = fail` even though the local tool execution itself reports `status = success`.

## Source-Check Repair Guidance

_Loop 229-253. Anchor issue: #131._

When a local fixture returns an unapproved source, the runner must include repair guidance in the failed `sourceChecks` entry. The guidance should make the boundary explicit:

- A successful fixture call proves execution only.
- Source trust is a separate gate.
- Unreviewed external URLs are not accepted as evidence.
- The immediate repair is to return an approved in-repo source, or add a reviewed project-owned source with tests.

Minimal approved output example:

```yaml
output:
  title: Tool Registry Contract v0.1
  url: specs/TOOL-REGISTRY-v0.1.md
```

## MCP Adapter Output Source Checks

_Loops 404-428. Anchor issue: #131._

MCP-shaped adapter output is not trusted by transport alone. A future MCP runtime must pass the same `approved-source-output` gate before task completion.

Current deterministic fixtures:

- `tests/fixtures/mcp-approved-output.json` returns `Tool Registry Contract v0.1` and passes.
- `tests/fixtures/mcp-unapproved-output.json` returns `Unreviewed MCP Source` and fails with builder-facing guidance.

The check is local JSON-only. It does not call MCP servers, network APIs, live retrievers, shell commands, credentials, or payment systems.
