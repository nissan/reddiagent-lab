# Error Taxonomy v0.1

_Loop 72. Anchor issue: #82._

## Error Classes

| Class | Meaning | Example |
|---|---|---|
| schema.invalid | ADL does not match JSON Schema | missing harness.instructions |
| compatibility.unsupported | Target cannot support a feature | real settlement on dry-run target |
| policy.denied | Policy blocks an action | payment above approval threshold |
| secret.missing | Required secret reference cannot resolve | OPENAI_API_KEY absent |
| eval.failed | Required eval did not pass | receipt missing |
| runtime.failed | Runner failed after validation | tool timeout |

