#!/usr/bin/env python3
"""Static local runner plugin interface checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_checker(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/local_runner_plugin_interface.py", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    ready = run_checker("tests/fixtures/local-runner-plugin-ready.json")
    assert ready.returncode == 0, ready.stderr
    ready_doc = json.loads(ready.stdout)
    assert ready_doc["status"] == "pass"
    assert ready_doc["mode"] == "static-local-runner-plugin-interface"
    assert ready_doc["runtimeExecutionAllowed"] is False
    assert ready_doc["networkAccess"] is False
    assert ready_doc["paymentAccess"] is False
    assert ready_doc["mcpInvocation"] is False
    assert ready_doc["externalExecutionAllowed"] is False
    assert ready_doc["pluginLoaded"] is False
    assert ready_doc["pluginInvoked"] is False
    assert ready_doc["issues"] == []

    unsafe = run_checker("tests/fixtures/local-runner-plugin-unsafe.json")
    assert unsafe.returncode == 1
    unsafe_doc = json.loads(unsafe.stdout)
    assert unsafe_doc["status"] == "fail"
    assert unsafe_doc["runtimeExecutionAllowed"] is False
    assert unsafe_doc["networkAccess"] is False
    assert unsafe_doc["paymentAccess"] is False
    assert unsafe_doc["mcpInvocation"] is False
    assert unsafe_doc["pluginLoaded"] is False
    assert unsafe_doc["pluginInvoked"] is False
    messages = {issue["path"]: issue["message"] for issue in unsafe_doc["issues"]}
    assert messages["plugin.mode"] == "Only deterministic-local-fixture mode is allowed."
    assert messages["plugin.entrypoint.kind"] == "Entrypoint kind is not allowed."
    assert messages["capabilities.networkAccess"] == "Capability must be false."
    assert messages["capabilities.shellAccess"] == "Capability must be false."
    assert messages["capabilities.credentialAccess"] == "Capability must be false."
    assert messages["capabilities.paymentAccess"] == "Capability must be false."
    assert messages["capabilities.mcpInvocation"] == "Capability must be false."
    assert messages["boundaries.runtimeExecutionAllowed"] == "Execution boundary must be false."
    assert messages["boundaries.externalExecutionAllowed"] == "Execution boundary must be false."
    assert messages["fixtureContract.deterministic"] == "Fixture contract must be deterministic."
    assert messages["fixtureContract.approvedSourcesOnly"] == "Fixture outputs must use approved sources only."
    assert messages["fixtureContract.sideEffects"] == "Fixture side effects must be none."
    assert messages["plugin.entrypoint.command"] == "Plugin declaration embeds a live execution field."
    assert messages["plugin.entrypoint.endpoint"] == "Plugin declaration embeds a live URL."
    assert messages["plugin.entrypoint.env"] == "Plugin declaration embeds a live execution field."
    assert messages["paymentRail"] == "Plugin declaration embeds a live execution field."
    assert messages["wallet"] == "Plugin declaration embeds a live execution field."

    print("PASS local runner plugin interface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
