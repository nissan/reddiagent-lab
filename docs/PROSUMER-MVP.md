# Prosumer MVP Shape

_Loop 54. Anchor issue: #55._

## MVP

The smallest useful prosumer product is not an agent marketplace. It is a guided agent builder that produces a valid ADL file, dry-runs it locally, and shows a trace.

## MVP Flow

1. Choose agent job.
2. Pick model profile.
3. Add optional tool.
4. Add policy and eval gate.
5. Validate ADL.
6. Dry-run locally.
7. Inspect trace.
8. Export report-only review artifacts.

## Current Static Plan

`scripts/prosumer_builder_plan.py` maps the MVP flow onto the current ADL examples:

- `examples/simple-agent.yaml` proves the no-tool local dry-run path.
- `examples/tool-agent.yaml` proves deterministic local fixture execution with `tool.executed`, `source.checked`, source-check summary, and required-gate completion previews.
- `examples/payment-agent.yaml` keeps x402, receipts, and reputation as metadata-only and flags live payment execution as unsupported.
- invalid ADL examples produce a failed validation step and block dry-run/trace preview.

Report-only exports currently point to Agent Spec, A2A Agent Card, Agent Skills / `SKILL.md`, starter manifest, provider compatibility, and RAP bridge checks. The export step includes a `staticUiExportMatrix` so a local UI can render each target's command, readiness state, blockers, metadata-only sections, strict export command where one exists, and authoritative test file.

Matrix readiness states are local/static only:

- `report-ready` for deterministic report commands.
- `metadata-only` when a target can display ReddiAgent semantics but cannot preserve or enforce them losslessly.
- `blocked-before-generation` for starter code review manifests that must not write files yet.
- `blocked-by-validation` when invalid ADL blocks export review.
- `not-applicable` when RAP bridge evidence is irrelevant for an ADL without payment, receipt, or reputation metadata.

The plan does not call model providers, live runtimes, MCP servers, wallets, facilitators, payment rails, or external services.

## Local Validation UI Prototype

`docs/adl-validation-ui.html` is a local/static prototype for the validation step in the MVP flow. It embeds bundled ADL examples, shows validation/report-only results generated from the existing Python validator, and offers browser-only prototype checks for pasted ADL. The authoritative command remains `python3 scripts/validate_examples.py --format json <adl-path>`.

The UI is intentionally not deployed and does not start a server, call providers, invoke MCP, access wallets/payment rails, read credentials, or activate a runtime.

## Non-Goals

- Real payments.
- Real provider execution.
- Marketplace publishing.
- Multi-agent orchestration.
