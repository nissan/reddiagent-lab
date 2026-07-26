#!/usr/bin/env python3
"""Check report-only Microsoft Agent Framework compatibility output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

REQUIRED_REPORT_KEYS = {
    "agent",
    "source",
    "target",
    "supported",
    "lossless",
    "structuralErrors",
    "warnings",
    "supportedRequirements",
    "unsupportedRequirements",
    "degradedRequirements",
    "metadataOnlyExtensions",
    "lossMetadata",
    "pinned",
    "runtimeExecutionAllowed",
    "networkAccess",
    "paymentAccess",
    "mcpInvocation",
}
OPTIONAL_REPORT_KEYS = {"mafPromptYaml", "mafPromptYamlOmitted"}
PINNED = {"package": "agent-framework", "range": ">=1.12,<2", "factory": "ChatClientPromptAgentFactory"}
DEFAULT_SOURCES = [
    "examples/v0.2/simple-agent.yaml",
    "examples/v0.2/tool-contract-agent.yaml",
    "examples/v0.2/payment-agent.yaml",
    "examples/v0.2/delegation-research-agent.yaml",
]


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/maf_compatibility.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_single(path: str) -> dict:
    proc = run_command("--single", path)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def loss_codes(report: dict) -> set[str]:
    return {item["code"] for item in report["lossMetadata"]}


def degraded_by_requirement(report: dict) -> dict:
    return {item["requirement"]: item for item in report["degradedRequirements"]}


def assert_report_shape(report: dict) -> None:
    keys = set(report)
    assert REQUIRED_REPORT_KEYS <= keys, sorted(REQUIRED_REPORT_KEYS - keys)
    assert keys - REQUIRED_REPORT_KEYS <= OPTIONAL_REPORT_KEYS, sorted(keys - REQUIRED_REPORT_KEYS)
    # Exactly one of the prompt-export keys is present.
    assert ("mafPromptYaml" in keys) != ("mafPromptYamlOmitted" in keys)
    assert report["target"] == "maf"
    assert report["pinned"] == PINNED
    assert report["runtimeExecutionAllowed"] is False
    assert report["networkAccess"] is False
    assert report["paymentAccess"] is False
    assert report["mcpInvocation"] is False


def test_simple_agent_supported_but_not_lossless() -> None:
    report = run_single("examples/v0.2/simple-agent.yaml")
    assert_report_shape(report)
    assert report["agent"] == "simple-research-helper"
    assert report["supported"] is True
    assert report["lossless"] is False
    assert report["structuralErrors"] == []
    assert report["unsupportedRequirements"] == []

    supported = {item["requirement"] for item in report["supportedRequirements"]}
    assert {"metadata.name", "metadata.description", "harness.instructions.inline", "model.providers.preferred"} <= supported

    degraded = degraded_by_requirement(report)
    assert degraded["harness.policies"]["degradedTo"] == "function-approval-middleware"
    assert degraded["harness.evalGates"]["degradedTo"] == "foundry-external"
    assert degraded["model.requirements.structuredOutput"]["degradedTo"] == "empty-output-schema-slot"
    assert "harness.memory" in report["metadataOnlyExtensions"]

    codes = loss_codes(report)
    assert "adl-has-no-output-schema" in codes
    assert "maf-approval-middleware-lacks-policy-semantics" in codes
    schema_loss = next(item for item in report["lossMetadata"] if item["code"] == "adl-has-no-output-schema")
    assert "#389" in schema_loss["detail"]


def test_simple_agent_prompt_yaml_export() -> None:
    report = run_single("examples/v0.2/simple-agent.yaml")
    prompt = yaml.safe_load(report["mafPromptYaml"])
    assert prompt["kind"] == "Prompt"
    assert prompt["name"] == "simple-research-helper"
    assert prompt["displayName"] == "simple-research-helper"
    assert prompt["description"]
    assert prompt["instructions"].startswith("Answer clearly.")
    assert prompt["model"]["connection"]["kind"] == "OpenAI"
    # ADL has no concrete model id/endpoint; both defer to PowerFx =Env.* refs.
    assert prompt["model"]["id"].startswith("=Env.")
    assert prompt["model"]["connection"]["endpoint"].startswith("=Env.")


def test_payment_and_delegation_reports() -> None:
    for path in ("examples/v0.2/payment-agent.yaml", "examples/v0.2/delegation-research-agent.yaml"):
        report = run_single(path)
        assert_report_shape(report)
        assert report["supported"] is True
        assert report["lossless"] is False

        assert {"extensions.x402", "extensions.receipts", "extensions.reputation"} <= set(
            report["metadataOnlyExtensions"]
        ), path
        unsupported = {item["requirement"]: item["reason"] for item in report["unsupportedRequirements"]}
        assert unsupported == {
            "extensions.x402": "maf-has-no-payment-surface",
            "extensions.receipts": "maf-has-no-receipt-surface",
            "extensions.reputation": "maf-has-no-reputation-surface",
        }, path

        degraded = degraded_by_requirement(report)
        assert degraded["harness.policies"]["degradedTo"] == "function-approval-middleware", path
        assert degraded["harness.evalGates"]["degradedTo"] == "foundry-external", path
        assert degraded["harness.observability"]["degradedTo"] == "otel-advisory", path
        assert "maf-has-no-payment-surface" in loss_codes(report), path

        # Core quartet still maps: inline instructions + openai connector.
        assert "mafPromptYaml" in report, path


def test_mcp_and_non_declarative_tools() -> None:
    report = run_single("examples/v0.2/tool-contract-agent.yaml")
    assert_report_shape(report)
    assert report["supported"] is True

    supported_tools = {
        item["requirement"]: item for item in report["supportedRequirements"] if "toolType" in item
    }
    assert supported_tools["harness.tools.list_mcp_fixture"]["toolType"] == "mcp"
    assert "MCP" in supported_tools["harness.tools.list_mcp_fixture"]["mafTarget"]
    assert supported_tools["harness.tools.normalize_topic"]["toolType"] == "function"
    # MAF MCP support never flips the static-review boundary.
    assert report["mcpInvocation"] is False

    degraded = degraded_by_requirement(report)
    assert degraded["harness.tools.fetch_approved_url"]["degradedTo"] == "code-first-function-tool"
    assert degraded["harness.tools.run_local_check"]["degradedTo"] == "code-first-function-tool"
    assert "maf-no-declarative-tool-type" in loss_codes(report)


def test_path_instructions_omit_prompt_yaml() -> None:
    report = run_single("examples/v0.2/path-agent.yaml")
    assert_report_shape(report)
    assert report["supported"] is True
    assert report["mafPromptYamlOmitted"] == {"reason": "instructions-path-ref-not-inlined"}
    degraded = degraded_by_requirement(report)
    assert degraded["harness.instructions.path"]["degradedTo"] == "path-reference-metadata"
    assert "adl-instruction-path-not-inlined" in loss_codes(report)


def test_invalid_document_fails_gracefully() -> None:
    proc = run_command("--single", "examples/invalid/adl-v0.2-string-instructions.yaml")
    assert proc.returncode == 1, proc.stderr
    report = json.loads(proc.stdout)
    assert_report_shape(report)
    assert report["supported"] is False
    assert report["lossless"] is False
    assert report["structuralErrors"]
    assert "harness.instructions" in report["structuralErrors"][0]
    assert report["supportedRequirements"] == []
    assert report["unsupportedRequirements"] == []
    assert report["degradedRequirements"] == []
    assert report["metadataOnlyExtensions"] == []
    assert report["lossMetadata"] == []
    assert report["mafPromptYamlOmitted"] == {"reason": "structural-errors"}


def test_default_run_is_deterministic() -> None:
    first = run_command()
    second = run_command()
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    reports = json.loads(first.stdout)
    assert [report["source"] for report in reports] == DEFAULT_SOURCES
    for report in reports:
        assert_report_shape(report)


def main() -> int:
    test_simple_agent_supported_but_not_lossless()
    test_simple_agent_prompt_yaml_export()
    test_payment_and_delegation_reports()
    test_mcp_and_non_declarative_tools()
    test_path_instructions_omit_prompt_yaml()
    test_invalid_document_fails_gracefully()
    test_default_run_is_deterministic()
    print("PASS MAF compatibility")
    return 0


if __name__ == "__main__":
    sys.exit(main())
