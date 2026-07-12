#!/usr/bin/env python3
"""Check provider compatibility report CLI selectors and output modes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_cli(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/provider_compatibility.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def test_target_agent_selection_covers_provider_and_mcp_paths() -> None:
    proc = run_cli(
        [
            "--agent",
            "mcp-readonly-docs",
            "--target",
            "openai",
            "--target",
            "anthropic",
            "--target",
            "mcp-readonly",
        ]
    )
    reports = json.loads(proc.stdout)
    assert [item["target"] for item in reports] == ["openai", "anthropic", "mcp-readonly"]
    assert {item["agent"] for item in reports} == {"mcp-readonly-docs"}

    for item in reports:
        assert item["boundary"] == {
            "runtimeExecutionAllowed": False,
            "networkAccess": False,
            "paymentAccess": False,
            "mcpInvocation": False,
        }
        assert item["supported"] is False
        assert item["unsupportedFeatures"] == ["mcp_execution"]
        assert item["requiredHostedServices"] == ["mcp:approved-docs-search"]

    assert reports[0]["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert reports[1]["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert reports[2]["requiredSecrets"] == []


def test_local_python_selector_and_summary_output_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "provider-summary.txt"
        proc = run_cli(
            [
                "examples/simple-agent.yaml",
                "--target",
                "local-python",
                "--format",
                "summary",
                "--output",
                str(output),
            ]
        )
        assert proc.stdout == ""
        text = output.read_text()

    assert "Provider compatibility report (report-only)" in text
    assert "simple-research-helper -> local-python" in text
    assert "supported=true level=1" in text
    assert "runtimeExecutionAllowed=false" in text


def test_no_matching_agent_fails_before_empty_report() -> None:
    proc = run_cli(["--agent", "missing-agent"], check=False)
    assert proc.returncode == 1
    assert "No ADL examples matched" in proc.stderr
    assert proc.stdout == ""


def test_list_targets_includes_mcp_readonly() -> None:
    proc = run_cli(["--list-targets"])
    targets = proc.stdout.splitlines()
    assert "openai" in targets
    assert "anthropic" in targets
    assert "local-python" in targets
    assert "mcp-readonly" in targets


def main() -> int:
    test_target_agent_selection_covers_provider_and_mcp_paths()
    test_local_python_selector_and_summary_output_file()
    test_no_matching_agent_fails_before_empty_report()
    test_list_targets_includes_mcp_readonly()
    print("PASS provider compatibility CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
