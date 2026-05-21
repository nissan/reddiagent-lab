# Retrospective - Loops 2-8 Foundation Pass

_Date: 2026-05-21_

## Loops

- Loop 2 / issue #2: framework matrix.
- Loop 3 / issue #3: platform-native matrix.
- Loop 4 / issue #4: homebrew/open-source matrix.
- Loop 5 / issue #5: domain model v0.1.
- Loop 6 / issue #6: ADL v0.1.
- Loop 7 / issue #7: payment/reputation extension v0.1.
- Loop 8 / issue #8: prosumer builder journey.

## Acceptance Checks

- [x] Foundation research matrices exist.
- [x] Domain model exists.
- [x] ADL prose spec exists.
- [x] Payment/reputation extension exists.
- [x] Builder journey exists.
- [x] STATUS.md updated.

## What Changed

- Regular Python tool-calling became a core baseline, not a side note.
- Platform-native lock-in needs explicit ADL compatibility reporting.
- Payment and reputation should stay extension-namespaced until the ADL core stabilizes.

## Decisions

- ReddiAgent should compile toward frameworks/platforms but be defined above them.
- The harness is the main product surface; the model is one replaceable dependency.
- Prosumer education should start with one useful job, one model profile, one tool, one policy, and one eval.

## Plan Adjustments

- Add concrete examples before deeper schema work.
- Add provider mapping, lifecycle, eval, runtime, security, observability, conformance, glossary, and roadmap loops.

## Next Loop Recommendation

- Create examples/simple-agent.yaml as the first concrete ADL artifact.

