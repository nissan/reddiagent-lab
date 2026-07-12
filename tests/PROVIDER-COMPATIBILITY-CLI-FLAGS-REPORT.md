# Provider Compatibility CLI Flags Report

_Issue: #146. Scope: report-only provider compatibility CLI ergonomics._

## What Changed

- `scripts/provider_compatibility.py` now supports explicit target selection with repeated `--target`.
- `--agent` filters by ADL `metadata.name`.
- Positional ADL paths restrict input files.
- `--format json|summary` chooses the deterministic JSON export or a human-readable summary.
- `--output <path>` writes the static report to a local file.
- `--list-targets` prints available report-only targets.
- `mcp-readonly` is now a static compatibility target for MCP declaration review only.

## Boundary

The CLI remains report-only. It reads local ADL YAML and writes local report output. It does not:

- call OpenAI, Anthropic, Gemini, LangGraph, Ollama, or any other provider;
- resolve or invoke MCP servers;
- activate a runtime;
- read credentials;
- touch wallets, facilitators, payment rails, settlement, production gateway config, or live cron definitions;
- make paid/model calls.

Every compatibility row continues to report:

```json
{
  "runtimeExecutionAllowed": false,
  "networkAccess": false,
  "paymentAccess": false,
  "mcpInvocation": false
}
```

## Validation

Run locally on 2026-07-12 AEST:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_compatibility_cli.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_snapshots.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py --agent mcp-readonly-docs --target openai --target anthropic --target mcp-readonly
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/provider_compatibility.py examples/simple-agent.yaml --target local-python --format summary
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_compatibility.py tests/test_provider_compatibility_cli.py
bash tests/smoke-validation.sh
git diff --check
```

All validation passed after correcting a test assertion that had guessed the simple fixture name.
