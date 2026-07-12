# Adapter Interface v0.1

_Loop 53. Anchor issue: #54._

## Purpose

Adapters translate ADL into a provider/runtime compatibility report and, later, executable code.

## Required Methods

- load(adl)
- validate()
- compatibility_report(target)
- compile(target)
- dry_run(target)

## First Rule

Adapters must report compatibility before generating code.

## Output Contract

Compatibility output follows specs/PROVIDER-COMPATIBILITY-REPORT-v0.1.md.

## Read-Only Shape Checks

_Loops 379-403. Anchor issue: #131._

The first adapter check is a read-only shape check, not a compiler or runtime.

For MCP, `scripts/adapter_readiness.py` verifies that an ADL file declares named MCP server references without embedding live execution fields. It reports:

- `mode = read-only-adapter-shape`
- `networkAccess = false`
- `mcpInvocation = false`
- `paymentAccess = false`

Failing readiness means the adapter cannot proceed to any live runtime step.
