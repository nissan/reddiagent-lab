#!/usr/bin/env python3
"""Check provider compatibility report CLI selectors and output modes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


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
            "gemini",
            "--target",
            "ollama",
            "--target",
            "langgraph",
            "--target",
            "mcp-readonly",
        ]
    )
    reports = json.loads(proc.stdout)
    assert [item["target"] for item in reports] == [
        "openai",
        "anthropic",
        "gemini",
        "ollama",
        "langgraph",
        "mcp-readonly",
    ]
    assert {item["agent"] for item in reports} == {"mcp-readonly-docs"}

    for item in reports:
        assert item["boundary"] == {
            "runtimeExecutionAllowed": False,
            "networkAccess": False,
            "paymentAccess": False,
            "mcpInvocation": False,
        }
        assert item["supported"] is False
        assert item["requiredHostedServices"] == ["mcp:approved-docs-search"]

    assert reports[0]["unsupportedFeatures"] == ["mcp_execution"]
    assert reports[1]["unsupportedFeatures"] == ["mcp_execution"]
    assert reports[2]["unsupportedFeatures"] == [
        "provider_not_declared",
        "model_requirement:model.providers",
        "mcp_execution",
    ]
    assert reports[3]["unsupportedFeatures"] == [
        "provider_not_declared",
        "model_requirement:model.providers",
        "mcp_execution",
    ]
    assert reports[4]["unsupportedFeatures"] == ["mcp_execution"]
    assert reports[5]["unsupportedFeatures"] == ["mcp_execution"]

    assert reports[0]["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert reports[1]["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert reports[2]["requiredSecrets"] == []
    assert reports[3]["requiredSecrets"] == []
    assert reports[4]["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert reports[5]["requiredSecrets"] == []


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


def test_v02_invalid_source_boundaries_fail_before_reporting() -> None:
    invalid_paths = [
        "examples/invalid/adl-v0.2-data-source-alias.yaml",
        "examples/invalid/adl-v0.2-untrusted-source-no-check.yaml",
        "examples/invalid/adl-v0.2-untrusted-source-approved-expectation.yaml",
        "examples/invalid/adl-v0.2-unknown-provider-id.yaml",
        "examples/invalid/adl-v0.2-unknown-model-requirement.yaml",
    ]

    for path in invalid_paths:
        proc = run_cli([path, "--target", "openai"])
        reports = json.loads(proc.stdout)
        assert proc.stderr == ""
        assert len(reports) == 1
        report = reports[0]
        assert report["target"] == "openai"
        assert report["supported"] is False
        assert report["level"] == 0
        assert report["compatibilityMode"] == "provider-compatibility-report-refused"
        assert report["unsupportedFeatures"] == ["adl_v0_2_schema_validation"]
        assert report["providerResolution"]["selectedRole"] == "schema-invalid"
        assert report["dataSourceTypes"] == []
        assert report["sourceBoundary"] == []
        assert report["validationDiagnostics"], path
        assert report["conformance"]["achievedLevel"] == -1
        assert report["conformance"]["status"] == "fail"


def test_v02_provider_refusal_does_not_crash_on_malformed_provider_shapes() -> None:
    malformed_docs = {
        "providers-string": """
apiVersion: reddiagent.dev/v0.2
kind: Agent
metadata:
  name: providers-string
  description: Malformed provider shape.
model:
  capability: chat
  providers: openai
  requirements:
    toolCalling: true
harness:
  instructions:
    inline: "Stay static."
  runtime:
    target: local-python
""",
        "fallbacks-string": """
apiVersion: reddiagent.dev/v0.2
kind: Agent
metadata:
  name: fallbacks-string
  description: Malformed fallback provider shape.
model:
  capability: chat
  providers:
    preferred: anthropic
    fallbacks: openai
  requirements:
    toolCalling: true
harness:
  instructions:
    inline: "Stay static."
  runtime:
    target: local-python
