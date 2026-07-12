# Local Runner Plugin Interface v0.1

_Anchor issue: #148._

## Purpose

The local runner plugin interface defines a reviewed declaration shape for future local runner extensions without enabling external execution.

This interface is a static contract only. A declaration can describe deterministic local fixture behavior, but the runner must not import, load, invoke, resolve, install, or execute a plugin from this contract.

## Declaration Shape

A plugin declaration is a JSON document with:

- `schemaVersion`: `local-runner-plugin.v0.1`
- `plugin.id`: stable identifier
- `plugin.name`: human-readable name
- `plugin.mode`: `deterministic-local-fixture`
- `plugin.entrypoint`: metadata-only local fixture reference
- `plugin.tools`: declared local fixture tools
- `capabilities`: all runtime capability flags set to `false`
- `boundaries`: all execution boundary flags set to `false`
- `fixtureContract`: deterministic fixture requirements

Allowed `entrypoint.kind` values:

- `python-function`
- `static-fixture`

The entrypoint is descriptive metadata. It is not an import hook.

## Required False Capabilities

Every reviewed declaration must include:

- `networkAccess = false`
- `shellAccess = false`
- `credentialAccess = false`
- `paymentAccess = false`
- `mcpInvocation = false`
- `filesystemMutation = false`

Every reviewed declaration must also include:

- `runtimeExecutionAllowed = false`
- `externalExecutionAllowed = false`

## Fail-Closed Fields

Static checks fail closed if any declaration embeds live execution fields, including:

- `url`
- `endpoint`
- `serverUrl`
- `command`
- `args`
- `env`
- `headers`
- `token`
- `apiKey`
- `secret`
- `credential`
- `wallet`
- `privateKey`
- `facilitator`
- `paymentRail`

Static checks also fail closed if any string value contains an `http://` or `https://` URL.

## Fixture Contract

`fixtureContract` must declare:

- `deterministic = true`
- `approvedSourcesOnly = true`
- `sideEffects = none`

This keeps local fixtures compatible with the existing `--execute-tools` path while preserving the current no-external-execution boundary.

## Report Boundary

`scripts/local_runner_plugin_interface.py` performs static declaration checks only. Reports always include:

- `runtimeExecutionAllowed = false`
- `networkAccess = false`
- `paymentAccess = false`
- `mcpInvocation = false`
- `externalExecutionAllowed = false`

No plugin is imported, loaded, invoked, installed, resolved, or executed by this checker.
