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
        assert item["unsupportedFeatures"] == ["mcp_execution"]
        assert item["requiredHostedServices"] == ["mcp:approved-docs-search"]

    assert reports[0]["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert reports[1]["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert reports[2]["requiredSecrets"] == ["GEMINI_API_KEY"]
    assert reports[3]["requiredSecrets"] == []
    assert reports[4]["requiredSecrets"] == []
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
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert "Payment extension is dry-run only" in payment["warnings"][1]


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
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert "Payment extension is dry-run only" in payment["warnings"][1]


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
    assert payment["unsupportedFeatures"] == ["real_settlement"]
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert "Payment extension is dry-run only" in payment["warnings"][1]


def test_gemini_compatibility_mode_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "gemini"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "gemini-provider-compatibility-only"
    assert report["supported"] is False
    assert report["unsupportedFeatures"] == ["mcp_execution"]
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
    assert tool["supported"] is True
    assert tool["providerMapping"]["modelProfile"]["localProviderDeclared"] is False
    assert tool["providerMapping"]["adapterMapping"]["functionTools"] == ["search_docs"]
    assert tool["providerMapping"]["adapterMapping"]["toolCalls"] == "custom-harness-required"

    payment = reports["paid-specialist-researcher"]
    assert payment["supported"] is False
    assert payment["unsupportedFeatures"] == ["real_settlement"]
    assert payment["providerMapping"]["adapterMapping"]["metadataOnly"] == [
        "harness.policies",
        "harness.evalGates",
        "extensions.x402",
        "extensions.receipts",
        "extensions.reputation",
    ]
    assert "Payment extension is dry-run only" in payment["warnings"][1]


def test_ollama_compatibility_mode_keeps_mcp_execution_unsupported() -> None:
    proc = run_cli(["examples/mcp-readonly-agent.yaml", "--target", "ollama"])
    report = json.loads(proc.stdout)[0]
    assert report["compatibilityMode"] == "ollama-local-provider-compatibility-only"
    assert report["supported"] is False
    assert report["requiredSecrets"] == []
    assert report["unsupportedFeatures"] == ["mcp_execution"]
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
    assert simple["requiredSecrets"] == []
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
    assert report["requiredSecrets"] == []
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
    test_no_matching_agent_fails_before_empty_report()
    test_list_targets_includes_mcp_readonly()
    print("PASS provider compatibility CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
