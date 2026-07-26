# Schema Changelog

_Loop 71. Anchor issue: #81._

## 2026-07-22 — ADL v0.2: observability, x402 hardening, examples (#331–#334)

- **Additive.** Observability minimums: `harness.observability` gains typed
  `events`, `summaries`, `destinations`, `evidenceRefs`, `traceRef`,
  `retention`, `redaction`, `receipts`, and `exports`. Minimum required event
  sets are cumulative per conformance level (Level 1 `trace.started` through
  Level 4 `adapter.loss.reported`); missing required events are conformance
  failures, not schema failures. (#331)
- **Breaking (spend/refund intents).** x402 authority schema hardening:
  spend-capable or refund-capable `extensions.x402.intents[*]` must now declare
  `purpose`, `scope`, `authority` (with `principal`, `spender`, `maxAmount`,
  `currency`, `rails`, `purpose`, `scope`, `expiresAt`, `revocation`, `audit`),
  `requireReceipt: true`, `receiptRef`, and `policyRefs`. `currency` and
  `rails` are now closed enums (`USD`/`USDC`/`EUR`/`GBP`;
  `x402-dry-run`/`solana`/`base`/`stripe`/`other-x402`). Receipt declarations
  bind via `extensions.receipts.refs`. (#332, #333)
- **Additive.** Checked `examples/v0.2/` set (12 positive examples plus
  invalid fixtures) and stable machine-readable validation diagnostics with
  category, path, line, and column. (#334)

## 2026-07-21 — ADL v0.2: contracts and vocabulary tightening (#325–#330)

- **Breaking (when tools declare risky metadata).** Tool contract metadata +
  policy linkage: tools/functions may declare `permissions`, `sideEffects`,
  `timeout`, `retryPolicy`, and `auditLevel`. Mutating, network, payment,
  shell, filesystem, messaging, and MCP tools must declare explicit
  `policyRefs` bound to a matching allow policy; tool IDs must be unique
  across `harness.tools` and `harness.functions`. (#325)
- **Breaking.** Eval-gate completion contract: `harness.evalGates` entries now
  require `required`, `severity`, `appliesTo`, `evidence`, `retryable`, and
  `onFailure` in addition to v0.1's `id`/`type`/`rule`. Completion is computed
  from gate results, fail-closed on missing evidence. (#326)
- **Breaking.** Source-boundary vocabulary: data-source aliases `document`,
  `web`, and `knowledge-base` are removed (`file`/`url` are canonical).
  `dataSources` entries now require `sourceRef` (type-prefixed), `trust`,
  `citationRequired`, and `sourceCheck`; shape fields are mutually exclusive
  per type. (#327)
- **Additive.** Conformance-level field mapping: optional top-level
  `conformance` block and the Level 0–4 profile matrix mapping required field
  sets and evidence outputs per level. (#328)
- **Breaking.** Provider capability constraints: `model.providers.*` is now a
  closed provider-id enum (`openai`, `anthropic`, `gemini`, `ollama`) and
  `model.requirements` is a closed vocabulary (`toolCalling`,
  `structuredOutput`, `streaming`, `jsonMode`, `contextWindow`,
  `maxOutputTokens`, `modalities`). Unknown provider ids or requirement keys
  fail schema validation. (#329)
- **Additive (strict when present).** Runtime/deployment descriptor
  normalization: `harness.runtime` gains typed `network`, `secretRefs`,
  `storage`, `scheduler`, `activation`, and `constraints`; `harness.deployment`
  and `harness.recovery` mirror the same typed boundary. Embedded secret
  values are invalid; declarations remain report-only. (#330)

## 2026-07-20 — ADL v0.2: canonical shape and policy model (#321–#324)

- **Breaking.** Canonical shape normalization: `apiVersion` is
  `reddiagent.dev/v0.2`; `harness.instructions` must be an object with exactly
  one of `inline` or `path` — the legacy bare-string form fails validation.
  The prose field contract is machine-checked against the schema. (#321)
- **Breaking.** Structured permission/capability policy model:
  `harness.policies` entries replace free-form `type`/`rule` prose with
  required `capability`, `subject`, `resource`, `action`, `effect`, `scope`,
  and `enforcement` (plus optional `limits`/`approval`). Unknown capabilities
  and unenforceable targets fail closed. (#322)
- **Breaking.** policyRef compatibility binding: risky capabilities must bind
  to an allow policy whose capability, resource, action, and enforcement
  target match; a nearby policy id is not enough. (#324)
- **Breaking.** Source-boundary/extension strictness baseline: unknown
  extension namespaces fail schema validation unless prefixed with `x-` or an
  `http(s)://` URI key; v0.1's warn-only strict mode is gone. (#321)

## 2026-05-22

- Added ADL v0.1 JSON Schema.
- Added policy type enum.
- Added eval gate type enum.
- Added extension namespace registry.
- Added invalid example for missing harness instructions.
- Added builder-facing validation guidance without changing the ADL schema contract.
- Added invalid fixture examples for unsupported model capability, unsupported runtime target, invalid tool id, duplicate fallback providers, and invalid x402 rails.
- scripts/validate_examples.py now defaults to builder-facing text while preserving --format raw and adding --format json for UI/CI consumers.

## Compatibility

Current valid examples still pass after policy/eval enum tightening.
