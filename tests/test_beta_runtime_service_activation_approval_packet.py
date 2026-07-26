#!/usr/bin/env python3
"""Beta runtime service activation approval packet checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-approval-packet.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-approval-packet-scenarios.json"
PINNED_CANARY = ROOT / "tests" / "fixtures" / "beta-runtime-activation-canary-runner.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_activation_approval_packet as packet  # noqa: E402


def run_packet(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_service_activation_approval_packet.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def normalize_dynamic(value):
    if isinstance(value, dict):
        return {
            key: (
                "<current-git-head>"
                if key in {"sourceCommit"}
                else "<runtime-stdout-sha>"
                if key == "stdoutSha256"
                else "<runtime-stderr-sha>"
                if key == "stderrSha256"
                else normalize_dynamic(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_dynamic(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return packet.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = packet.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_canary_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads(PINNED_CANARY.read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-runtime-service-approval-canary-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-activation-canary-runner.json"
        artifact_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["canaryEvidenceFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = packet.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_copied_canary_fixture_fails() -> None:
    scenario = positive_scenario()
    with tempfile.TemporaryDirectory(prefix="beta-runtime-service-approval-path-pin-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-activation-canary-runner.json"
        artifact_path.write_text(PINNED_CANARY.read_text())
        scenario["canaryEvidenceFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = packet.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert "canaryEvidenceFixture.path" in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_packet()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-runtime-service-activation-approval-packet"
    assert doc["issue"] == 291
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "approvalPacketReadyVerdicts": 1,
        "holdVerdicts": 11,
        "rejectVerdicts": 1,
        "positiveScenarios": 2,
        "negativeScenarios": 11,
        "failClosedScenarios": 11,
    }
    for boundary, expected in {
        "deterministicLocalOnly": True,
        "approvalPacketOnly": True,
        "requiresSeparateLiveActivationRun": True,
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
    positive = results["runtime-service-approval-packet-ready-pass"]
    packet_doc = positive["approvalPacket"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "approval-packet-ready"
    assert packet_doc["approvalPacketId"] == "reddiagent-beta-0-runtime-service-activation-approval-packet"
    assert packet_doc["sourceEvidenceHashes"]["canaryFixture"]["path"] == "tests/fixtures/beta-runtime-activation-canary-runner.json"
    assert packet_doc["sourceEvidenceHashes"]["canaryFixture"]["hashMatches"] is True
    assert packet_doc["sourceEvidenceHashes"]["canaryFixture"]["sha256"] == "228a36887aefa75d9947e76c636c328c8aa8495b474f3266b56af563604ca7e6"
    assert packet_doc["sourceEvidenceHashes"]["activationEvidenceFixture"]["hashMatches"] is True
    assert packet_doc["sourceEvidenceHashes"]["e2eSmokeFixture"]["hashMatches"] is True
    assert packet_doc["selectedRuntimePath"] == {
        "adlPath": "examples/simple-agent.yaml",
        "reviewedCommand": "python scripts/run_local_agent.py examples/simple-agent.yaml",
        "toolExecution": None,
    }
    assert tuple(packet_doc["requiredOperatorApprovals"]) == packet.REQUIRED_OPERATOR_APPROVALS
    assert [item["name"] for item in packet_doc["redactedEnvSecretRequirements"]] == list(packet.REQUIRED_ENV_SECRET_NAMES)
    assert all(item["value"] == "<redacted>" for item in packet_doc["redactedEnvSecretRequirements"])
    assert packet_doc["rollbackDisablePlan"]["liveRuntimeEnabledAfterRollback"] is False
    assert packet_doc["dryRunCommandTranscript"]["exitCode"] == 0
    assert packet_doc["traceEvalSummary"]["completionStatus"] == "pass"
    assert packet_doc["operatorControlStateBefore"]["runtimeEnabled"] is False
    assert packet_doc["operatorControlStateAfter"]["runtimeEnabled"] is False
    assert packet_doc["riskVerdict"] == "approval-packet-ready"
    assert packet_doc["stopCue"].startswith("STOP:")
    assert "separate explicit live activation" in packet_doc["stopCue"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "canaryEvidenceFixture.exists" in finding_paths["missing-canary-evidence-denied"]
    assert "canaryEvidenceFixture.sha256" in finding_paths["stale-canary-evidence-hash-denied"]
    assert "approvalPacketId" in finding_paths["wrong-packet-id-denied"]
    assert "requiredOperatorApprovals" in finding_paths["missing-operator-approval-denied"]
    assert "redactedEnvSecretNames" in finding_paths["env-secret-value-denied"]
    assert "liveActionChecklist" in finding_paths["missing-live-action-checklist-denied"]
    assert "localCommands[1]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[2]" in finding_paths["unsafe-command-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-rails-reject-denied"]
    assert "liveServiceActivationRequested" in finding_paths["live-rails-reject-denied"]
    assert "serviceStartRequested" in finding_paths["live-rails-reject-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-reject-denied"]
    assert "coolifyDeploymentRequested" in finding_paths["live-rails-reject-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-reject-denied"]
    assert "paymentRequested" in finding_paths["live-rails-reject-denied"]
    assert "devnetRequested" in finding_paths["live-rails-reject-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-reject-denied"]
    assert "packageArchivePublishRequested" in finding_paths["live-rails-reject-denied"]
    assert results["live-rails-reject-denied"]["verdict"] == "reject"
    assert "stopCue" in finding_paths["unsafe-activation-claim-denied"]
    assert "rollbackDisablePlan.disableCommand" in finding_paths["missing-rollback-plan-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "canaryEvidenceFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"canaryId": "stale"}), "canaryId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "token=abc123"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"redactedEnvSecretNames": ["RUNTIME_SECRET=value"]}), "redactedEnvSecretNames")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["docker pull reddiagent/test:latest"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["curl https://frosty-prism-5q6j.here.now/"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"riskVerdict": "activation-complete"}), "riskVerdict")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"stopCue": "Runtime activation completed."}), "stopCue")
    assert_copied_canary_fixture_fails()

    assert_canary_mutation_fails(lambda canary_doc: canary_doc.update({"status": "fail"}), "canaryEvidenceFixture.status")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0].update({"verdict": "hold"}), "canaryEvidenceFixture.results.verdict")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["selectedRuntimePath"].update({"adlPath": "examples/tool-agent.yaml"}), "canaryEvidenceFixture.results.selectedRuntimePath")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["canaryCommandTranscript"].update({"traceEvents": []}), "canaryEvidenceFixture.results.canaryCommandTranscript.traceEvents")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["operatorControlStateAfter"].update({"runtimeEnabled": True}), "canaryEvidenceFixture.results.operatorControlStateAfter")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0].update({"credentialPayload": "private key"}), "canaryEvidenceFixture.results.credentialPayload")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["activationEvidence"].update({"acceptedSourceSmoke": None}), "canaryEvidenceFixture.results.activationEvidence.upstreamHashes")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["activationEvidence"].update({"fixture": None}), "canaryEvidenceFixture.results.activationEvidence.fixture")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["activationEvidence"]["fixture"].update({"hashMatches": False}), "canaryEvidenceFixture.results.activationEvidence.fixture")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["activationEvidence"]["acceptedSourceSmoke"].update({"fixture": None}), "canaryEvidenceFixture.results.activationEvidence.acceptedSourceSmoke.fixture")
    assert_canary_mutation_fails(lambda canary_doc: canary_doc["results"][0]["activationEvidence"]["acceptedSourceSmoke"]["fixture"].update({"hashMatches": False}), "canaryEvidenceFixture.results.activationEvidence.acceptedSourceSmoke.fixture")

    with tempfile.TemporaryDirectory(prefix="beta-runtime-service-approval-out-") as tmp:
        written = run_packet("--packet-output-dir", tmp)
        paths = written["localApprovalPacketWrite"]
        manifest = Path(paths["manifestPath"])
        assert manifest.exists()
        loaded = json.loads(manifest.read_text())
        assert loaded["approvalPacketId"] == packet_doc["approvalPacketId"]
        assert loaded["sourceEvidenceHashes"]["canaryFixture"]["hashMatches"] is True
        assert loaded["selectedRuntimePath"]["reviewedCommand"] == gate.LOCAL_COMMAND_PREFIX
        assert loaded["riskVerdict"] == "approval-packet-ready"
        assert loaded["stopCue"].startswith("STOP:")
        assert paths["manifestSha256"] == gate.sha256_text(manifest.read_text())

    print("PASS beta runtime service activation approval packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
