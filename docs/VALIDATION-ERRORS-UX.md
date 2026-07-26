# Builder UX Notes for Validation Errors

_Updated during loops 84-103. Anchor issues: #110-#130._

## Principle

Validation errors should tell the builder what to fix, not expose raw schema jargon first.

## Example

Raw:

    harness: 'instructions' is a required property

Builder-facing:

    Add harness.instructions. This tells the agent what job it is allowed to perform and how it should behave.

## UX Rules

- Show file path.
- Show failing section.
- Explain why it matters.
- Provide a minimal valid snippet.
- Link to the tutorial that uses the same concept.

## Formatter Contract

The validation formatter turns every JSON Schema failure into a builder guidance item:

- problem: a short diagnosis in plain language.
- location: the ADL path to edit.
- why_it_matters: the product reason the field exists.
- fix: the smallest safe repair.
- snippet: a minimal YAML example.
- reference: the most relevant spec, tutorial, or contract.
- raw_message: the original schema message for debugging.

CLI usage:

    python3 scripts/validate_examples.py
    python3 scripts/validate_examples.py --format raw examples/invalid/missing-instructions.yaml
    python3 scripts/validate_examples.py --format json examples/invalid/missing-instructions.yaml

Default output is builder-facing text. Raw schema output remains available for implementers, and JSON output is intended for future UI/CI integration.

## Covered Error Families

- Missing agent instructions.
- Unsupported model capability.
- Unsupported runtime target.
- Invalid tool identifiers.
- Duplicate fallback providers.
- Invalid x402 payment intent rails.
