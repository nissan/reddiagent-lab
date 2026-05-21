# Evaluation Gates v0.1

_Loop 14. Anchor issue: #15._

## Purpose

Eval gates decide whether the harness can mark work complete.

## Gate Types

| Type | Purpose | Example |
|---|---|---|
| output-check | Validate response shape or content | Must include answer and uncertainty note |
| source-check | Validate citations or source use | Must cite approved source |
| tool-check | Validate tool behavior | Tool call stayed within allowed domain |
| budget-check | Validate spend | Spend <= 0.25 USDC |
| receipt-check | Validate economic/evidence metadata | Receipt exists and hashes match |
| human-review | Require human approval | Approval required above threshold |

## Gate Result

Each gate returns:

- id
- status: pass, fail, warn, skipped
- evidence
- message
- retryable

## Completion Rule

Required gates must pass before task completion. Warning gates can complete but should be visible in traces and receipts.

