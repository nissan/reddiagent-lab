# Agent Definition Language v0.2

_Anchor issues: #310, #311._

## Goal

ADL v0.2 keeps ReddiAgent's canonical document shape aligned across prose,
JSON Schema, and checked examples. The v0.2 canonical instruction shape is an
object with either `inline` text or a `path` reference. A bare string path is not
valid ADL v0.2. Permission policies are structured capability declarations so
compatibility checks can fail closed before execution.

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

## Permission Policy Shape

`harness.policies` entries must be machine-readable. ADL v0.2 does not accept
free-form permission prose as the policy contract. Each policy carries:

- `id`: stable policy identifier referenced by risky capabilities.
- `capability`: typed capability, one of `tool`, `network`, `filesystem`,
  `payment`, `messaging`, `human-approval`, `data`, `memory`, or `runtime`.
- `subject`: actor the policy applies to, usually `agent` or `operator`.
- `resource`: resource or capability target, such as `tool:search_docs`,
  `./docs`, `https://docs.reddiagent.dev`, or `x402:intent:review-fee`.
- `action`: operation being allowed or denied, such as `invoke`, `fetch`,
  `read`, `spend`, `send`, or `approve`.
- `effect`: `allow` or `deny`.
- `scope`: bounded scope object with a required `type`.
- `limits`: optional structured limits such as call counts, allowed domains,
  read-only access, maximum spend, receipt requirements, or message counts.
- `approval`: optional approval object. Human approval policies must require
  approval.
- `enforcement`: enforcement target and phase. Supported targets are
  `static-validator`, `runtime-adapter`, `policy-engine`, and `human-review`.

Risky capabilities must reference matching policies where applicable. Tools and
functions use `policyRefs` and must bind to an allow policy whose resource,
action, and enforcement target match the declared tool or function. Payment
intents use `policyRefs` under `extensions.x402.intents` and must bind to a
payment policy for the exact `x402:intent:<id>` resource, direction/action,
limits, receipt requirement, and before-execution policy-engine enforcement.
Unknown, mismatched, or unenforceable capability policy declarations fail
compatibility before execution.

Canonical allow example:

```yaml
harness:
  tools:
    - id: search_docs
      type: function
      description: Search reviewed project documents.
      policyRefs:
        - allow-reviewed-tool
  policies:
    - id: allow-reviewed-tool
      capability: tool
      subject: agent
      resource: tool:search_docs
      action: invoke
      effect: allow
      scope:
        type: task
      limits:
        maxCalls: 5
      approval:
        required: false
        mode: none
      enforcement:
        target: runtime-adapter
        phase: before-execution
```

## Validation Principles

- Missing required top-level, model, or harness fields fail validation.
- Prose examples must validate against the v0.2 JSON Schema.
- Checked examples must use the same object-shaped `harness.instructions`
  contract.
- Shape-divergence fixtures must fail with a clear `harness.instructions`
  validation error.
- Permission policies must use structured capability fields rather than
  free-form prose rules.
- Risky tool, payment, messaging, network, filesystem, and human approval
  declarations must be explicitly bounded by matching enforceable policy, not
  merely any existing policy id with a nearby capability type.
- Unknown capability names and unsupported enforcement targets fail
  compatibility before any execution path.
