# Starter Code Generation Beta Report

Issue: #242

## Scope

`scripts/starter_code_plan.py --generate-beta --output-dir <temp-dir> <adl>` now writes a deterministic local starter package under the explicit output directory only.

## Positive Evidence

- Pinned normalized artifact: `tests/fixtures/starter-code-generation-beta.json`
- Positive ADL: `examples/simple-agent.yaml`
- Generated package files:
  - `README.md`
  - `agent.adl.yaml`
  - `src/agent_harness.py`
  - `tests/test_static_contract.py`
  - `.env.example`
  - `tests/test_policy_eval_gates.py`
- The generated static contract and deterministic harness both run locally with Python only.

## Fail-Closed Evidence

`tests/test_starter_code_generation_beta.py` verifies local failures for:

- missing `--output-dir`
- unsafe `--package-dir ../escape`
- invalid ADL validation
- dependency install request
- provider/model call request
- live MCP request
- live payment request
- mainnet request

## Boundary

No dependency install, provider/model/API call, credential access, live MCP, wallet/payment rail, devnet/mainnet, deployment, package publishing, production gateway mutation, or write outside the explicit temp output directory is performed.
