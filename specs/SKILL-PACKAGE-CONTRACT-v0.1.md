# Skill Package Contract v0.1

_Loop 77. Anchor issue: #91. Updated by issue #134._

## Purpose

Skills package reusable harness capability. The portable package target for this contract is the Agent Skills open format: a directory containing `SKILL.md` with YAML frontmatter plus Markdown instructions, and optional `scripts/`, `references/`, and `assets/` directories.

ReddiAgent remains the canonical ADL and harness contract. Agent Skills / `SKILL.md` is a static package/export target unless a separate runtime adapter is reviewed and approved.

## Agent Skills-Aligned Package Shape

```text
<skill-name>/
  SKILL.md
  scripts/       # optional static declarations
  references/    # optional progressive-disclosure docs
  assets/        # optional templates/resources
```

`SKILL.md` frontmatter:

- `name` (required): lowercase letters, numbers, and hyphens; max 64 chars; matches package directory.
- `description` (required): describes what the skill does and when to use it.
- `license` (optional): short license name or bundled license-file reference.
- `compatibility` (optional): environment/client expectations.
- `metadata` (optional): ReddiAgent namespaced static review metadata.
- `allowed-tools` (optional): experimental static pre-approval hint.

The body carries instructions, examples, edge cases, and relative references to bundled files.

## ReddiAgent Fields

- `id` maps to `name`.
- `version` maps to namespaced metadata or a bundled reference.
- `description` maps to frontmatter `description`.
- `prompts` map to the body or `references/`.
- `tools` map to `allowed-tools`, `scripts/`, or metadata-only notes depending on whether they are bundled static helpers or external tools.
- `dataSources` map to `references/` or metadata-only notes.
- `policies` map to metadata-only notes unless the skill client can enforce them.
- `evalGates` map to metadata-only notes unless the skill client can enforce them.
- `compatibility` maps to frontmatter `compatibility`.

## Static Export Rule

A skill must declare the harness surfaces it modifies. Strict `SKILL.md` export is allowed only when those surfaces can be represented without losing ReddiAgent semantics.

If payment authority, x402, receipts, reputation, MCP invocation, memory behavior, source checks, runtime target, policies, or eval gates cannot be enforced by the target Agent Skills client, the exporter must report them as metadata-only or unsupported and refuse strict lossless export.

All static reports and mapped packages must preserve:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

No Agent Skills client, script, MCP server, wallet, facilitator, payment rail, settlement, credential, network, or runtime path is invoked by this contract.
