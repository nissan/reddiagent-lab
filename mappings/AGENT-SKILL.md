# ADL to Agent Skills / SKILL.md Mapping

_Issue: #134. Status: report-only._

## Boundary

Agent Skills / `SKILL.md` is a portable capability package target, not a ReddiAgent runtime target. This mapping never installs, activates, resolves, or executes a skill. Static outputs must report:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`

## Target Shape

The target package follows the Agent Skills open format:

```text
<skill-name>/
  SKILL.md
  scripts/       # optional, static declaration only
  references/    # optional, static declaration only
  assets/        # optional, static declaration only
```

`SKILL.md` has YAML frontmatter with `name` and `description` required. Optional frontmatter fields are `license`, `compatibility`, `metadata`, and experimental `allowed-tools`. The Markdown body carries activation instructions and references to bundled files.

## Field Mapping

| ADL field | SKILL.md target | Status |
|---|---|---|
| `metadata.name` | frontmatter `name`, slug-normalized | supported |
| `metadata.description` | frontmatter `description` | supported |
| `harness.instructions.inline` | Markdown body | supported |
| `harness.instructions.path` | Markdown body file reference | metadata-only unless the file is bundled |
| `extensions.agentSkills.license` | frontmatter `license` | supported |
| `extensions.agentSkills.compatibility` | frontmatter `compatibility` | supported |
| `extensions.agentSkills.allowedTools` | frontmatter `allowed-tools` | supported as experimental static text |
| `extensions.agentSkills.toolDeclarations` | frontmatter metadata and Markdown tool declarations | supported as static package declarations only |
| `extensions.agentSkills.usageNotes` | frontmatter metadata and Markdown usage notes | supported |
| `extensions.agentSkills.constraints` | frontmatter metadata and Markdown constraints | supported |
| `extensions.agentSkills.references` | Markdown body references | supported as static package declarations |
| `extensions.agentSkills.scripts` | Markdown body script references | supported as static package declarations only |
| `extensions.agentSkills.assets` | Markdown body asset references | supported as static package declarations only |
| `model.*` | frontmatter metadata | metadata-only |
| `harness.tools` | frontmatter/body metadata | metadata-only unless represented as bundled scripts |
| `harness.dataSources` | frontmatter/body metadata | metadata-only |
| `harness.memory` | frontmatter/body metadata | metadata-only |
| `harness.policies` | frontmatter/body metadata | metadata-only |
| `harness.evalGates` | frontmatter/body metadata | metadata-only |
| `harness.runtime` | frontmatter/body metadata | metadata-only |
| `extensions.x402` | frontmatter metadata | metadata-only; live payment unsupported |
| `extensions.receipts` | frontmatter metadata | metadata-only |
| `extensions.reputation` | frontmatter metadata | metadata-only |
| MCP declarations | frontmatter/body metadata | metadata-only; invocation unsupported |

## Lossless Export Rule

Strict `SKILL.md` export is allowed only when the ADL can be represented without losing ReddiAgent semantics. Any field that the Agent Skills format cannot enforce, such as payment authority, MCP invocation policy, eval gates, source checks, memory behavior, or runtime target semantics, makes the export lossy and must be refused with diagnostics.

The report may still include a mapped static review package for lossy inputs. That package is evidence for humans, not an executable runtime installation.
