#!/usr/bin/env python3
"""Check report-only Agent Skills / SKILL.md export output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def run_report(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/adl_to_agent_skill.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/adl_to_agent_skill.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def skill_frontmatter(package: dict) -> dict:
    content = package["files"][0]["content"]
    _, raw_frontmatter, _ = content.split("---", 2)
    return yaml.safe_load(raw_frontmatter)


def assert_static_boundaries(report: dict) -> None:
    assert report["runtimeExecutionAllowed"] is False
    assert report["networkAccess"] is False
    assert report["paymentAccess"] is False
    assert report["mcpInvocation"] is False
    mapped = report["mappedDocument"]
    assert mapped["format"] == "agent-skill-package-review"
    assert mapped["files"][0]["path"].endswith("/SKILL.md")
    frontmatter = skill_frontmatter(mapped)
    assert frontmatter["metadata"]["reddiagent.runtimeExecutionAllowed"] == "false"
    assert frontmatter["metadata"]["reddiagent.networkAccess"] == "false"
    assert frontmatter["metadata"]["reddiagent.paymentAccess"] == "false"
    assert frontmatter["metadata"]["reddiagent.mcpInvocation"] == "false"


def main() -> int:
    reports = run_report("examples/simple-agent.yaml", "examples/payment-agent.yaml")
    by_agent = {report["agent"]: report for report in reports}

    simple = by_agent["simple-research-helper"]
    assert simple["target"] == "agent-skills-skill-md"
    assert simple["supported"] is True
    assert simple["lossless"] is False
    assert simple["unsupportedFeatures"] == []
    assert "model" in simple["metadataOnlyExtensions"]
    assert "harness.memory" in simple["metadataOnlyExtensions"]
    assert "harness.policies" in simple["metadataOnlyExtensions"]
    assert "harness.evalGates" in simple["metadataOnlyExtensions"]
    simple_package = simple["mappedDocument"]
    simple_frontmatter = skill_frontmatter(simple_package)
    assert simple_frontmatter["name"] == "simple-research-helper"
    assert simple_frontmatter["description"].startswith("Answers a user question")
    assert "# ReddiAgent Boundary" in simple_package["files"][0]["content"]
    assert_static_boundaries(simple)

    payment = by_agent["paid-specialist-researcher"]
    assert payment["supported"] is True
    assert payment["lossless"] is False
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    payment_content = payment["mappedDocument"]["files"][0]["content"]
    assert "Payment access is not allowed" in payment_content
    assert_static_boundaries(payment)

    lossy = run_command(
        "--export-skill-package",
        "tests/fixtures/agent-skill-lossy-agent.yaml",
    )
    assert lossy.returncode == 3
    assert lossy.stdout == ""
    refusal = json.loads(lossy.stderr)
    assert refusal["error"] == "agent_skill_export_would_drop_reddi_semantics"
    assert refusal["runtimeExecutionAllowed"] is False
    assert refusal["networkAccess"] is False
    assert refusal["paymentAccess"] is False
    assert refusal["mcpInvocation"] is False
    assert "extensions.x402" in refusal["diagnostics"][0]["metadataOnlyExtensions"]
    assert "live_payment_execution" in refusal["diagnostics"][0]["unsupportedFeatures"]
    assert "mcp_runtime_invocation" in refusal["diagnostics"][0]["unsupportedFeatures"]

    exported = run_command(
        "--export-skill-package",
        "--single",
        "tests/fixtures/agent-skill-lossless-agent.yaml",
    )
    assert exported.returncode == 0
    package = json.loads(exported.stdout)
    assert package["skillDirectory"] == "lossless-skill-agent"
    assert package["files"][0]["path"] == "lossless-skill-agent/SKILL.md"
    frontmatter = skill_frontmatter(package)
    assert frontmatter["name"] == "lossless-skill-agent"
    assert frontmatter["license"] == "Apache-2.0"
    assert frontmatter["allowed-tools"] == "Read"
    assert frontmatter["metadata"]["reddiagent.metadataOnlySections"] == "[]"
    assert "references/TAXONOMY.md" in package["files"][0]["content"]

    exported_yaml = run_command(
        "--export-skill-package",
        "--output-format",
        "yaml",
        "--single",
        "tests/fixtures/agent-skill-lossless-agent.yaml",
    )
    assert exported_yaml.returncode == 0
    assert "skillDirectory: lossless-skill-agent" in exported_yaml.stdout
    assert "lossless-skill-agent/SKILL.md" in exported_yaml.stdout

    print("PASS Agent Skills SKILL.md export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
