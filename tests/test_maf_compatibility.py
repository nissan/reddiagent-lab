#!/usr/bin/env python3
"""Check report-only Microsoft Agent Framework compatibility output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

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
RUNTIME_EXAMPLES = [
    "examples/v0.2/runtime-hosted-container-agent.yaml",
    "examples/v0.2/runtime-local-python-agent.yaml",
    "examples/v0.2/runtime-platform-native-agent.yaml",
    "examples/v0.2/runtime-serverless-platform-agent.yaml",
]
# The full key-set a `mafPromptYaml` export may carry; policy, eval, and
# payment content must never leak into the export.
PROMPT_EXPORT_ALLOWED_KEYS = {"kind", "name", "displayName", "description", "instructions", "model"}
HARNESS_LOSS_CODES = {
    "harness.runtime": "maf-no-runtime-descriptor",
    "harness.deployment": "maf-no-deployment-descriptor",
    "harness.recovery": "maf-no-recovery-controls",
    "harness.dataSources": "maf-no-data-source-contract",
}


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


def run_single_doc(doc: dict, name: str = "probe.yaml") -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(yaml.safe_dump(doc))
        return run_single(str(path))


def test_runtime_deployment_recovery_data_sources_are_metadata_only() -> None:
    report = run_single_doc(
        {
            "metadata": {"name": "runtime-loss-probe"},
            "harness": {
                "instructions": {"inline": "Static probe."},
                "runtime": {"target": "hosted-container"},
                "deployment": {"target": "local"},
                "recovery": {"mode": "none"},
                "dataSources": [{"id": "notes", "trust": "untrusted"}],
            },
            "model": {"providers": {"preferred": "openai"}},
        }
    )
    assert_report_shape(report)
    assert report["supported"] is True
    assert report["lossless"] is False
    assert set(HARNESS_LOSS_CODES) <= set(report["metadataOnlyExtensions"])
    assert set(HARNESS_LOSS_CODES.values()) <= loss_codes(report)
    for item in report["lossMetadata"]:
        if item["code"] in HARNESS_LOSS_CODES.values():
            assert HARNESS_LOSS_CODES[item["path"]] == item["code"]


def test_runtime_examples_surface_runtime_sections() -> None:
    for path in RUNTIME_EXAMPLES:
        report = run_single(path)
        assert_report_shape(report)
        assert report["lossless"] is False, path
        assert "harness.runtime" in report["metadataOnlyExtensions"], path
        assert "maf-no-runtime-descriptor" in loss_codes(report), path


def test_malformed_shapes_fail_gracefully() -> None:
    base = {"metadata": {"name": "malformed-probe"}, "harness": {"instructions": {"inline": "x"}}}
    cases = [
        (
            "preferred-as-mapping.yaml",
            {**base, "model": {"providers": {"preferred": {"id": "openai"}}}},
            "model.providers.preferred",
        ),
        (
            "providers-as-list.yaml",
            {**base, "model": {"providers": ["openai"]}},
            "model.providers",
        ),
        (
            "tool-as-bare-string.yaml",
            {**base, "harness": {"instructions": {"inline": "x"}, "tools": ["fetch"]}},
            "harness.tools[0]",
        ),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for name, doc, needle in cases:
            path = Path(tmp) / name
            path.write_text(yaml.safe_dump(doc))
            proc = run_command("--single", str(path))
            assert proc.returncode == 1, (name, proc.returncode, proc.stderr)
            assert "Traceback" not in proc.stderr, (name, proc.stderr)
            report = json.loads(proc.stdout)
            assert_report_shape(report)
            assert report["supported"] is False, name
            assert report["lossless"] is False, name
            assert any(needle in error for error in report["structuralErrors"]), (
                name,
                report["structuralErrors"],
            )


def test_falsy_extensions_still_listed() -> None:
    report = run_single_doc(
        {
            "metadata": {"name": "falsy-extension-probe"},
            "harness": {"instructions": {"inline": "Static probe."}},
            "model": {"providers": {"preferred": "openai"}},
            "extensions": {"x402": {}, "telemetry": None},
        }
    )
    assert_report_shape(report)
    assert "extensions.x402" in report["metadataOnlyExtensions"]
    assert "extensions.telemetry" in report["metadataOnlyExtensions"]
    unsupported = {item["requirement"]: item["reason"] for item in report["unsupportedRequirements"]}
    assert unsupported["extensions.x402"] == "maf-has-no-payment-surface"
    assert "maf-has-no-payment-surface" in loss_codes(report)


def test_missing_provider_gets_distinct_omission_reason() -> None:
    no_model = run_single_doc(
        {
            "metadata": {"name": "no-model-probe"},
            "harness": {"instructions": {"inline": "Static probe."}},
        }
    )
    assert_report_shape(no_model)
    assert no_model["mafPromptYamlOmitted"] == {"reason": "no-model-provider-declared"}

    unmappable = run_single_doc(
        {
            "metadata": {"name": "unmappable-provider-probe"},
            "harness": {"instructions": {"inline": "Static probe."}},
            "model": {"providers": {"preferred": "mistral"}},
        }
    )
    assert_report_shape(unmappable)
    assert unmappable["mafPromptYamlOmitted"] == {"reason": "no-maf-connector-for-preferred-provider"}
    assert "no-maf-connector-for-provider" in loss_codes(unmappable)


def test_prompt_export_key_set_is_bounded() -> None:
    exports_seen = 0
    for path in DEFAULT_SOURCES:
        report = run_single(path)
        if "mafPromptYaml" not in report:
            continue
        exports_seen += 1
        prompt = yaml.safe_load(report["mafPromptYaml"])
        assert set(prompt) <= PROMPT_EXPORT_ALLOWED_KEYS, (path, sorted(set(prompt)))
    assert exports_seen > 0


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
    test_runtime_deployment_recovery_data_sources_are_metadata_only()
    test_runtime_examples_surface_runtime_sections()
    test_malformed_shapes_fail_gracefully()
    test_falsy_extensions_still_listed()
    test_missing_provider_gets_distinct_omission_reason()
    test_prompt_export_key_set_is_bounded()
    test_default_run_is_deterministic()
    print("PASS MAF compatibility")
    return 0


if __name__ == "__main__":
    sys.exit(main())
