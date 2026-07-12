# Smoke and Snapshot CI Report

Issue: #156

## Scope

- Adds `.github/workflows/smoke-snapshots.yml` for pull requests and pushes to `main`.
- Runs Python compilation, example validation, deterministic snapshot checks, and the existing smoke-validation suite.
- Keeps the workflow deterministic and local-only.

## Guardrails

- No provider/model calls.
- No credentials or secrets.
- No live runtime activation.
- No MCP server resolution or invocation.
- No wallet, facilitator, payment rail, settlement, or production gateway configuration.

## Validation

Local validation for this change should include:

```bash
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_snapshots.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/*.py tests/*.py
git diff --check
```

The workflow is intentionally narrower than a full integration pipeline. It checks static/report-only ReddiAgent spec, export, fixture, and validation behavior and skips every live/runtime/provider/payment path by design.
