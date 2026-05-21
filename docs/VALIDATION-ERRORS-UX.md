# Builder UX Notes for Validation Errors

_Loop 74. Anchor issues: #86/#87._

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

