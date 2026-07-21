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
  `payment`, `messaging`, `shell`, `human-approval`, `data`, `memory`, or
  `runtime`.
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
functions use `policyRefs` and must bind to an allow policy whose capability,
resource, action, and enforcement target match the declared tool or function.
Plain tools default to `capability: tool`, `resource: tool:<id>`, and
`action: invoke`; tools that model another risky capability, such as external
messaging, declare that capability, resource, and action explicitly. Payment
intents use `policyRefs` under `extensions.x402.intents` and must bind to a
payment policy for the exact `x402:intent:<id>` resource, direction/action,
limits, receipt requirement, and before-execution policy-engine enforcement.
Unknown, mismatched, or unenforceable capability policy declarations fail
compatibility before execution.

## Tool Contract Metadata

ADL v0.2 tool declarations may include static contract metadata so validators
and adapters can fail closed before invoking a tool:

- `permissions`: normalized capability tags requested by the tool. Supported
  values are `tool`, `network`, `payment`, `shell`, `filesystem`, `messaging`,
  `mcp`, and `mutation`.
- `sideEffects`: bounded effect metadata with required `mode`. Supported modes
  are `none`, `read`, `write`, `network`, `payment`, `messaging`, `shell`,
  `filesystem`, `mcp`, and `multiple`, with optional `mutatesState`,
  `external`, and `resources`.
- `timeout`: execution budget with required `seconds` and optional
  `behavior` of `fail-closed`, `cancel`, or `retry`.
- `retryPolicy`: retry contract with required `maxAttempts`, optional
  `backoff`, and optional `retryOn` error labels.
- `auditLevel`: one of `none`, `metadata`, `event`, `payload-redacted`, or
  `full`.

Safe fixture tools may declare `permissions: [tool]`, `sideEffects.mode: none`,
and no `policyRefs`. Mutating, network, payment, shell, filesystem, messaging,
and MCP tools must declare explicit `policyRefs`; a nearby policy is not enough.
Tool IDs must be unique across `harness.tools` and `harness.functions` so the
harness cannot bind a policy reference to the wrong implementation.

Canonical allow example:

```yaml
harness:
  tools:
    - id: search_docs
      type: function
      description: Search reviewed project documents.
      permissions:
        - network
      sideEffects:
        mode: network
        external: true
        resources:
          - https://docs.reddiagent.dev
      timeout:
        seconds: 10
        behavior: fail-closed
      retryPolicy:
        maxAttempts: 1
        backoff: none
      auditLevel: payload-redacted
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

## Data Source Boundary Contract

ADL v0.2 uses one canonical `harness.dataSources[*].type` vocabulary:

- `file`: local or packaged file/document content. Legacy `document` aliases
  must be rewritten to `file`.
- `url`: citable web URL content. Legacy `web` aliases must be rewritten to
  `url`.
- `api`: reviewed API endpoint metadata.
- `database`: reviewed database connection metadata.
- `vector-index`: reviewed retrieval index metadata.
- `mcp`: MCP-shaped output metadata. This is a static source boundary and does
  not permit live MCP invocation.

The legacy `knowledge-base` alias is not valid in ADL v0.2. Builders must
choose the concrete backing type (`file`, `url`, `api`, `database`,
`vector-index`, or `mcp`) so adapters do not invent source semantics.

Every data source carries a source-boundary declaration:

- `sourceRef`: stable typed reference using the same prefix as `type`, such as
  `file:docs/source.md`, `url:https://docs.example.test/page`,
  `api:catalog`, `database:readonly-warehouse`, `vector-index:docs`, or
  `mcp:approved-docs-search`.
- `trust`: `approved`, `untrusted`, or `unknown`.
- `citationRequired`: whether output may complete without a citation to this
  source.
- `sourceCheck`: fail-closed source-check expectation with `required`,
  `expectation`, and optional `gateRef`.

Each source type has exactly one shape field:

- `file` requires `path`.
- `url` requires `url`.
- `api` requires `api.endpoint` and `api.method`.
- `database` requires `database.engine` and `database.connectionRef`.
- `vector-index` requires `vectorIndex.indexRef`.
- `mcp` requires `mcp.serverRef` and `mcp.outputShape`.

Source shape fields are mutually exclusive. A `file` source with `url`, an
`api` source with `path`, or a `sourceRef` prefix that does not match `type`
fails validation before compatibility reporting. `untrusted` and `unknown`
sources must still require citation and source-check evidence; they remain
review-visible and cannot silently become trusted completion evidence.

Canonical data source examples:

