#!/usr/bin/env python3
"""Beta runtime service activation evidence gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-evidence-gate.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-evidence-gate-scenarios.json"
PINNED_PACKET = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-approval-packet.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_activation_evidence_gate as service_gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_service_activation_evidence_gate.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def normalize_dynamic(value):
    if isinstance(value, dict):
        return {
            key: "<current-git-head>" if key == "sourceCommit" else normalize_dynamic(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_dynamic(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return service_gate.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = service_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_packet_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads(PINNED_PACKET.read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-runtime-service-evidence-packet-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-service-activation-approval-packet.json"
        artifact_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["approvalPacketFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = service_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_copied_packet_fixture_fails() -> None:
    scenario = positive_scenario()
    with tempfile.TemporaryDirectory(prefix="beta-runtime-service-evidence-path-pin-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-service-activation-approval-packet.json"
        artifact_path.write_text(PINNED_PACKET.read_text())
        scenario["approvalPacketFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = service_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert "approvalPacketFixture.path" in {finding["path"] for finding in result["findings"]}


def assert_same_path_rehashed_packet_fixture_fails() -> None:
    scenario = positive_scenario()
    original = PINNED_PACKET.read_text()
    source = json.loads(original)
    source["oliRegressionMarker"] = "same-path rehashed #291 packet must not pass"
    mutated = json.dumps(source, indent=2, sort_keys=True) + "\n"
    try:
        PINNED_PACKET.write_text(mutated)
        scenario["expectedArtifactHashes"] = [
            {"path": "tests/fixtures/beta-runtime-service-activation-approval-packet.json", "sha256": gate.digest(PINNED_PACKET)}
        ]
        result = service_gate.build_result(scenario, gate.source_commit())
    finally:
        PINNED_PACKET.write_text(original)
    assert result["status"] == "fail"
    finding_paths = {finding["path"] for finding in result["findings"]}
    assert "approvalPacketFixture.expectedSha256" in finding_paths
    assert "approvalPacketFixture.sha256" in finding_paths


def main() -> int:
    doc = run_gate()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-runtime-service-activation-evidence-gate"
    assert doc["issue"] == 293
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "failClosedScenarios": 12,
        "holdForLiveRunVerdicts": 1,
        "holdVerdicts": 10,
        "negativeScenarios": 12,
        "positiveScenarios": 2,
        "rejectVerdicts": 2,
        "rollbackVerdicts": 1,
    }
    for boundary, expected in {
        "deterministicLocalOnly": True,
        "dryRunSubstituteOnly": True,
        "actualServiceMutation": False,
        "serviceStarted": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
        "hostedFetch": False,
        "liveMcpInvocation": False,
        "liveRuntimeActivation": False,
        "dockerStarted": False,
        "surfpoolStarted": False,
        "coolifyDeployment": False,
        "walletAccess": False,
        "paymentAccess": False,
        "facilitatorAccess": False,
        "settlementAccess": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "deploymentPublished": False,
        "packagePublished": False,
        "archivePublished": False,
        "publicPublished": False,
        "externalSpend": False,
    }.items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["runtime-service-activation-evidence-hold-pass"]
    evidence = positive["runEvidence"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "hold-for-live-run"
    assert evidence["approvalPacketEvidence"]["fixture"]["path"] == "tests/fixtures/beta-runtime-service-activation-approval-packet.json"
    assert evidence["approvalPacketEvidence"]["fixture"]["sha256"] == service_gate.PINNED_APPROVAL_PACKET_SHA256
    assert evidence["approvalPacketEvidence"]["fixture"]["hashMatches"] is True
    source_hashes = evidence["approvalPacketEvidence"]["sourceEvidenceHashes"]
    assert source_hashes["canaryFixture"]["hashMatches"] is True
    assert source_hashes["activationEvidenceFixture"]["hashMatches"] is True
    assert source_hashes["e2eSmokeFixture"]["hashMatches"] is True
    assert source_hashes["canaryFixture"]["path"] == "tests/fixtures/beta-runtime-activation-canary-runner.json"
    assert source_hashes["activationEvidenceFixture"]["path"] == "tests/fixtures/beta-runtime-activation-evidence-gate.json"
    assert source_hashes["e2eSmokeFixture"]["path"] == "tests/fixtures/beta-e2e-acceptance-smoke.json"
    assert evidence["selectedRuntimePath"] == {
        "adlPath": "examples/simple-agent.yaml",
        "reviewedCommand": "python scripts/run_local_agent.py examples/simple-agent.yaml",
        "toolExecution": None,
    }
    assert set(evidence["operatorApprovalsRecorded"]) == set(service_gate.REQUIRED_OPERATOR_APPROVALS)
    assert all(evidence["operatorApprovalsRecorded"][name] is True for name in service_gate.REQUIRED_OPERATOR_APPROVALS)
    assert evidence["activationDecision"]["decision"] == "hold"
    assert evidence["activationDecision"]["liveActionAuthorized"] is False
    assert evidence["boundedRunTranscript"]["mode"] == "dry-run-substitute"
    assert evidence["boundedRunTranscript"]["exitCode"] == 0
    assert evidence["traceEvalSummary"]["completionStatus"] == "pass"
    assert evidence["traceEvalSummary"]["toolExecution"] is None
    assert evidence["rollbackDisableVerification"]["liveRuntimeEnabledAfterRollback"] is False
    assert evidence["riskVerdict"] == "hold-for-separate-live-run"
    assert "live service activation still requires" in evidence["nextStepCue"]
    assert evidence["boundaries"]["actualServiceMutation"] is False
    assert results["runtime-service-activation-evidence-rollback-pass"]["verdict"] == "rollback"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "approvalPacketFixture.exists" in finding_paths["missing-approval-packet-denied"]
    assert "approvalPacketFixture.expectedSha256" in finding_paths["stale-approval-packet-hash-denied"]
    assert "runEvidenceId" in finding_paths["wrong-run-id-denied"]
    assert "operatorApprovalsRecorded.separate_live_activation_run_approval" in finding_paths["missing-operator-approval-record-denied"]
    assert "preflightChecklist" in finding_paths["thin-preflight-denied"]
    assert "activationDecision.decision" in finding_paths["unsafe-live-decision-denied"]
    assert "activationDecision.liveActionAuthorized" in finding_paths["unsafe-live-decision-denied"]
    assert "liveServiceActivationRequested" in finding_paths["unsafe-live-decision-denied"]
    assert "serviceStartRequested" in finding_paths["unsafe-live-decision-denied"]
    assert "boundedRunTranscript.mode" in finding_paths["unsafe-transcript-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-transcript-denied"]
    assert "traceEvalSummary" in finding_paths["missing-trace-eval-denied"]
    assert "rollbackDisableVerification.disableCommand" in finding_paths["missing-rollback-verification-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-payload-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-denied"]
    assert "coolifyDeploymentRequested" in finding_paths["live-rails-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-denied"]
    assert "paymentRequested" in finding_paths["live-rails-denied"]
    assert "devnetRequested" in finding_paths["live-rails-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-denied"]
    assert "packageArchivePublishRequested" in finding_paths["live-rails-denied"]
    assert "activationCompleted" in finding_paths["unsafe-completion-claim-denied"]
    assert "nextStepCue" in finding_paths["unsafe-completion-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "approvalPacketFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "private_key"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"activationDecision": {"decision": "activate", "liveActionAuthorized": True}}), "activationDecision.decision")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"boundedRunTranscript": {"mode": "live-service", "command": "launchctl start", "exitCode": 0}}), "boundedRunTranscript.mode")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"traceEvalSummary": {}}), "traceEvalSummary")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableVerification": {}}), "rollbackDisableVerification.disableCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Activation completed."}), "nextStepCue")
    assert_copied_packet_fixture_fails()
    assert_same_path_rehashed_packet_fixture_fails()

    assert_packet_mutation_fails(lambda packet_doc: packet_doc.update({"status": "fail"}), "approvalPacketFixture.status")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc.update({"follows": [291]}), "approvalPacketFixture.follows")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0].update({"verdict": "hold"}), "approvalPacketFixture.results.verdict")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"]["selectedRuntimePath"].update({"adlPath": "examples/tool-agent.yaml"}), "approvalPacketFixture.results.selectedRuntimePath")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"].update({"requiredOperatorApprovals": []}), "approvalPacketFixture.results.requiredOperatorApprovals")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"]["redactedEnvSecretRequirements"][0].update({"value": "secret"}), "approvalPacketFixture.results.redactedEnvSecretRequirements.value")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"]["rollbackDisablePlan"].update({"liveRuntimeEnabledAfterRollback": True}), "approvalPacketFixture.results.rollbackDisablePlan.liveRuntimeEnabledAfterRollback")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"].update({"stopCue": "Activation completed."}), "approvalPacketFixture.results.stopCue")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"]["sourceEvidenceHashes"]["canaryFixture"].update({"hashMatches": False}), "approvalPacketFixture.results.sourceEvidenceHashes.canaryFixture")
    assert_packet_mutation_fails(lambda packet_doc: packet_doc["results"][0]["approvalPacket"]["sourceEvidenceHashes"].update({"acceptedE2eSmokeSha256": ""}), "approvalPacketFixture.results.sourceEvidenceHashes.upstream")

    print("PASS beta runtime service activation evidence gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
