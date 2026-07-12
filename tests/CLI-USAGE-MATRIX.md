# CLI Usage Matrix

_Loops 329-353. Anchor issue: #131._

## Scope

This matrix documents the local-python runner behavior that builders and automation can rely on.

It is still local fixture work only. It does not authorize or implement network tools, MCP execution, HTTP calls, shell commands, credentials, messaging, filesystem mutation tools, or live payment behavior.

## Matrix

| Case | Command shape | Exit | Diagnostics | Meaning |
|---|---|---:|---|---|
| Validation error | `run_local_agent.py examples/invalid/bad-tool-id.yaml` | `1` | Text guidance on stdout | ADL is invalid; runner did not execute. |
| Strict denied tool | `run_local_agent.py examples/unsafe/undeclared-tool-fixture.yaml --execute-tools` | `2` | Denial guidance on stderr | Fixture requested a blocked runtime capability. |
| Allowed denied tool report | `run_local_agent.py examples/unsafe/undeclared-tool-fixture.yaml --execute-tools --allow-denied-tools` | `0` | JSON report on stdout | Transport succeeded, but required gates failed. |
| Source-check failure report | `run_local_agent.py examples/unsafe/unapproved-source-fixture.yaml --execute-tools --allow-denied-tools` | `0` | JSON report on stdout | Tool executed, but source trust failed. |
| Required-gate shell failure | `run_local_agent.py examples/unsafe/unapproved-source-fixture.yaml --execute-tools --allow-denied-tools --fail-on-required-gate` | `3` | JSON report on stdout | Automation opted into process failure for incomplete gates. |

## Contract

- Exit `0` only means the runner produced the requested report.
- `completion.status` is the task completion signal.
- `completion.transportStatus = pass` means deterministic local report generation worked.
- `completion.requiredGateStatus = fail` means a required gate blocked task completion.
- Exit `3` is reserved for `--fail-on-required-gate`; it preserves JSON diagnostics.
- Exit `1` and `2` remain validation/runtime-denial failures before report-mode completion.

## Verification

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 tests/test_cli_usage_matrix.py
```

Current expected result:

```text
PASS CLI usage matrix
```