```yaml
harness:
  dataSources:
    - id: project_docs
      type: file
      description: Reviewed local project documentation.
      sourceRef: file:docs/ADL-v0.2.md
      path: specs/ADL-v0.2.md
      trust: approved
      citationRequired: true
      sourceCheck:
        required: true
        expectation: approved-source
        gateRef: approved-source-output
    - id: public_docs
      type: url
      description: Reviewed public documentation URL.
      sourceRef: url:https://docs.reddiagent.dev/adl
      url: https://docs.reddiagent.dev/adl
      trust: approved
      citationRequired: true
      sourceCheck:
        required: true
        expectation: approved-source
    - id: catalog_api
      type: api
      description: Reviewed read-only catalog API.
      sourceRef: api:catalog
      api:
        endpoint: https://api.example.test/catalog
        method: GET
      trust: approved
      citationRequired: true
      sourceCheck:
        required: true
        expectation: approved-source
    - id: local_index
      type: vector-index
      description: Reviewed local documentation index.
      sourceRef: vector-index:docs
      vectorIndex:
        indexRef: indexes/docs
        embeddingModel: text-embedding-metadata-only
      trust: approved
      citationRequired: true
      sourceCheck:
        required: true
        expectation: approved-source
    - id: docs_mcp_output
      type: mcp
      description: MCP-shaped docs output inspected without live invocation.
      sourceRef: mcp:approved-docs-search
      mcp:
        serverRef: approved-docs-search
        toolName: search
        outputShape: source-citable-output
      trust: approved
      citationRequired: true
      sourceCheck:
        required: true
        expectation: approved-source
```

## Eval Gate Completion Contract

ADL v0.2 eval gates define the task completion contract before a runtime,
adapter, or exporter treats work as complete. Each `harness.evalGates` entry
carries:

- `id`: stable gate identifier used by traces, receipts, and conformance
  reports.
- `type`: one of `output-check`, `source-check`, `tool-check`,
  `budget-check`, `receipt-check`, or `human-review`.
- `rule`: human-readable rule summary.
- `required`: whether this gate must pass before task completion.
- `severity`: `error` or `critical` for required gates; `info` or `warning`
  for non-blocking gates.
- `appliesTo`: scoped target for the gate, with `scope` set to `task`,
  `output`, `tool`, `source`, `budget`, `receipt`, or `human-review`, and an
  optional `targetRef`.
- `evidence`: required evidence reference and JSON Schema. Missing evidence
  for a required gate uses the fail-closed default status. Required gate
  results must include the declared evidence reference; missing or mismatched
  evidence references do not satisfy completion.
- `retryable`: whether the harness may retry after this gate fails.
- `onFailure`: completion behavior. Required gates must use
  `completion: block` and `defaultStatus: fail`; warning gates must use
  `completion: warn`.

Completion is computed from gate results, not from dry-run transport success.
If any required gate is missing, `fail`, or otherwise not `pass`, the task
completion status is `fail`. Non-required gates remain visible in traces and
receipts but cannot block completion. Existing local dry-run semantics remain:
`completion.transportStatus = pass` only means deterministic validation and
reporting completed; `completion.requiredGateStatus` and `completion.status`
carry the task completion result.

Missing evidence for a required gate uses the fail-closed default status.
Required gate results must include the declared evidence reference.
Non-required gates remain visible in traces and receipts but cannot block completion.
`completion.transportStatus = pass` only means deterministic validation and reporting completed.

Canonical required gate example:

```yaml
harness:
  evalGates:
    - id: approved-source-output
      type: source-check
      rule: "Outputs must cite an approved source before completion."
      required: true
      severity: error
      appliesTo:
        scope: source
        targetRef: tool:search_docs
      evidence:
        ref: trace:source.checked
        schema:
          type: object
          required: [status]
          properties:
            status:
              enum: [pass, fail]
      retryable: false
      onFailure:
        completion: block
        defaultStatus: fail
        visibility: trace-and-receipt
```

Canonical warning gate example:

```yaml
harness:
  evalGates:
    - id: preferred-summary-style
      type: output-check
      rule: "Output should include a concise summary."
      required: false
      severity: warning
      appliesTo:
        scope: output
      evidence:
        ref: trace:output.style_checked
        schema:
          type: object
          required: [status]
          properties:
            status:
              enum: [pass, warn, fail]
      retryable: true
      onFailure:
        completion: warn
        defaultStatus: warn
        visibility: trace
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
- Required eval gates fail closed when evidence is missing or failing; warning
  gates remain visible and non-blocking.
- Data source aliases fail validation in ADL v0.2; adapters and reports must
  use only the canonical `file`, `url`, `api`, `database`, `vector-index`, and
  `mcp` vocabulary.
- Source boundary declarations must match their source type, trust state,
  citation requirement, and source-check expectation before compatibility or
  export surfaces can treat a source as usable.
