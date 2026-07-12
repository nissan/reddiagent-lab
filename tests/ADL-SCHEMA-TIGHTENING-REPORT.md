# ADL Schema Tightening Report

Issue: #147

This report covers the static ADL schema tightening for `harness.dataSources` and `harness.memory`.

## Scope

- `harness.dataSources` now uses a dedicated `dataSource` schema instead of the generic `namedRef` schema.
- Each data source requires `id`, `type`, and `description`.
- Data source `type` is constrained to reviewed source categories: `document`, `file`, `web`, `api`, `database`, `vector-index`, `mcp`, and `knowledge-base`.
- Optional data source fields are explicit: `sourceRef`, `path`, `url`, and `trust`.
- `harness.memory` now requires `mode` when present and allows only the fields from `specs/MEMORY-CONTRACT-v0.1.md`.
- Persistent or external memory requires both `retention` and `privacyPolicy`.

## Boundary

This is schema, fixture, and validation-guidance work only. It does not activate a runtime, read or write credentials, resolve MCP servers, invoke tools, call external providers, access wallets, use facilitators, touch payment rails, mutate production gateway config, or make paid/model calls.

## Fixtures

- `examples/invalid/bad-data-source.yaml` fails because a data source omits `type`.
- `examples/invalid/bad-memory.yaml` fails because persistent memory omits `privacyPolicy`.

## Validation

- `scripts/validate_examples.py` keeps existing valid examples passing.
- `tests/test_validation_guidance.py` checks builder-facing guidance for the new data-source and memory errors.
- `tests/smoke-validation.sh` now includes `tests/test_validation_guidance.py`.
