# Prosumer Builder Journey

_Loop 8. Anchor issue: #8._

## Goal

Help a prosumer move from "I want an agent" to "I can build, run, evaluate, and improve one."

## One-Hour Path

1. Pick one useful job.
2. Choose a default model profile.
3. Add one tool.
4. Add one data source or memory mode.
5. Add one safety/budget policy.
6. Run locally.
7. Inspect trace/log output.
8. Add one eval gate.
9. Package the definition.
10. Optional: add payment/reputation extension.

## Learning Stages

| Stage | Builder question | ReddiAgent artifact |
|---|---|---|
| Idea | What job should this agent do? | metadata.description |
| Model | What model capability is needed? | model |
| Harness | What does the model need around it? | harness |
| Tools | What actions can it take? | tools/functions |
| Data | What does it know or retrieve? | dataSources/memory |
| Policy | What can it not do? | policies |
| Eval | How do I know it worked? | evalGates |
| Runtime | Where does it run? | runtime/deployment |
| Economics | Can it pay/get paid/prove work? | extensions.x402/receipts/reputation |

## Teaching Principle

Every concept should be explainable as a simple Python loop first, then upgraded into framework/platform targets.

