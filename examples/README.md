# Examples

This directory holds Agent Definition Language (ADL) example documents and
validator fixtures. Two spec generations coexist here on purpose:

- **`examples/*.yaml` (root)** — ADL **v0.1** examples
  (`apiVersion: reddiagent.dev/v0.1`). v0.1 is **superseded** by ADL v0.2
  (`specs/ADL-v0.2.md`), but these files are retained because compatibility
  tooling, dry-run snapshots, and historical reports consume them by path.
  Do not delete, move, or reshape them.
- **`examples/v0.2/`** — the **current canonical examples** for ADL v0.2
  (`specs/ADL-v0.2.md` + `specs/ADL-v0.2.schema.json`). New examples and new
  integrations should start here.
- **`examples/invalid/`** — negative fixtures that validators must reject.
  `bad-*` and other unprefixed files target the v0.1 validator; `adl-v0.2-*`
  files target the v0.2 schema and conformance rules. They are consumed by the
  pytest suites (for example `tests/test_adl_v02_canonical_shape.py` and
  `tests/test_level1.py`).
- **`examples/unsafe/`** — fixtures with unsafe or undeclared capabilities used
  by tool-execution and runtime-safety checks (see
  `tests/test_tool_execution.py`); they are not meant to validate cleanly in
  every lane.

## ADL v0.1 (root, superseded)

| File | Purpose |
| --- | --- |
| `simple-agent.yaml` | Minimal chat agent. |
| `tool-agent.yaml` | Agent with a declared tool. |
| `mcp-readonly-agent.yaml` | Read-only MCP server declaration. |
| `payment-agent.yaml` | v0.1 payment sketch with prose `rule:` policies. Superseded by `v0.2/payment-agent.yaml`, which carries the full v0.2 payment authority contract. |

Validate (the script is hardcoded to `specs/ADL-v0.1.schema.json`; by default it
checks `simple-agent.yaml`, `tool-agent.yaml`, and `payment-agent.yaml`):

```bash
python3 scripts/validate_examples.py
python3 scripts/validate_examples.py examples/mcp-readonly-agent.yaml
```

## ADL v0.2 (`examples/v0.2/`, canonical)

- `simple-agent.yaml` — answers a user question using only model reasoning and a session log.
- `path-agent.yaml` — references reviewed system instructions by relative path.
- `permission-policy-agent.yaml` — structured capability policies for risky agent capabilities.
- `tool-contract-agent.yaml` — tool contract metadata (permissions, side effects, timeouts) and policy linkage.
- `source-boundary-agent.yaml` — canonical data source boundaries and source checks.
- `provider-capability-agent.yaml` — deterministic provider fallback and model capability diagnostics.
- `payment-agent.yaml` — flagship payment example: bounded spend intent on the `x402-dry-run` rail only, full payment authority (principal/spender/maxAmount/currency/rails/expiresAt/revocation/audit), policy-engine-enforced spend policy, receipt binding, reputation signals; conformance Level 3.
- `runtime-local-python-agent.yaml` — local-python runtime descriptor with no network or live activation.
- `runtime-hosted-container-agent.yaml` — hosted-container descriptor for static compatibility review only.
- `runtime-serverless-platform-agent.yaml` — serverless/platform-native descriptor for event-triggered static review.
- `runtime-platform-native-agent.yaml` — platform-native descriptor with deployment-only constraints.
- `memory-observability-agent.yaml` — persistent/external memory metadata and observability without live access.
- `adapter-loss-export-agent.yaml` — strict adapter-loss export metadata for static compatibility review.

Validate and check conformance profiles (schema validation plus Level 0-4
field-set checks, without executing anything):

```bash
python3 scripts/adl_v02_conformance.py examples/v0.2/*.yaml
python3 scripts/adl_v02_conformance.py --requested-level 3 examples/v0.2/payment-agent.yaml
```

All declarations stay static: `paymentAccess=false`, no live rails, no runtime
activation. Live payment rails (`solana`, `base`, `stripe`, `other-x402`) are
vocabulary only and are reported as unsupported until a separately approved
lane exists.

## Full check

```bash
python3 -m pytest tests/ -q
bash tests/smoke-validation.sh
```
