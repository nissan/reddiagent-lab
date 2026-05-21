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

