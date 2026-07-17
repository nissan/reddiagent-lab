# Starter Code Plan Report

_Issues: #168, #174, #184, #185, and #197. Scope: static/report-only starter code generator plan, dry-run file manifest fixtures, template contract fixtures, safety policy fixtures, and preview bundle fixtures._

## Summary

- Added `scripts/starter_code_plan.py`, a deterministic manifest command that maps ADL examples to a starter-code review artifact.
- The command emits planned file paths, target layout metadata, model/tool summaries, validation status, blocked pre-generation gates, and explicit non-goals.
- Added `dryRunFileManifest` fixture summaries plus `tests/fixtures/starter-code-dry-run-file-manifest.json` so the simple/tool/payment dry-run file manifests are losslessly pinned for review.
- Added `templateContracts` plus `tests/fixtures/starter-code-template-contracts.json` so planned starter templates are pinned by template id, planned path, required input refs, blocked gates, and non-goals without rendering templates.
- Added `starterSafetyPolicy` plus `tests/fixtures/starter-code-safety-policy.json` so ready static review and unsafe generation requests are pinned before a generator can write files.
- Added `previewBundle` plus `tests/fixtures/starter-code-preview-bundles.json` so planned files, template contracts, blocked gates, safety policy state, and fail-closed live/unsafe claims are bundled for UI/reviewer preview without writing starter files.
- The manifest is intentionally not a generator: it does not write files, install dependencies, run providers, resolve MCP servers, activate runtimes, or touch payment rails.

## Static Boundary

Every manifest preserves:

- `runtimeExecutionAllowed=false`
- `networkAccess=false`
- `paymentAccess=false`
- `mcpInvocation=false`
- `writesFiles=false`
- `installsDependencies=false`

## Coverage

- `examples/simple-agent.yaml` proves a minimal local Python starter manifest can be reviewed without tools or payments.
- `examples/tool-agent.yaml` proves deterministic local tool fixtures are represented as review-only fixture files.
- `examples/payment-agent.yaml` proves non-local runtime and x402/payment semantics are blocked behind explicit review gates.
- `examples/invalid/missing-instructions.yaml` proves invalid ADL fails closed and produces no planned starter files.
- `tests/fixtures/starter-code-dry-run-file-manifest.json` pins dry-run file path lists, status counts, validation status, blocked gate ids, and non-goal ids for the simple/tool/payment examples.
- `tests/fixtures/starter-code-template-contracts.json` pins template ids, planned template paths, required input refs, status counts, template non-goals, and validation status for the simple/tool/payment examples.
- `tests/fixtures/starter-code-safety-policy.json` pins a ready static-review request plus unsafe policy ids for dependency installs, external network/tool execution, MCP invocation, provider/model/local-model execution, credential/private material, wallet/payment/settlement access, deployment, and production config mutation.
- `tests/fixtures/starter-code-preview-bundles.json` pins starter preview bundle summaries for the simple/tool/payment examples, including planned paths, template contract ids, blocked gate ids, denied unsafe policy ids, and fail-closed flags.

## Validation

- `tests/test_starter_code_plan.py`
- `python3 scripts/starter_code_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml`
- `python3 scripts/starter_code_plan.py --single examples/invalid/missing-instructions.yaml` returns exit `1`
- `tests/smoke-validation.sh`

## Non-Goals

- No runnable starter project generation.
- No starter template rendering.
- No preview bundle may claim live execution, file writes, dependency installs, unsafe policy allowance, or successful invalid ADL generation.
- No dependency install or framework scaffold.
- No unsafe starter-generation request is allowed by the safety policy fixture.
- No provider/model call, local model probe, MCP invocation/resolution, credential lookup, wallet/facilitator/payment rail/settlement, deployment, or paid/model test call.
