# Docker Local/VPS Testing Lane Report

Issue: #249
Parent: #247
Related: #220

`scripts/docker_testing_lane.py` builds deterministic, local-only evidence for a Docker testing lane without pulling images, starting containers, mutating a VPS, accessing credentials, invoking live MCP, calling providers, publishing packages, deploying, or touching devnet/mainnet. The lane records when local Docker is enough versus when VPS Docker is justified, and pins the review contract for images, env vars, network exposure, logs, volumes, teardown, and rollback.

## Evidence

- Scenario source: `tests/fixtures/docker-testing-lane-scenarios.json`
- Generated evidence: `tests/fixtures/docker-testing-lane.json`
- Focused test: `tests/test_docker_testing_lane.py`
- Smoke gate: `tests/smoke-validation.sh`

## Guardrail Coverage

- Positive fixtures: local Docker static evidence and VPS Docker selection evidence.
- Negative fixtures: unpinned image, dependency pull request, host-network/public port exposure, secret env value persistence, credential-like payload leakage, missing cleanup/teardown, devnet/mainnet/live-network flags, production/deployment claims, and wallet/payment/facilitator/settlement requests.
- Boundary assertions: no Docker pull/start, VPS mutation, hosted service use, credential persistence, live MCP invocation, provider/API calls, devnet/mainnet, package publication, deployment, settlement, or spend.

Current outcome: #249 is ready for review as a reproducible testing-environment contract. It is not a live Docker run and does not claim runtime, deployment, settlement, or production readiness.