""",
    }

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, content in malformed_docs.items():
            path = Path(tmp) / f"{name}.yaml"
            path.write_text(content)
            paths.append(str(path))

        proc = run_cli([*paths, "--target", "openai"])

    reports = json.loads(proc.stdout)
    assert proc.stderr == ""
    assert [report["agent"] for report in reports] == ["providers-string", "fallbacks-string"]
    assert reports[0]["providerResolution"]["orderedCandidates"] == []
    assert reports[1]["providerResolution"]["orderedCandidates"] == ["anthropic"]
    for report in reports:
        assert report["supported"] is False
        assert report["compatibilityMode"] == "provider-compatibility-report-refused"
        assert report["unsupportedFeatures"] == ["adl_v0_2_schema_validation"]
        assert report["providerResolution"]["selectedProvider"] is None
        assert report["providerResolution"]["selectedRole"] == "schema-invalid"
        assert report["boundary"]["runtimeExecutionAllowed"] is False
        assert report["validationDiagnostics"]


def test_v02_provider_exports_conformance_metadata() -> None:
    proc = run_cli(["tests/fixtures/adl-v0.2-level3-ready.yaml", "--target", "openai"])
    report = json.loads(proc.stdout)[0]

    assert report["target"] == "openai"
    assert report["conformance"]["requestedLevel"] == 3
    assert report["conformance"]["achievedLevel"] >= 3
    assert report["conformance"]["status"] == "pass"
    assert report["conformance"]["missingFieldsByLevel"]["3"] == []


def test_v02_provider_exports_cumulative_conformance_failure_metadata() -> None:
    proc = run_cli(["tests/fixtures/adl-v0.2-level4-complete-without-level3.yaml", "--target", "openai"])
    report = json.loads(proc.stdout)[0]

    assert report["target"] == "openai"
    assert report["conformance"]["requestedLevel"] == 4
    assert report["conformance"]["status"] == "fail"
    assert report["conformance"]["achievedLevel"] < 4
    assert report["conformance"]["missingFieldsByLevel"]["4"] == []
    assert report["conformance"]["missingFieldsByLevel"]["3"] == [
        "extensions.x402.enabled=true",
        "extensions.x402.intents",
        "extensions.receipts.required=true",
        "extensions.reputation.emitSignals",
    ]


def test_v02_provider_refusal_does_not_crash_on_invalid_requested_level() -> None:
    proc = run_cli(["tests/fixtures/adl-v0.2-invalid-requested-level.yaml", "--target", "openai"])
    report = json.loads(proc.stdout)[0]

    assert report["target"] == "openai"
    assert report["supported"] is False
    assert report["compatibilityMode"] == "provider-compatibility-report-refused"
    assert report["conformance"]["requestedLevel"] == 5
    assert report["conformance"]["achievedLevel"] == -1
    assert report["conformance"]["status"] == "fail"


def test_v02_provider_reports_resolution_and_model_requirement_diagnostics() -> None:
    proc = run_cli(
        [
            "examples/v0.2/provider-capability-agent.yaml",
            "--target",
            "anthropic",
            "--target",
            "openai",
            "--target",
            "ollama",
            "--target",
            "gemini",
        ]
    )
    reports = {item["target"]: item for item in json.loads(proc.stdout)}

    anthropic = reports["anthropic"]
    assert anthropic["providerResolution"] == {
        "requestedTarget": "anthropic",
        "orderedCandidates": ["anthropic", "openai", "ollama"],
        "selectedProvider": "anthropic",
        "selectedRole": "preferred",
        "hostedProvider": True,
    }
    assert anthropic["supported"] is False
    assert anthropic["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert anthropic["unsupportedFeatures"] == [
        "model_requirement:jsonMode",
        "model_requirement:maxOutputTokens",
        "model_requirement:modalities",
    ]
    assert {
        (item["requirement"], item["requested"])
        for item in anthropic["modelCapabilityRequirements"]["unsupportedRequirements"]
    } == {
        ("jsonMode", True),
        ("maxOutputTokens", 12000),
        ("modalities", "audio"),
    }

    openai = reports["openai"]
    assert openai["providerResolution"]["selectedRole"] == "fallback"
    assert openai["providerResolution"]["selectedProvider"] == "openai"
    assert openai["supported"] is True
    assert openai["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert openai["modelCapabilityRequirements"]["unsupportedRequirements"] == []

    ollama = reports["ollama"]
    assert ollama["providerResolution"]["selectedRole"] == "fallback"
    assert ollama["providerResolution"]["hostedProvider"] is False
    assert ollama["requiredSecrets"] == []
    assert ollama["supported"] is False
    assert {
        (item["requirement"], item["requested"])
        for item in ollama["modelCapabilityRequirements"]["degradedRequirements"]
    } == {
        ("toolCalling", True),
        ("structuredOutput", True),
        ("jsonMode", True),
    }
    assert ollama["modelCapabilityRequirements"]["lossMetadata"]
    assert any("Some model capability requirements are degraded" in warning for warning in ollama["warnings"])

    gemini = reports["gemini"]
    assert gemini["providerResolution"] == {
        "requestedTarget": "gemini",
        "orderedCandidates": ["anthropic", "openai", "ollama"],
        "selectedProvider": None,
        "selectedRole": "not-declared",
        "hostedProvider": False,
    }
    assert gemini["supported"] is False
    assert gemini["requiredSecrets"] == []
    assert "provider_not_declared" in gemini["unsupportedFeatures"]
    assert {
        item["requirement"]
        for item in gemini["modelCapabilityRequirements"]["unsupportedRequirements"]
    } == {"model.providers"}
    assert any("not declared in model.providers" in warning for warning in gemini["warnings"])


def test_openai_compatibility_mode_maps_metadata_only_semantics() -> None:
    proc = run_cli(
        [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/payment-agent.yaml",
            "--target",
            "openai",
        ]
    )
    reports = {item["agent"]: item for item in json.loads(proc.stdout)}

    simple = reports["simple-research-helper"]
    assert simple["target"] == "openai"
    assert simple["compatibilityMode"] == "openai-adapter-compatibility-only"
    assert simple["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert simple["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert simple["providerMapping"]["reportOnly"] is True
    assert simple["providerMapping"]["adapterMapping"]["tools"] == []
    assert simple["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.memory",
    ]
    assert "metadata-only" in simple["warnings"][0]

    tool = reports["source-checker"]
    assert tool["supported"] is True
    assert tool["providerMapping"]["adapterMapping"]["tools"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["structuredOutput"] is True
    assert tool["providerMapping"]["adapterMapping"]["unsupportedExecution"] == []

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == ["real_settlement"]
    assert payment["providerResolution"]["selectedProvider"] == "openai"
    assert payment["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert any("Payment extension is dry-run only" in warning for warning in payment["warnings"])


def test_openai_compatibility_mode_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "openai"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "openai-adapter-compatibility-only"
    assert report["supported"] is False
    assert report["unsupportedFeatures"] == ["mcp_execution"]
    assert report["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert report["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.tools[type=mcp]",
    ]
    assert report["providerMapping"]["adapterMapping"]["unsupportedExecution"] == ["docs_search"]


def test_anthropic_compatibility_mode_maps_mcp_metadata_without_invocation() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "anthropic"])
    report = json.loads(proc.stdout)[0]
    assert report["target"] == "anthropic"
    assert report["compatibilityMode"] == "anthropic-mcp-compatibility-only"
    assert report["supported"] is False
    assert report["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert report["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert report["unsupportedFeatures"] == ["mcp_execution"]
    assert report["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert "metadata-only" in report["warnings"][0]
    assert report["providerMapping"]["reportOnly"] is True
    assert report["providerMapping"]["adapterMapping"]["toolUseSchemas"] == []
    assert report["providerMapping"]["adapterMapping"]["mcpDeclarations"] == [
        {
            "id": "docs_search",
            "serverRef": "approved-docs-search",
            "toolName": "search",
        }
    ]
    assert report["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
    ]
    assert report["providerMapping"]["adapterMapping"]["unsupportedExecution"] == ["docs_search"]


def test_anthropic_compatibility_mode_preserves_payment_as_metadata_only() -> None:
    proc = run_cli(["examples/tool-agent.yaml", "examples/payment-agent.yaml", "--target", "anthropic"])
    reports = {item["agent"]: item for item in json.loads(proc.stdout)}

    tool = reports["source-checker"]
    assert tool["supported"] is True
    assert tool["providerMapping"]["adapterMapping"]["toolUseSchemas"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["mcpDeclarations"] == []
    assert tool["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
    ]

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == ["real_settlement"]
    assert payment["providerResolution"]["selectedProvider"] == "anthropic"
    assert payment["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert any("Payment extension is dry-run only" in warning for warning in payment["warnings"])


def test_gemini_compatibility_mode_maps_functions_and_metadata_only_semantics() -> None:
    proc = run_cli(
        [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/payment-agent.yaml",
            "--target",
            "gemini",
        ]
    )
    reports = {item["agent"]: item for item in json.loads(proc.stdout)}

    simple = reports["simple-research-helper"]
    assert simple["target"] == "gemini"
    assert simple["compatibilityMode"] == "gemini-provider-compatibility-only"
    assert simple["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert simple["requiredSecrets"] == ["GEMINI_API_KEY"]
    assert simple["providerMapping"]["reportOnly"] is True
    assert simple["providerMapping"]["adapterMapping"]["functionDeclarations"] == []
    assert simple["providerMapping"]["adapterMapping"]["grounding"] == "not-configured"
    assert simple["providerMapping"]["adapterMapping"]["codeExecution"] == "unsupported"
    assert simple["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.memory",
    ]
    assert "metadata-only or unsupported" in simple["warnings"][0]

    tool = reports["source-checker"]
    assert tool["supported"] is True
    assert tool["providerMapping"]["adapterMapping"]["functionDeclarations"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["structuredOutput"] is True

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == [
        "provider_not_declared",
        "real_settlement",
        "model_requirement:model.providers",
    ]
    assert payment["providerResolution"]["selectedProvider"] is None
    assert payment["requiredSecrets"] == []
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert any("Payment extension is dry-run only" in warning for warning in payment["warnings"])


def test_gemini_compatibility_mode_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "gemini"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "gemini-provider-compatibility-only"
    assert report["supported"] is False
    assert report["unsupportedFeatures"] == [
        "provider_not_declared",
        "model_requirement:model.providers",
        "mcp_execution",
    ]
    assert report["requiredSecrets"] == []
    assert report["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert report["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.tools[type=mcp]",
    ]
    assert report["providerMapping"]["adapterMapping"]["unsupportedExecution"] == ["docs_search"]


def test_ollama_compatibility_mode_maps_local_provider_metadata_only() -> None:
    proc = run_cli(
        [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/payment-agent.yaml",
            "--target",
            "ollama",
        ]
    )
    reports = {item["agent"]: item for item in json.loads(proc.stdout)}

    simple = reports["simple-research-helper"]
    assert simple["target"] == "ollama"
    assert simple["compatibilityMode"] == "ollama-local-provider-compatibility-only"
    assert simple["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert simple["requiredSecrets"] == []
    assert simple["providerMapping"]["reportOnly"] is True
    assert simple["providerMapping"]["modelProfile"]["localProviderDeclared"] is True
    assert simple["providerMapping"]["adapterMapping"]["localEndpoint"] == "not-probed"
    assert simple["providerMapping"]["adapterMapping"]["modelId"] == "metadata-only"
    assert simple["providerMapping"]["adapterMapping"]["toolCalls"] == "not-required"
    assert simple["providerMapping"]["adapterMapping"]["structuredOutput"] == "custom-harness-required"
    assert simple["providerMapping"]["adapterMapping"]["stateAndMemory"] == "external-harness-owned"
    assert simple["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.memory",
    ]
    assert "local endpoint" in simple["warnings"][0]

    tool = reports["source-checker"]
    assert tool["supported"] is False
    assert tool["unsupportedFeatures"] == [
        "provider_not_declared",
        "model_requirement:model.providers",
    ]
    assert tool["providerMapping"]["modelProfile"]["localProviderDeclared"] is False
    assert tool["providerMapping"]["adapterMapping"]["functionTools"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["toolCalls"] == "custom-harness-required"

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == [
        "provider_not_declared",
        "real_settlement",
        "model_requirement:model.providers",
    ]
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert any("Payment extension is dry-run only" in warning for warning in payment["warnings"])


def test_ollama_compatibility_mode_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "ollama"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "ollama-local-provider-compatibility-only"
    assert report["supported"] is False
    assert report["requiredSecrets"] == []
    assert report["unsupportedFeatures"] == [
        "provider_not_declared",
        "model_requirement:model.providers",
        "mcp_execution",
    ]
    assert report["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert report["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.tools[type=mcp]",
    ]
    assert report["providerMapping"]["adapterMapping"]["unsupportedExecution"] == ["docs_search"]


def test_langgraph_compatibility_report_maps_graph_state_without_generation() -> None:
    proc = run_cli(
        [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/payment-agent.yaml",
            "--target",
            "langgraph",
        ]
    )
    reports = {item["agent"]: item for item in json.loads(proc.stdout)}

    simple = reports["simple-research-helper"]
    assert simple["target"] == "langgraph"
    assert simple["compatibilityMode"] == "langgraph-compatibility-report-only"
    assert simple["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
    }
    assert simple["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert simple["providerMapping"]["reportOnly"] is True
    assert simple["providerMapping"]["adapterMapping"]["graph"] == "not-generated"
    assert simple["providerMapping"]["adapterMapping"]["stateSchema"] == {
        "messages": "harness-owned",
        "memory": "metadata-only",
        "policyResults": "metadata-only",
        "evalResults": "metadata-only",
        "receipt": "not-declared",
    }
    assert simple["providerMapping"]["adapterMapping"]["nodes"] == ["model", "eval-gates"]
    assert simple["providerMapping"]["adapterMapping"]["toolNodes"] == []
    assert simple["providerMapping"]["adapterMapping"]["edges"] == "static-plan-only"
    assert simple["providerMapping"]["adapterMapping"]["checkpointing"] == "metadata-only"
    assert "static-plan-only" in simple["warnings"][0]

    tool = reports["source-checker"]
    assert tool["supported"] is True
    assert tool["providerMapping"]["adapterMapping"]["nodes"] == ["model", "tools", "eval-gates"]
    assert tool["providerMapping"]["adapterMapping"]["toolNodes"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["checkpointing"] == "not-declared"

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == ["real_settlement"]
    assert payment["providerMapping"]["adapterMapping"]["nodes"] == [
        "model",
        "tools",
        "eval-gates",
        "receipt-metadata",
    ]
    assert payment["providerMapping"]["adapterMapping"]["stateSchema"]["receipt"] == "metadata-only"
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]


def test_langgraph_compatibility_report_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "langgraph"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "langgraph-compatibility-report-only"
    assert report["supported"] is False
    assert report["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert report["unsupportedFeatures"] == ["mcp_execution"]
    assert report["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert report["providerMapping"]["adapterMapping"]["graph"] == "not-generated"
    assert report["providerMapping"]["adapterMapping"]["mcpToolNodes"] == ["docs_search"]
    assert report["providerMapping"]["adapterMapping"]["unsupportedExecution"] == ["docs_search"]
    assert report["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "harness.tools[type=mcp]",
    ]


def test_provider_reports_use_canonical_source_boundary_vocabulary() -> None:
    proc = run_cli(
        [
            "examples/v0.2/source-boundary-agent.yaml",
            "--target",
            "openai",
            "--target",
            "anthropic",
            "--target",
            "gemini",
            "--target",
            "ollama",
            "--target",
            "langgraph",
        ]
    )
    reports = json.loads(proc.stdout)
    expected_types = ["file", "url", "api", "database", "vector-index", "mcp"]

    assert [item["target"] for item in reports] == ["openai", "anthropic", "gemini", "ollama", "langgraph"]
    for report in reports:
        assert report["dataSourceTypes"] == expected_types
        assert [source["type"] for source in report["sourceBoundary"]] == expected_types
        assert report["providerMapping"]["adapterMapping"]["sourceBoundary"] == report["sourceBoundary"]
        assert "harness.dataSources" in report["providerMapping"]["adapterMapping"]["metadataOnly"]
        for source in report["sourceBoundary"]:
            assert source["sourceRef"].startswith(f"{source['type']}:")
            assert source["trust"] == "approved"
            assert source["citationRequired"] is True
            assert source["sourceCheckRequired"] is True
            assert source["sourceCheckExpectation"] == "approved-source"


def test_provider_reports_refuse_invalid_v02_source_boundaries() -> None:
    proc = run_cli(
        [
            "examples/invalid/adl-v0.2-data-source-alias.yaml",
            "examples/invalid/adl-v0.2-untrusted-source-no-check.yaml",
            "examples/invalid/adl-v0.2-untrusted-source-approved-expectation.yaml",
            "--target",
            "openai",
        ]
    )
    reports = json.loads(proc.stdout)

    assert [report["agent"] for report in reports] == [
        "data-source-alias",
        "untrusted-source-no-check",
        "untrusted-source-approved-expectation",
    ]
    for report in reports:
        assert report["target"] == "openai"
        assert report["supported"] is False
        assert report["level"] == 0
        assert report["compatibilityMode"] == "provider-compatibility-report-refused"
        assert report["unsupportedFeatures"] == ["adl_v0_2_schema_validation"]
        assert report["dataSourceTypes"] == []
        assert report["sourceBoundary"] == []
        assert report["validationDiagnostics"]

    alias_messages = [item["message"] for item in reports[0]["validationDiagnostics"]]
    untrusted_no_check_messages = [item["message"] for item in reports[1]["validationDiagnostics"]]
    untrusted_approved_messages = [item["message"] for item in reports[2]["validationDiagnostics"]]
    assert any("document" in message and "is not one of" in message for message in alias_messages)
    assert "True was expected" in untrusted_no_check_messages
    assert any("'approved-source' is not one of" in message for message in untrusted_approved_messages)


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
    assert "gemini" in targets
    assert "ollama" in targets
    assert "langgraph" in targets
    assert "local-python" in targets
    assert "mcp-readonly" in targets


def main() -> int:
    test_target_agent_selection_covers_provider_and_mcp_paths()
    test_local_python_selector_and_summary_output_file()
    test_v02_invalid_source_boundaries_fail_before_reporting()
    test_v02_provider_refusal_does_not_crash_on_malformed_provider_shapes()
    test_v02_provider_exports_conformance_metadata()
    test_v02_provider_exports_cumulative_conformance_failure_metadata()
    test_v02_provider_refusal_does_not_crash_on_invalid_requested_level()
    test_v02_provider_reports_resolution_and_model_requirement_diagnostics()
    test_openai_compatibility_mode_maps_metadata_only_semantics()
    test_openai_compatibility_mode_keeps_mcp_execution_unsupported()
    test_anthropic_compatibility_mode_maps_mcp_metadata_without_invocation()
    test_anthropic_compatibility_mode_preserves_payment_as_metadata_only()
    test_gemini_compatibility_mode_maps_functions_and_metadata_only_semantics()
    test_gemini_compatibility_mode_keeps_mcp_execution_unsupported()
    test_ollama_compatibility_mode_maps_local_provider_metadata_only()
    test_ollama_compatibility_mode_keeps_mcp_execution_unsupported()
    test_langgraph_compatibility_report_maps_graph_state_without_generation()
    test_langgraph_compatibility_report_keeps_mcp_execution_unsupported()
    test_provider_reports_use_canonical_source_boundary_vocabulary()
    test_provider_reports_refuse_invalid_v02_source_boundaries()
    test_no_matching_agent_fails_before_empty_report()
    test_list_targets_includes_mcp_readonly()
    print("PASS provider compatibility CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
