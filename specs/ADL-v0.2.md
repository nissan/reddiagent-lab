# Agent Definition Language v0.2

_Anchor issue: #310._

## Goal

ADL v0.2 keeps ReddiAgent's canonical document shape aligned across prose,
JSON Schema, and checked examples. The v0.2 canonical instruction shape is an
object with either `inline` text or a `path` reference. A bare string path is not
valid ADL v0.2.

## Top-Level Shape

```yaml
apiVersion: reddiagent.dev/v0.2
kind: Agent
metadata:
  name: research-assistant
  description: Answers questions using approved sources.
model:
  capability: chat
  providers:
    preferred: openai
    fallbacks: [anthropic, gemini, ollama]
  requirements:
    toolCalling: true
    structuredOutput: true
harness:
  instructions:
    path: ./prompts/system.md
  tools: []
  functions: []
  skills: []
  dataSources: []
  memory:
    mode: session
  policies: []
  evalGates: []
  runtime:
    target: local-python
  deployment: {}
  observability: {}
  recovery: {}
extensions: {}
```

## Field Contract

The field contract below is intentionally machine checked against
`specs/ADL-v0.2.schema.json`.

```json
{
  "topLevel": {
    "required": ["apiVersion", "kind", "metadata", "model", "harness"],
    "optional": ["extensions"]
  },
  "model": {
    "required": ["capability", "providers", "requirements"],
    "optional": ["cost"]
  },
  "harness": {
    "required": ["instructions", "runtime"],
    "optional": [
      "tools",
      "functions",
      "skills",
      "dataSources",
      "memory",
      "policies",
      "evalGates",
      "deployment",
      "observability",
      "recovery"
    ]
  }
}
```

## Instruction Shape

`harness.instructions` must be an object. It must contain exactly one source:

- `inline`: non-empty instruction text embedded in the ADL document.
- `path`: non-empty path to an instruction file relative to the ADL document.

The following shape is canonical:

```yaml
harness:
  instructions:
    path: ./prompts/system.md
```

This legacy shape is invalid in v0.2:

```yaml
harness:
  instructions: ./prompts/system.md
```

## Validation Principles

- Missing required top-level, model, or harness fields fail validation.
- Prose examples must validate against the v0.2 JSON Schema.
- Checked examples must use the same object-shaped `harness.instructions`
  contract.
- Shape-divergence fixtures must fail with a clear `harness.instructions`
  validation error.
