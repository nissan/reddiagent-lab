#!/usr/bin/env python3
"""Beta runtime activation canary runner checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-activation-canary-runner.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-activation-canary-runner-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_canary_runner as canary  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_canary(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_activation_canary_runner.py", *extra_args],
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
                if key in {"sourceCommit", "acceptedSourceCommit"}
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
    return canary.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = canary.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_activation_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads((ROOT / "tests" / "fixtures" / "beta-runtime-activation-evidence-gate.json").read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-runtime-activation-canary-artifact-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-activation-evidence-gate.json"
        artifact_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["activationEvidenceFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = canary.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_copied_activation_fixture_fails() -> None:
    scenario = positive_scenario()
    source = ROOT / "tests" / "fixtures" / "beta-runtime-activation-evidence-gate.json"
    with tempfile.TemporaryDirectory(prefix="beta-runtime-activation-canary-path-pin-") as tmp:
        artifact_path = Path(tmp) / "beta-runtime-activation-evidence-gate.json"
        artifact_path.write_text(source.read_text())
        scenario["activationEvidenceFixturePath"] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = canary.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert "activationEvidenceFixture.path" in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_canary()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-local-runtime-activation-canary-runner"
    assert doc["issue"] == 289
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [287]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "acceptCanaryVerdicts": 1,
        "holdVerdicts": 10,
        "rejectVerdicts": 1,
        "positiveScenarios": 2,
        "negativeScenarios": 10,
        "failClosedScenarios": 10,
    }
    for boundary, expected in {
        "deterministicLocalOnly": True,
        "inProcessRuntimeOnly": True,
        "serviceStarted": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
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
    positive = results["runtime-activation-canary-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept-canary"
    assert positive["canaryId"] == "reddiagent-beta-0-local-runtime-activation-canary"
    assert positive["activationEvidence"]["fixture"]["path"] == "tests/fixtures/beta-runtime-activation-evidence-gate.json"
    assert positive["activationEvidence"]["fixture"]["hashMatches"] is True
    assert positive["activationEvidence"]["acceptedResultId"] == "runtime-activation-evidence-accept-pass"
    assert positive["activationEvidence"]["acceptedVerdict"] == "activate-local"
    assert positive["activationEvidence"]["acceptedRuntimePath"]["adlPath"] == "examples/simple-agent.yaml"
    assert positive["selectedRuntimePath"]["reviewedCommand"] == "python scripts/run_local_agent.py examples/simple-agent.yaml"
    assert positive["canaryCommandTranscript"]["exitCode"] == 0
    assert positive["canaryCommandTranscript"]["traceEvents"] == gate.REQUIRED_TRACE_EVENTS
    assert positive["traceEvalSummary"]["completionStatus"] == "pass"
    assert positive["traceEvalSummary"]["requiredGateStatus"] == "pass"
    assert positive["traceEvalSummary"]["toolExecution"] is None
    assert positive["operatorControlStateBefore"]["runtimeEnabled"] is False
    assert positive["operatorControlStateAfter"]["runtimeEnabled"] is False
    assert positive["rollbackDisableDryRunProof"]["liveRuntimeEnabledAfterRollback"] is False
    assert "true live runtime/service activation" in positive["nextStepCue"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "activationEvidenceFixture.exists" in finding_paths["missing-activation-evidence-denied"]
    assert "activationEvidenceFixture.sha256" in finding_paths["stale-activation-evidence-hash-denied"]
    assert "canaryId" in finding_paths["wrong-canary-id-denied"]
    assert "operatorControlStateBefore.runtimeEnabled" in finding_paths["missing-before-control-denied"]
    assert "operatorControlStateAfter.runtimeEnabled" in finding_paths["missing-after-control-denied"]
    assert "rollbackDisableDryRunProof.rollbackCommand" in finding_paths["missing-rollback-proof-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[1]" in finding_paths["unsafe-command-denied"]
    assert "localCommands" in finding_paths["unsafe-command-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "liveRuntimeRequested" in finding_paths["live-rails-reject-denied"]
    assert "serviceStartRequested" in finding_paths["live-rails-reject-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-reject-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-reject-denied"]
    assert "paymentRequested" in finding_paths["live-rails-reject-denied"]
    assert "devnetRequested" in finding_paths["live-rails-reject-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-reject-denied"]
    assert "packageArchivePublishRequested" in finding_paths["live-rails-reject-denied"]
    assert results["live-rails-reject-denied"]["verdict"] == "reject"
    assert "nextStepCue" in finding_paths["unsafe-activation-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "activationEvidenceFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"activationEvidenceId": "stale"}), "activationEvidenceId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["solana-test-validator"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["docker pull reddiagent/test:latest"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["curl https://poppy-rafter-79h2.here.now/"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorControlStateAfter": {"runtimeEnabled": True}}), "operatorControlStateAfter.runtimeEnabled")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableDryRunProof": {"disableCommand": "live-runtime:disable"}}), "rollbackDisableDryRunProof.disableCommand")
    assert_copied_activation_fixture_fails()

    assert_activation_mutation_fails(lambda activation: activation.update({"status": "fail"}), "activationEvidenceFixture.status")
    assert_activation_mutation_fails(lambda activation: activation["results"][0].update({"verdict": "hold"}), "activationEvidenceFixture.results.verdict")
    assert_activation_mutation_fails(lambda activation: activation["results"][0]["selectedRuntimePath"].update({"adlPath": "examples/tool-agent.yaml"}), "activationEvidenceFixture.results.selectedRuntimePath")
    assert_activation_mutation_fails(lambda activation: activation["results"][0]["localCommandTranscript"].update({"traceEvents": []}), "activationEvidenceFixture.results.localCommandTranscript.traceEvents")
    assert_activation_mutation_fails(lambda activation: activation["results"][0].update({"nextStepCue": "Runtime activation completed and mainnet enabled."}), "activationEvidenceFixture.results.nextStepCue")
    assert_activation_mutation_fails(lambda activation: activation["results"][0].update({"credentialPayload": "token=abc123 secret=hunter2"}), "activationEvidenceFixture.results.credentialPayload")

    with tempfile.TemporaryDirectory(prefix="beta-runtime-activation-canary-out-") as tmp:
        written = run_canary("--canary-output-dir", tmp)
        paths = written["localCanaryEvidenceWrite"]
        manifest = Path(paths["manifestPath"])
        assert manifest.exists()
        loaded = json.loads(manifest.read_text())
        assert loaded["canaryId"] == positive["canaryId"]
        assert loaded["activationEvidence"]["fixture"]["hashMatches"] is True
        assert loaded["selectedRuntimePath"]["reviewedCommand"] == gate.LOCAL_COMMAND_PREFIX
        assert loaded["traceEvalSummary"]["completionStatus"] == "pass"
        assert paths["manifestSha256"] == gate.sha256_text(manifest.read_text())

    print("PASS beta runtime activation canary runner")
    return 0


if __name__ == "__main__":
    sys.exit(main())
