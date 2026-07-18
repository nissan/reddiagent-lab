# Provider Adapter Generated-Code Sandbox Beta Report

_Issue: #243. Scope: deterministic local-only provider adapter stub materialization._

## What Landed

- Added `scripts/provider_adapter_generated_code_sandbox_beta.py`, a local-only CLI that requires an explicit output directory and materializes provider adapter stub files from approved ADL and provider manifest fixtures.
- Added `tests/fixtures/provider-adapter-sandbox-policy.json` to pin the provider sandbox policy: hosted provider calls, credential access, network access, dependency installs, and mainnet are all disabled.
- Added pinned positive evidence in `tests/fixtures/provider-adapter-generated-code-sandbox-beta.json`.
- Added `tests/test_provider_adapter_generated_code_sandbox_beta.py` and smoke wiring.

## Evidence Shape

The generated artifact records:

- adapter manifest source, manifest id, planned file count, and source-manifest generation status;
- prompt and model metadata placeholders with `credentialRef=<withheld>` and no raw prompt/task storage;
- budget and eval gate placeholders;
- generated file index with paths, byte counts, and hashes;
- cleanup transcript for the generated package;
- cost evidence with `hostedProviderCalls=0`, `hostedProviderModelApiCalls=false`, and `externalSpendUsd=0`.

## Fail-Closed Coverage

The test covers:

- missing `--output-dir`;
- missing/invalid provider policy fixture;
- valid but unapproved ADL fixture path;
- unapproved adapter manifest fixture path;
- credential request;
- network/provider call request;
- dependency install request;
- unsafe repo output path;
- package directory traversal;
- mainnet request.

## Boundary

No hosted provider/model API call, credential lookup/access/storage, dependency install, live runtime, MCP invocation, wallet/payment rail access, devnet/mainnet run, deployment, package publishing, or write outside the explicit temp output directory is performed.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_provider_adapter_generated_code_sandbox_beta.py
/Users/loki/.pyenv/versions/3.14.3/bin/python3 -m py_compile scripts/provider_adapter_generated_code_sandbox_beta.py tests/test_provider_adapter_generated_code_sandbox_beta.py
PYTHON=/Users/loki/.pyenv/versions/3.14.3/bin/python3 bash tests/smoke-validation.sh
```
