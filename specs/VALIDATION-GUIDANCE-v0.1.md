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

## Runtime Denial Guidance

_Loop 154-178. Anchor issue: #131._

Some builder problems are schema-valid but runtime-denied. These are not JSON Schema validation failures, but they should still explain the issue in builder-facing language.

Denied local tool fixture guidance contains:

- tool_id: denied tool identifier.
- problem: plain-language denial reason.
- why_it_matters: safety or portability rationale.
- fix: minimal safe repair.
- snippet: valid YAML fragment.
- reference: relevant spec.

Initial runtime-denial coverage:

- undeclared fixture tool ID.
- declared but unsupported local fixture tool.

Strict mode prints denial guidance to stderr and exits with code 2. `--allow-denied-tools` includes the same guidance in each denied result for conformance tests.
