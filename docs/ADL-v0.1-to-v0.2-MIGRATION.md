# Migrating ADL Documents from v0.1 to v0.2

For builders holding ADL v0.1 YAML documents who want them to validate
against `specs/ADL-v0.2.schema.json`. ADL v0.2 is stricter everywhere:
closed vocabularies, structured policies, and fail-closed extension
namespaces. Work through the breaking changes in order, then validate.

## 1. Update `apiVersion`

The version string is a schema `const` — the old value fails immediately.

```yaml
# Before
apiVersion: reddiagent.dev/v0.1
# After
apiVersion: reddiagent.dev/v0.2
```

## 2. `harness.instructions` must be an object

A bare string path is invalid in v0.2. Use an object with exactly one of
`inline` or `path`.

```yaml
# Before (v0.1)
harness:
  instructions: ./prompts/system.md

# After (v0.2)
harness:
  instructions:
    path: ./prompts/system.md
# or
harness:
  instructions:
    inline: "Answer clearly. Say when you are uncertain."
```

## 3. Rewrite free-form policies as the structured policy model

v0.1 policies were `{id, type, rule}` with prose rules. v0.2 requires
`capability`, `subject`, `resource`, `action`, `effect`, `scope`, and
`enforcement` (with optional `limits` and `approval`). Prose `rule` fields
are no longer the contract.

```yaml
# Before (v0.1)
policies:
  - id: no-external-actions
    type: permission
    rule: "The agent may not send messages, spend money, or browse."

# After (v0.2)
policies:
  - id: no-external-actions
    capability: network
    subject: agent
    resource: external-network
    action: connect
    effect: deny
    scope:
      type: task
    enforcement:
      target: static-validator
      phase: before-execution
```

Risky tools, functions, and payment intents must also point at a matching
allow policy via `policyRefs`; the referenced policy's capability, resource,
action, and enforcement target must match the declaration. A nearby policy id
with roughly the right capability is not enough.

## 4. Data sources: aliases removed, boundary fields required

The v0.1 types `document`, `web`, and `knowledge-base` are gone. Rewrite
`document` to `file`, `web` to `url`, and pick a concrete backing type for
`knowledge-base` (`file`, `url`, `api`, `database`, `vector-index`, or `mcp`).
Every source now requires `sourceRef` (prefixed with its type), `trust`,
`citationRequired`, and `sourceCheck`, and each type has exactly one shape
field (`file` uses `path`, `url` uses `url`, etc. — mixing them fails).

```yaml
# Before (v0.1)
dataSources:
  - id: project_docs
    type: document
    description: Project documentation.
    path: docs/handbook.md

# After (v0.2)
dataSources:
  - id: project_docs
    type: file
    description: Reviewed project documentation.
    sourceRef: file:docs/handbook.md
    path: docs/handbook.md
    trust: approved
    citationRequired: true
    sourceCheck:
      required: true
      expectation: approved-source
```

Approved sources must use `expectation: approved-source`; untrusted or
unknown sources must use `manual-review` or `not-citable` and still require
citation and source-check evidence.

## 5. Provider ids and model requirements are closed vocabularies

`model.providers.preferred` and `.fallbacks` accept only `openai`,
`anthropic`, `gemini`, and `ollama`. Model-scoped ids like
`openai:gpt-4.1-mini` fail. `model.requirements` accepts only `toolCalling`,
`structuredOutput`, `streaming`, `jsonMode`, `contextWindow`,
`maxOutputTokens`, and `modalities` (`text`, `image`, `audio`, `embedding`);
any other key fails schema validation.

## 6. Eval gates carry the full completion contract

v0.1 gates were `{id, type, rule}`. v0.2 additionally requires `required`,
`severity`, `appliesTo`, `evidence`, `retryable`, and `onFailure`. Required
gates must block completion and fail closed; warning gates must warn.

```yaml
# Before (v0.1)
evalGates:
  - id: has-answer
    type: output-check
    rule: "Response must include an answer or an uncertainty statement."

# After (v0.2)
evalGates:
  - id: has-answer
    type: output-check
    rule: "Response must include an answer or an uncertainty statement."
    required: true
    severity: error
    appliesTo:
      scope: output
    evidence:
      ref: trace:output.checked
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

## 7. Strict extension namespaces

v0.1 warned on unknown extension namespaces; v0.2 fails them. Only `x402`,
`receipts`, `reputation`, and `identity` are recognized. Anything else must
be prefixed with `x-` or use an `http://`/`https://` URI key.

```yaml
# Before (v0.1) — warned, now fails
extensions:
  payments: { provider: custom }

# After (v0.2)
extensions:
  x-payments: { provider: custom }
```

## 8. x402 spend/refund intents need full authority

Spend-capable or refund-capable intents must now declare `purpose`, `scope`,
an `authority` block (`principal`, `spender`, `maxAmount`, `currency`,
`rails`, `purpose`, `scope`, UTC `expiresAt`, `revocation`, `audit`),
`requireReceipt: true`, `receiptRef`, and `policyRefs` bound to a payment
policy for the exact `x402:intent:<id>` resource. `currency` (`USD`, `USDC`,
`EUR`, `GBP`) and `rails` (`x402-dry-run`, `solana`, `base`, `stripe`,
`other-x402`) are now closed enums; `x402-dry-run` remains the only
report-only compatible rail. See `examples/v0.2/permission-policy-agent.yaml`
and `specs/ADL-v0.2.md` "Extension And Payment Authority Contract".

## 9. Mostly-additive changes to review

- `harness.runtime` still requires only `target`, but the new typed sections
  (`network`, `secretRefs`, `storage`, `scheduler`, `activation`,
  `constraints`) are strict when present, and embedded secret values are
  invalid — use references only.
- `harness.deployment`, `harness.observability`, and `harness.recovery` are
  now fully typed. Observability minimum event sets are conformance-gated per
  level (e.g. Level 1 needs `trace.started`, `trace.completed`,
  `task.completed`, `task.failed`).
- Optional top-level `conformance` block declares `requestedLevel` (0–4).
- Tool contract metadata (`permissions`, `sideEffects`, `timeout`,
  `retryPolicy`, `auditLevel`) is optional, but risky metadata requires
  `policyRefs`, and tool ids must be unique across tools and functions.

## 10. Validate

Run the conformance checker over your migrated documents:

```bash
python3 scripts/adl_v02_conformance.py \
  path/to/your-agent.yaml --requested-level 1

# Options: --requested-level {0,1,2,3,4} (conformance profile to check),
#          --output FILE (write the JSON report to a file)
```

The report includes `requestedLevel`, `achievedLevel`,
`missingFieldsByLevel`, and `forbiddenCapabilitiesByLevel`. Working examples
of every migrated shape live in `examples/v0.2/`.
