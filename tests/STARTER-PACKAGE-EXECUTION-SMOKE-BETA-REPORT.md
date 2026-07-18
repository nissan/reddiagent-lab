# Starter Package Execution Smoke Beta

Issue #244 adds a deterministic local execution smoke for generated starter packages.

## Evidence

- Command: `scripts/starter_code_plan.py --execution-smoke-beta --output-dir <temp-dir> examples/simple-agent.yaml`
- Pinned normalized artifact: `tests/fixtures/starter-package-execution-smoke-beta.json`
- Focused test: `tests/test_starter_package_execution_smoke_beta.py`
- Smoke validation: `tests/smoke-validation.sh`

The smoke generates the starter package inside a dedicated system temp directory, runs only generated in-package Python checks from the generated package root, and emits command transcript, trace evidence, eval evidence, budget evidence, generated file manifest, and cleanup transcript.

## Positive Coverage

- `tests/test_static_contract.py`
- `tests/test_policy_eval_gates.py`
- `src/agent_harness.py`

All commands run with local Python, no dependency install, no network request, no provider/model call, no MCP invocation, no wallet/payment/settlement access, no devnet/mainnet, no deployment, and no write outside the explicit temp output.

## Fail-Closed Coverage

`tests/test_starter_package_execution_smoke_beta.py` verifies local failures for:

- missing `--output-dir`
- missing generated package under `--output-dir`
- unsafe non-temp working directory
- unsafe path traversal
- attempted package path outside temp output
- invalid ADL
- dependency install request
- provider/model call request
- live MCP request
- live payment request
- mainnet request
