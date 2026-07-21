#!/usr/bin/env python3
"""Check provider adapter codegen planning stays compatibility-only."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MANIFEST_FIXTURE = ROOT / "tests/fixtures/provider-adapter-codegen-manifest.json"


def run_cli(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/provider_adapter_codegen_plan.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def test_all_provider_targets_are_blocked_before_codegen() -> None:
    proc = run_cli(
        [
            "examples/simple-agent.yaml",
            "examples/tool-agent.yaml",
            "examples/payment-agent.yaml",
            "examples/mcp-readonly-agent.yaml",
        ]
    )
    plan = json.loads(proc.stdout)

    assert plan["planId"] == "provider-adapter-codegen-compatibility-only"
    assert plan["planStatus"] == "blocked-before-runnable-codegen"
    assert plan["boundary"] == {
        "runtimeExecutionAllowed": False,
        "networkAccess": False,
        "paymentAccess": False,
        "mcpInvocation": False,
        "writesFiles": False,
        "installsDependencies": False,
        "generatesRunnableCode": False,
    }
    assert plan["inputs"]["targets"] == ["openai", "anthropic", "gemini", "ollama", "langgraph"]
    assert plan["inputs"]["compatibilityReportCount"] == 20

    targets = {item["target"]: item for item in plan["targetPlans"]}
    assert set(targets) == {"openai", "anthropic", "gemini", "ollama", "langgraph"}
    assert targets["openai"]["compatibilityModes"] == ["openai-adapter-compatibility-only"]
    assert targets["anthropic"]["compatibilityModes"] == ["anthropic-mcp-compatibility-only"]
    assert targets["gemini"]["compatibilityModes"] == ["gemini-provider-compatibility-only"]
    assert targets["ollama"]["compatibilityModes"] == ["ollama-local-provider-compatibility-only"]
    assert targets["langgraph"]["compatibilityModes"] == ["langgraph-compatibility-report-only"]

    for item in targets.values():
        assert item["codegenStatus"] == "blocked-report-only"
        assert item["generationAllowed"] is False
        assert len(item["plannedFileShapes"]) == 4
        assert any(
            file_shape["path"].endswith("_plan_test.py")
            for file_shape in item["plannedFileShapes"]
        )
        assert "real_settlement" in item["unsupportedSemantics"]
        assert "mcp_execution" in item["unsupportedSemantics"]
        assert item["warningCount"] > 0

    assert targets["openai"]["requiredSecrets"] == ["OPENAI_API_KEY"]
    assert targets["anthropic"]["requiredSecrets"] == ["ANTHROPIC_API_KEY"]
    assert targets["gemini"]["requiredSecrets"] == ["GEMINI_API_KEY"]
    assert targets["ollama"]["requiredSecrets"] == []
    assert targets["langgraph"]["requiredSecrets"] == ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    assert targets["anthropic"]["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert "metadata_only:extensions.x402" in targets["gemini"]["unsupportedSemantics"]
    assert "unsupported_execution:docs_search" in targets["langgraph"]["unsupportedSemantics"]

    fixture = json.loads(MANIFEST_FIXTURE.read_text())
    assert plan["adapterManifestFixture"] == fixture
    assert fixture["schemaVersion"] == "provider-adapter-codegen-manifest-fixture.v0.1"
    assert fixture["fixtureStatus"] == "blocked-report-only"
    assert fixture["boundary"] == plan["boundary"]
    assert [gate["id"] for gate in fixture["manifestValidationGates"]] == [
        "manifest-fixture-deterministic",
        "manifest-files-report-only",
        "manifest-target-support-metadata",
        "manifest-runtime-boundary-disabled",
    ]

    target_manifests = {
        item["target"]: item for item in fixture["targetManifests"]
    }
    assert set(target_manifests) == set(targets)
    assert target_manifests["openai"]["manifestId"] == "openai-provider-adapter-codegen-manifest"
    assert target_manifests["anthropic"]["targetSupportMetadata"]["requiredSecretRefs"] == [
        "ANTHROPIC_API_KEY"
    ]
    assert target_manifests["ollama"]["targetSupportMetadata"]["requiredSecretRefs"] == []
    assert target_manifests["langgraph"]["plannedFiles"][2]["path"] == (
        "adapters/langgraph/static_graph_review.json"
    )

    for manifest in target_manifests.values():
        assert manifest["manifestStatus"] == "blocked-report-only"
        assert manifest["generationAllowed"] is False
        assert len(manifest["plannedFiles"]) == 4
        assert len(manifest["blockers"]) == 2
        for planned_file in manifest["plannedFiles"]:
            assert planned_file["plannedOnly"] is True
            assert planned_file["generatedByThisPlan"] is False
            assert planned_file["validationStatus"] == "not-generated"


def test_target_and_agent_filters_keep_plan_static() -> None:
    proc = run_cli(["--agent", "mcp-readonly-docs", "--target", "anthropic", "--target", "langgraph"])
    plan = json.loads(proc.stdout)
    assert plan["inputs"]["examples"] == ["examples/mcp-readonly-agent.yaml"]
    assert plan["inputs"]["targets"] == ["anthropic", "langgraph"]
    assert plan["inputs"]["compatibilityReportCount"] == 2
    assert [item["target"] for item in plan["targetPlans"]] == ["anthropic", "langgraph"]

    anthropic, langgraph = plan["targetPlans"]
    assert anthropic["generationAllowed"] is False
    assert anthropic["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert anthropic["unsupportedSemantics"] == [
        "mcp_execution",
        "metadata_only:harness.evalGates",
        "metadata_only:harness.policies",
        "unsupported_execution:docs_search",
    ]
    assert langgraph["generationAllowed"] is False
    assert langgraph["requiredHostedServices"] == ["mcp:approved-docs-search"]
    assert langgraph["unsupportedSemantics"] == [
        "mcp_execution",
        "metadata_only:harness.evalGates",
        "metadata_only:harness.policies",
        "metadata_only:harness.tools[type=mcp]",
        "unsupported_execution:docs_search",
    ]


def test_summary_output_file_names_disabled_generation_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "provider-adapter-codegen-plan.txt"
        proc = run_cli(["examples/simple-agent.yaml", "--target", "ollama", "--format", "summary", "--output", str(output)])
        assert proc.stdout == ""
        text = output.read_text()

    assert "Provider adapter codegen plan (compatibility-only)" in text
    assert "writesFiles=false" in text
    assert "generatesRunnableCode=false" in text
    assert "ollama: status=blocked-report-only" in text


def test_no_matching_agent_fails_before_empty_plan() -> None:
    proc = run_cli(["--agent", "missing-agent"], check=False)
    assert proc.returncode == 1
    assert "No ADL examples matched" in proc.stderr
    assert proc.stdout == ""


def main() -> int:
    test_all_provider_targets_are_blocked_before_codegen()
    test_target_and_agent_filters_keep_plan_static()
    test_summary_output_file_names_disabled_generation_boundary()
    test_no_matching_agent_fails_before_empty_plan()
    print("PASS provider adapter codegen plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
