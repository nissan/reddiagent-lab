# Validation Guidance v0.1

_Loops 84-103. Anchor issues: #110-#130._

## Purpose

ReddiAgent validation must be useful to builders who are learning the abstraction. A failing ADL file should identify the exact field, explain why the field matters, and show a minimal valid repair.

## Guidance Item

Each formatted error contains:

- location: dot path to the ADL field or section.
- problem: plain-language diagnosis.
- why_it_matters: product and safety rationale.
- fix: minimal recommended action.
- snippet: valid YAML fragment.
- reference: relevant spec, tutorial, or contract.
- raw_message: original JSON Schema message.

## Initial Coverage

- harness.instructions
- model.capability
- harness.runtime.target
- harness.tools
- model.providers.fallbacks
- extensions.x402.intents

## Non-Goals

- No schema contract change.
- No web UI yet.
- No automatic repair writing to the source file.

## Next Expansion

- Add source line/column numbers.
- Add multiple-error grouping by section.
- Add machine-readable severity and category fields.
- Feed JSON output into a minimal validator UI.

