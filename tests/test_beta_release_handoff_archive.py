#!/usr/bin/env python3
"""Beta release handoff archive checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-release-handoff.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-handoff-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_release_handoff_archive  # noqa: E402


def run_handoff() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_release_handoff_archive.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def source_context() -> tuple[dict, dict]:
    pinned_acceptance = beta_release_handoff_archive.load_json(
        beta_release_handoff_archive.PINNED_ACCEPTANCE_BUNDLE
    )
    current_acceptance = beta_release_handoff_archive.current_acceptance_bundle()
    runtime_evidence = beta_release_handoff_archive.adl_v02_runtime_evidence()
    return pinned_acceptance, current_acceptance, runtime_evidence


def assert_positive_mutation_fails(mutator, expected_path: str, context: tuple[dict, dict], scenario_index: int = 0) -> None:
    scenarios = json.loads(SCENARIOS.read_text())
    positive = beta_release_handoff_archive.merge_scenario(scenarios["defaults"], scenarios["scenarios"][scenario_index])
    mutator(positive)
    result = beta_release_handoff_archive.build_result(positive, *context)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_handoff()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-release-handoff-archive"
    assert doc["issue"] == 264
    assert doc["refreshIssue"] == 337
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["boundaries"]["releaseHandoffArchive"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    evidence = doc["sourcePackageEvidence"]["acceptanceBundle"]
    assert evidence["source"] == "tests/fixtures/beta-activation-acceptance.json"
    assert evidence["status"] == "pass"
    assert evidence["currentEvidenceMatchesPinned"] is True
    runtime_evidence = doc["sourcePackageEvidence"]["adlV02RuntimeEvidence"]
    assert runtime_evidence["source"] == "tests/fixtures/local-executable-runtime-prototype.json"
    assert runtime_evidence["boundaries"] == {
        "deterministicLocalFixturesOnly": True,
        "liveRuntimeActivation": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
        "paymentAccess": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "deploymentPublished": False,
    }
    assert runtime_evidence["validRuntimeExample"] == {
        "id": "adl-v02-memory-observability-dry-run",
        "adl": "examples/v0.2/memory-observability-agent.yaml",
        "command": "python scripts/run_local_agent.py examples/v0.2/memory-observability-agent.yaml",
        "status": "pass",
        "exitCode": 0,
        "completionStatus": "pass",
        "safetyGate": "supported-adl-v02-local-runtime",
    }
    diagnostic_sample = runtime_evidence["invalidDiagnosticSample"]
    assert diagnostic_sample["id"] == "invalid-adl-v02-payment-diagnostics"
    assert diagnostic_sample["adl"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"
    assert diagnostic_sample["status"] == "pass"
    assert diagnostic_sample["exitCode"] == 1
    assert diagnostic_sample["stableFields"] == ["code", "severity", "category", "path", "line", "column"]
    assert diagnostic_sample["diagnostics"] == [
        {
            "code": "adl_v0_2_schema.required.extensions_x402_intents_0_authority",
            "severity": "error",
            "category": "payment",
            "path": "extensions.x402.intents.0.authority",
            "line": 22,
            "column": 9,
        }
    ]

    assert doc["summary"] == {
        "acceptedArchives": 18,
        "holdArchives": 1,
        "rollbackRequiredArchives": 3,
        "positiveScenarios": 3,
        "negativeScenarios": 19,
        "failClosedScenarios": 19,
    }
    results = {result["id"]: result for result in doc["results"]}
    expected_handoff_status = {
        "release-handoff-accepted-pass": "handoff-accepted",
        "release-handoff-hold-pass": "handoff-held",
        "release-handoff-rollback-required-pass": "handoff-rollback-required",
    }
    for result_id, handoff_status in expected_handoff_status.items():
        result = results[result_id]
        assert result["status"] == "pass"
        assert result["handoffStatus"] == handoff_status
        assert result["releaseId"] == "reddiagent-beta-0"
        assert result["selectedAdlPath"] == "examples/tool-agent.yaml"
        assert result["sourceAcceptanceBundlePath"] == "tests/fixtures/beta-activation-acceptance.json"
        assert result["sourceRehearsalPackagePath"] == "tests/fixtures/beta-activation-rehearsal.json"
        assert result["sourcePreflightPackagePath"] == "tests/fixtures/beta-activation-preflight.json"
        assert result["sourceDecisionPackagePath"] == "tests/fixtures/beta-operator-decision-package.json"
        assert result["sourceReviewPackagePath"] == "tests/fixtures/beta-review-ui.json"
        assert result["sourceRuntimePackagePath"] == "tests/fixtures/beta-operator-dry-run-package.json"
        assert result["adlV02RuntimeEvidence"] == runtime_evidence
        assert result["operatorIdentity"] == "operator://local-beta"
        assert result["reviewerIdentity"] == "reviewer://oli-local-fixture"
        assert result["localApprovalFixture"].startswith("tests/fixtures/beta-activation-acceptance.json#")
        assert result["handoffTimestamp"].startswith("fixture://")
        assert result["sourceAcceptanceTimestamp"].startswith("fixture://")
        assert result["acceptedActivationCue"] == "activate://beta-0/local-rehearsal-only"
        assert result["rollbackCue"] == "rollback://beta-0/local-operator-control-drill"
        assert result["liveRuntimeEnablementClaim"] == "none"
        assert result["deploymentClaim"] == "none"
        assert result["activationClaim"] == "none"
        assert "No live runtime enablement" in result["nextStepHandoff"]
        assert "no deployment" in result["nextStepHandoff"]
        assert "no activation is claimed" in result["nextStepHandoff"]
        assert all(
            step["liveRuntimeEnabled"] is False
            and step["deploymentPublished"] is False
            and "--dry-run" in step["command"]
            for step in result["operatorTranscript"]
        )
        assert any(step["event"] == "handoff.no_runtime_or_deployment_claim" for step in result["operatorTranscript"])
        assert all(item["status"] == "pass" for item in result["operatorChecklist"])
        assert all(item["exists"] and item["sha256"] for item in result["evidenceHashes"])
        evidence_paths = {item["path"] for item in result["evidenceHashes"]}
        assert "tests/fixtures/local-executable-runtime-prototype.json" in evidence_paths
        assert "examples/v0.2/memory-observability-agent.yaml" in evidence_paths
        assert "examples/invalid/adl-v0.2-x402-missing-authority.yaml" in evidence_paths

    assert "--cue activate://beta-0/local-rehearsal-only" in results["release-handoff-accepted-pass"]["operatorTranscript"][1]["command"]
    assert results["release-handoff-hold-pass"]["operatorTranscript"][1]["event"] == "handoff.release_hold_archived"
    assert "--cue rollback://beta-0/local-operator-control-drill" in results["release-handoff-rollback-required-pass"]["operatorTranscript"][1]["command"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "sourceAcceptanceBundlePath" in finding_paths["missing-acceptance-evidence-denied"]
    assert "releaseId" in finding_paths["mismatched-release-id-denied"]
    assert "selectedAdlPath" in finding_paths["mismatched-adl-path-denied"]
    assert "operatorIdentity" in finding_paths["missing-operator-identity-denied"]
    assert "reviewerIdentity" in finding_paths["missing-reviewer-identity-denied"]
    assert "handoffTimestamp" in finding_paths["missing-handoff-timestamp-denied"]
    assert "acceptedActivationCue" in finding_paths["missing-accepted-activation-cue-denied"]
    assert "rollbackCue" in finding_paths["missing-rollback-cue-denied"]
    assert "rollbackDisableEvidence.disableVerified" in finding_paths["missing-rollback-disable-evidence-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-runtime-request-denied"]
    assert "boundaryStatus.liveRuntimeActivation" in finding_paths["live-runtime-request-denied"]
    assert "scenario.Authorization" in finding_paths["credential-like-payload-denied"]
    assert "devnetRequested" in finding_paths["devnet-request-denied"]
    assert "boundaryStatus.devnetAccess" in finding_paths["devnet-request-denied"]
    assert "mainnetRequested" in finding_paths["mainnet-production-claim-denied"]
    assert "productionEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "mainnetEnabled" in finding_paths["mainnet-production-claim-denied"]
    assert "deploymentRequested" in finding_paths["deployment-request-denied"]
    assert "deploymentClaimed" in finding_paths["deployment-request-denied"]
    assert "boundaryStatus.deploymentPublished" in finding_paths["deployment-request-denied"]
    assert "claimsActivationOccurred" in finding_paths["activation-occurred-claim-denied"]
    assert "claimsLiveRuntimeEnablement" in finding_paths["live-runtime-enable-claim-denied"]
    assert "nextStepHandoff" in finding_paths["handoff-missing-boundary-text-denied"]
    assert "nextStepHandoff" in finding_paths["handoff-contradictory-activation-denied"]
    assert "nextStepHandoff" in finding_paths["handoff-contradictory-deployment-denied"]

    context = source_context()
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorIdentity": ""}), "operatorIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"reviewerIdentity": "", "localApprovalFixture": ""}), "reviewerIdentity", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceAcceptanceBundlePath": "tests/fixtures/stale.json"}), "sourceAcceptanceBundlePath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"selectedAdlPath": "examples/simple-agent.yaml"}), "selectedAdlPath", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"handoffTimestamp": ""}), "handoffTimestamp", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"acceptedActivationCue": ""}), "acceptedActivationCue", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"liveRuntimeRequested": 1}), "liveRuntimeRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"devnetRequested": 1}), "devnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": 1}), "mainnetRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"deploymentRequested": 1}), "deploymentRequested", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"claimsActivationOccurred": 1}), "claimsActivationOccurred", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"apiKey": "redacted fixture marker"}), "scenario.apiKey", context)
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepHandoff": "No live runtime enablement is claimed."}), "nextStepHandoff", context)
    assert_positive_mutation_fails(
        lambda scenario: scenario.update(
            {"nextStepHandoff": "No live runtime enablement, no deployment, and no activation is claimed. Runtime activation completed."}
        ),
        "nextStepHandoff",
        context,
    )
    assert_positive_mutation_fails(
        lambda scenario: scenario.update(
            {"nextStepHandoff": "No live runtime enablement, no deployment, and no activation is claimed. Deployed to production."}
        ),
        "nextStepHandoff",
        context,
    )
    assert_positive_mutation_fails(
        lambda scenario: scenario["rollbackDisableEvidence"].update({"disableVerified": False}),
        "rollbackDisableEvidence.disableVerified",
        context,
        2,
    )
    assert_positive_mutation_fails(
        lambda scenario: scenario["boundaryStatus"].update({"credentialAccess": True}),
        "boundaryStatus.credentialAccess",
        context,
    )
    print("PASS beta release handoff archive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
