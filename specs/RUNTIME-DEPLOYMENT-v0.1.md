# Runtime and Deployment v0.1

_Loop 15. Anchor issue: #16._

## Runtime Targets

| Target | Use case | Notes |
|---|---|---|
| local-python | learning, local prototypes | Best first target for prosumers |
| hosted-container | production preview | Portable and inspectable |
| serverless | short bounded tasks | Good for paid specialist tasks |
| platform-native | OpenAI/Bedrock/Gemini/etc | Useful when hosted tools are required |
| openclaw | advanced orchestration | Useful for skills, memory, subagents, channels |

## Deployment Descriptor

Deployment should describe:

- target
- resource limits
- secret references
- network permissions
- storage/memory persistence
- scheduler/event trigger
- observability sink
- rollback strategy

## Compatibility Rule

Runtime adapters must report unsupported features before execution.

## Required Gate Exit Mode

_Loops 304-328. Anchor issue: #131._

The local-python runner supports `--fail-on-required-gate` for automation.

Default behavior:

- emit JSON diagnostics
- return exit code `0` when the dry-run transport succeeds, even if required gates fail

With `--fail-on-required-gate`:

- still emit the same JSON diagnostics to stdout
- return exit code `3` when `completion.status = fail`
- keep schema/validation failures and strict runtime denials on their existing exit codes

This lets humans inspect reports by default while CI or scripts can opt into shell-level failure for incomplete tasks.

## CLI Usage Matrix

_Loops 329-353. Anchor issue: #131._

The local-python runner has an explicit CLI behavior matrix in `tests/CLI-USAGE-MATRIX.md`.

Key exit codes:

- `0`: report generation succeeded; inspect `completion.status`
- `1`: ADL validation failed before execution
- `2`: strict runtime denial failed before report-mode completion
- `3`: `--fail-on-required-gate` converted `completion.status = fail` into shell failure

Automation should use `--fail-on-required-gate` when incomplete required gates must fail the job. Builder-facing local runs can omit it to keep JSON diagnostics report-first.
