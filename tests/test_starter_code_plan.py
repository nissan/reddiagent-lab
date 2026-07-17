#!/usr/bin/env python3
"""Check static starter-code review manifest output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DRY_RUN_FIXTURE = ROOT / "tests" / "fixtures" / "starter-code-dry-run-file-manifest.json"
TEMPLATE_CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "starter-code-template-contracts.json"
SAFETY_POLICY_FIXTURE = ROOT / "tests" / "fixtures" / "starter-code-safety-policy.json"
PREVIEW_BUNDLE_FIXTURE = ROOT / "tests" / "fixtures" / "starter-code-preview-bundles.json"
EVE_SKELETON_FIXTURE = ROOT / "tests" / "fixtures" / "eve-project-skeleton-dry-run-manifests.json"


def run_plan(*paths: str) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, "scripts/starter_code_plan.py", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/starter_code_plan.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_static_boundaries(plan: dict) -> None:
    assert plan["runtimeExecutionAllowed"] is False
    assert plan["networkAccess"] is False
    assert plan["paymentAccess"] is False
    assert plan["mcpInvocation"] is False
    assert plan["writesFiles"] is False
    assert plan["installsDependencies"] is False


def file_paths(plan: dict) -> list[str]:
    return [item["path"] for item in plan["plannedFiles"]]


def gate_ids(plan: dict) -> list[str]:
    return [item["id"] for item in plan["blockedGatesBeforeGeneration"]]


def dry_run_fixture(plans: list[dict]) -> dict:
    return {plan["source"]: plan["dryRunFileManifest"] for plan in plans}


def template_contract_fixture(plans: list[dict]) -> dict:
    return {plan["source"]: plan["templateContractFixture"] for plan in plans}


def template_ids(plan: dict) -> list[str]:
    return [item["templateId"] for item in plan["templateContracts"]]


def safety_policy_fixture(plans: list[dict]) -> dict:
    return {plan["source"]: safety_policy_summary(plan) for plan in plans}


def preview_bundle_fixture(plans: list[dict]) -> dict:
    return {plan["source"]: preview_bundle_summary(plan) for plan in plans}


def eve_skeleton_fixture(plans: list[dict]) -> dict:
    return {plan["source"]: plan["eveProjectSkeletonDryRunManifest"] for plan in plans}


def preview_bundle_summary(plan: dict) -> dict:
    bundle = plan["previewBundle"]
    safety = bundle["safetyPolicyState"]
    return {
        "format": bundle["format"],
        "source": bundle["source"],
        "outputRoot": bundle["outputRoot"],
        "bundleStatus": bundle["bundleStatus"],
        "manifestOnly": bundle["manifestOnly"],
        "validationStatus": bundle["validationStatus"],
        "boundaryFlags": {
            "runtimeExecutionAllowed": bundle["runtimeExecutionAllowed"],
            "networkAccess": bundle["networkAccess"],
            "paymentAccess": bundle["paymentAccess"],
            "mcpInvocation": bundle["mcpInvocation"],
            "writesFiles": bundle["writesFiles"],
            "installsDependencies": bundle["installsDependencies"],
        },
        "plannedFileCount": len(bundle["plannedFilePreviews"]),
        "plannedPaths": [item["path"] for item in bundle["plannedFilePreviews"]],
        "templateContractCount": bundle["templateContractCount"],
        "templateContractIds": bundle["templateContractIds"],
        "blockedGateIds": bundle["blockedGateIds"],
        "readyRequestId": safety["readyRequestId"],
        "readyDecision": safety["readyDecision"],
        "unsafeCount": safety["unsafeCount"],
        "unsafeAllowed": safety["unsafeAllowed"],
        "unsafePolicyIds": safety["unsafePolicyIds"],
        "failClosed": bundle["failClosed"],
        "previewNonGoalIds": bundle["previewNonGoalIds"],
    }


def safety_policy_summary(plan: dict) -> dict:
    policy = plan["starterSafetyPolicy"]
    decisions: dict[str, int] = {}
    for request in policy["unsafeRequests"]:
        decision = request["decision"]
        decisions[decision] = decisions.get(decision, 0) + 1
    return {
        "format": policy["format"],
        "source": policy["source"],
        "outputRoot": policy["outputRoot"],
        "manifestOnly": policy["manifestOnly"],
        "validationStatus": policy["validationStatus"],
        "boundaryFlags": {
            "runtimeExecutionAllowed": policy["runtimeExecutionAllowed"],
            "networkAccess": policy["networkAccess"],
            "paymentAccess": policy["paymentAccess"],
            "mcpInvocation": policy["mcpInvocation"],
            "writesFiles": policy["writesFiles"],
            "installsDependencies": policy["installsDependencies"],
        },
        "readyRequestId": policy["readyRequest"]["requestId"],
        "readyDecision": policy["readyRequest"]["decision"],
        "unsafeCount": len(policy["unsafeRequests"]),
        "unsafePolicyIds": [request["policyId"] for request in policy["unsafeRequests"]],
        "unsafeDecisions": decisions,
        "policyNonGoalIds": policy["policyNonGoalIds"],
    }


def main() -> int:
    plans = run_plan(
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/mcp-readonly-agent.yaml",
        "examples/payment-agent.yaml",
    )
    expected_dry_run = json.loads(DRY_RUN_FIXTURE.read_text())
    expected_template_contracts = json.loads(TEMPLATE_CONTRACT_FIXTURE.read_text())
    expected_safety_policy = json.loads(SAFETY_POLICY_FIXTURE.read_text())
    expected_preview_bundles = json.loads(PREVIEW_BUNDLE_FIXTURE.read_text())
    expected_eve_skeleton = json.loads(EVE_SKELETON_FIXTURE.read_text())
    assert dry_run_fixture(plans) == expected_dry_run
    assert template_contract_fixture(plans) == expected_template_contracts
    assert safety_policy_fixture(plans) == expected_safety_policy
    assert preview_bundle_fixture(plans) == expected_preview_bundles
    assert eve_skeleton_fixture(plans) == expected_eve_skeleton
    by_agent = {plan["agent"]: plan for plan in plans}

    simple = by_agent["simple-research-helper"]
    assert simple["format"] == "starter-code-review-manifest"
    assert simple["supported"] is True
    assert simple["target"] == {
        "language": "python",
        "packageLayout": "single-agent-starter",
        "generationMode": "manifest-only",
        "outputRoot": "starter/simple-research-helper",
    }
    assert simple["validation"]["status"] == "pass"
    assert simple["tools"]["toolCount"] == 0
    assert "starter/simple-research-helper/src/agent_harness.py" in file_paths(simple)
    assert "starter/simple-research-helper/.env.example" in file_paths(simple)
    assert simple["dryRunFileManifest"]["manifestOnly"] is True
    assert simple["dryRunFileManifest"]["writesFiles"] is False
    assert simple["dryRunFileManifest"]["validationStatus"] == "pass"
    assert simple["templateContractFixture"]["format"] == "starter-code-template-contract-fixture"
    assert simple["templateContractFixture"]["writesFiles"] is False
    assert simple["templateContractFixture"]["templateCount"] == 6
    assert "starter.python_harness" in template_ids(simple)
    assert simple["starterSafetyPolicy"]["readyRequest"]["decision"] == "allow"
    assert len(simple["starterSafetyPolicy"]["unsafeRequests"]) == 8
    assert all(request["decision"] == "deny" for request in simple["starterSafetyPolicy"]["unsafeRequests"])
    assert simple["previewBundle"]["bundleStatus"] == "ready-for-static-review"
    assert simple["previewBundle"]["writesFiles"] is False
    assert simple["previewBundle"]["installsDependencies"] is False
    assert simple["previewBundle"]["safetyPolicyState"]["unsafeAllowed"] is False
    assert simple["previewBundle"]["failClosed"]["unsafeRequestsDenied"] is True
    assert simple["previewBundle"]["failClosed"]["liveClaimsAllowed"] is False
    assert simple["eveProjectSkeletonDryRunManifest"]["paths"] == [
        "eve/simple-research-helper/agent/instructions.md",
        "eve/simple-research-helper/agent/agent.ts",
        "eve/simple-research-helper/agent/reddiagent.metadata.json",
        "eve/simple-research-helper/evals/has_answer.eval.ts",
    ]
    assert simple["eveProjectSkeletonDryRunManifest"]["writesFiles"] is False
    assert simple["eveProjectSkeletonDryRunManifest"]["installsDependencies"] is False
    assert simple["eveProjectSkeletonDryRunManifest"]["deploymentAllowed"] is False
    assert "eve-typescript-generation-review" in simple["eveProjectSkeletonDryRunManifest"]["blockedGateIds"]
    assert "no-provider-model-local-execution" in simple["starterSafetyPolicy"]["policyNonGoalIds"]
    assert "provider-runtime-review" in gate_ids(simple)
    assert_static_boundaries(simple)

    tool = by_agent["source-checker"]
    assert tool["tools"] == {
        "toolCount": 1,
        "toolIds": ["search_docs"],
        "fixtureCount": 1,
        "fixtureToolIds": ["search_docs"],
    }
    assert "starter/source-checker/fixtures/tools.json" in file_paths(tool)
    assert "starter/source-checker/tests/test_policy_eval_gates.py" in file_paths(tool)
    assert "starter.local_tool_fixtures" in template_ids(tool)
    assert "starter.local_tool_fixtures" in tool["previewBundle"]["templateContractIds"]
    assert "harness.toolFixtures" in tool["templateContractFixture"]["requiredInputRefs"]
    assert "no-external-network-tool-execution" in tool["starterSafetyPolicy"]["policyNonGoalIds"]
    assert "no-provider-model-local-execution" in tool["starterSafetyPolicy"]["policyNonGoalIds"]
    assert "eve/source-checker/agent/tools/search_docs.ts" in tool["eveProjectSkeletonDryRunManifest"]["paths"]
    assert any(
        slot["slot"] == "agent/tools/" and slot["planned"] is True
        for slot in tool["eveProjectSkeletonDryRunManifest"]["slotSummary"]
    )
    assert tool["previewBundle"]["safetyPolicyState"]["unsafeAllowed"] is False
    assert tool["metadataOnlyExtensions"] == []
    assert_static_boundaries(tool)

    mcp = by_agent["mcp-readonly-docs"]
    assert "mcp_runtime_invocation" in mcp["unsupportedFeatures"]
    assert "mcp-resolution-review" in gate_ids(mcp)
    assert "eve/mcp-readonly-docs/agent/connections/docs_search.ts" in mcp["eveProjectSkeletonDryRunManifest"]["paths"]
    assert any(
        slot["slot"] == "agent/connections/" and slot["planned"] is True
        for slot in mcp["eveProjectSkeletonDryRunManifest"]["slotSummary"]
    )
    assert mcp["eveProjectSkeletonDryRunManifest"]["mcpInvocation"] is False
    assert_static_boundaries(mcp)

    payment = by_agent["paid-specialist-researcher"]
    assert "live_payment_execution" in payment["unsupportedFeatures"]
    assert "non_local_runtime_execution" in payment["unsupportedFeatures"]
    assert "extensions.x402" in payment["metadataOnlyExtensions"]
    assert "extensions.receipts" in payment["metadataOnlyExtensions"]
    assert "extensions.reputation" in payment["metadataOnlyExtensions"]
    assert "runtime-target-review" in gate_ids(payment)
    assert "payment-rail-review" in gate_ids(payment)
    assert "starter/paid-specialist-researcher/tests/test_policy_eval_gates.py" in file_paths(payment)
    assert payment["templateContractFixture"]["templateCount"] == 6
    for contract in payment["templateContracts"]:
        assert "payment-rail-review" in contract["blockedGateIds"]
        assert contract["writesFiles"] is False
        assert contract["installsDependencies"] is False
        assert contract["runtimeExecutionAllowed"] is False
    for request in payment["starterSafetyPolicy"]["unsafeRequests"]:
        assert request["allowed"] is False
        assert "payment-rail-review" in request["blockedGateIds"]
    assert "payment-rail-review" in payment["previewBundle"]["blockedGateIds"]
    assert "eve/paid-specialist-researcher/agent/tools/fetch_approved_url.ts" in payment["eveProjectSkeletonDryRunManifest"]["paths"]
    assert payment["eveProjectSkeletonDryRunManifest"]["paymentAccess"] is False
    assert payment["eveProjectSkeletonDryRunManifest"]["deploymentAllowed"] is False
    assert "wallet-payment-settlement" in payment["previewBundle"]["safetyPolicyState"]["unsafeRisks"]
    assert "no-wallet-payment-settlement-access" in payment["starterSafetyPolicy"]["policyNonGoalIds"]
    assert "no-provider-model-local-execution" in payment["starterSafetyPolicy"]["policyNonGoalIds"]
    assert_static_boundaries(payment)

    invalid = run_command("--single", "examples/invalid/missing-instructions.yaml")
    assert invalid.returncode == 1
    invalid_plan = json.loads(invalid.stdout)
    assert invalid_plan["supported"] is False
    assert invalid_plan["validation"]["status"] == "fail"
    assert invalid_plan["plannedFiles"] == []
    assert invalid_plan["dryRunFileManifest"]["fileCount"] == 0
    assert invalid_plan["dryRunFileManifest"]["paths"] == []
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["paths"] == []
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["fileCount"] == 0
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["validationStatus"] == "fail"
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["writesFiles"] is False
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["installsDependencies"] is False
    assert invalid_plan["eveProjectSkeletonDryRunManifest"]["deploymentAllowed"] is False
    assert invalid_plan["dryRunFileManifest"]["validationStatus"] == "fail"
    assert invalid_plan["templateContracts"] == []
    assert invalid_plan["templateContractFixture"]["templateCount"] == 0
    assert invalid_plan["templateContractFixture"]["plannedPaths"] == []
    assert invalid_plan["templateContractFixture"]["validationStatus"] == "fail"
    assert invalid_plan["starterSafetyPolicy"]["validationStatus"] == "fail"
    assert invalid_plan["starterSafetyPolicy"]["readyRequest"]["decision"] == "allow"
    assert len(invalid_plan["starterSafetyPolicy"]["unsafeRequests"]) == 8
    assert invalid_plan["previewBundle"]["bundleStatus"] == "blocked-invalid-adl"
    assert invalid_plan["previewBundle"]["plannedFilePreviews"] == []
    assert invalid_plan["previewBundle"]["templateContractIds"] == []
    assert invalid_plan["previewBundle"]["validationErrorCount"] > 0
    assert invalid_plan["previewBundle"]["failClosed"]["invalidAdlBlocksPlannedFiles"] is True
    assert invalid_plan["previewBundle"]["failClosed"]["unsafeRequestsDenied"] is True
    assert invalid_plan["previewBundle"]["failClosed"]["liveClaimsAllowed"] is False
    assert "no-provider-model-local-execution" in invalid_plan["starterSafetyPolicy"]["policyNonGoalIds"]
    assert "generator-implementation-review" in gate_ids(invalid_plan)
    assert_static_boundaries(invalid_plan)

    bad_single = run_command("--single", "examples/simple-agent.yaml", "examples/tool-agent.yaml")
    assert bad_single.returncode == 2
    assert "--single requires exactly one ADL path" in bad_single.stderr

    print("PASS starter code review manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
