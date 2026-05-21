# ReddiAgent Domain Model v0.1

_Loop 5. Anchor issue: #5._

## Core Model

    ReddiAgent
    - AgentDefinition
    - ModelProfile
    - Harness
    - Extensions

## Entities

| Entity | Purpose | Required in v0.1 |
|---|---|---|
| AgentDefinition | Top-level portable description | Yes |
| ModelProfile | Capability/constraint description of model needs | Yes |
| Harness | Runtime behavior around the model | Yes |
| Tool | External action with typed input/output | Optional |
| Function | Pure or bounded callable capability | Optional |
| Skill | Reusable capability bundle | Optional |
| DataSource | Knowledge, API, file, database, vector index, or stream | Optional |
| Memory | Persistent or session-scoped state | Optional |
| Policy | Permission, budget, safety, privacy, and operating rules | Yes |
| EvalGate | Acceptance or stop criteria | Optional but recommended |
| Runtime | Local, hosted, serverless, container, platform-native | Yes |
| DeploymentTarget | Where the harness runs | Optional |
| PaymentRail | Settlement option such as Solana, Base, Stripe, or other x402 rail | Optional |
| Receipt | Evidence of work/payment/result | Optional |
| ReputationSignal | Attestation derived from behavior, result, receipt, or review | Optional |
| Identity | Agent/user/org identity and signing context | Optional |

## Boundary Rules

- ModelProfile describes what model capability is needed; it should not contain provider secrets.
- Harness owns tools, state, permissions, evals, deployment, and recovery behavior.
- Payment/reputation is an extension, not a mandatory core dependency.
- Runtime targets may reject unsupported harness features but must report incompatibility clearly.

## v0.1 Non-Goals

- No universal runtime implementation.
- No on-chain reputation design in this repo.
- No single framework lock-in.
- No guarantee that every ADL file compiles to every platform.

