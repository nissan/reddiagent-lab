#!/usr/bin/env python3
"""Beta runtime activation evidence gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-activation-evidence-gate.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-activation-evidence-gate-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_activation_evidence_gate.py", *extra_args],
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
                if key == "sourceCommit"
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
    return gate.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_artifact_mutation_fails(source_path: Path, fixture_field: str, hash_path: str, mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads(source_path.read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-runtime-activation-artifact-") as tmp:
        artifact_path = Path(tmp) / source_path.name
        artifact_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario[fixture_field] = str(artifact_path)
        scenario["expectedArtifactHashes"] = [
            item for item in scenario["expectedArtifactHashes"] if item["path"] != hash_path
        ] + [{"path": str(artifact_path), "sha256": gate.digest(artifact_path)}]
        result = gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_gate()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-local-runtime-activation-evidence-gate"
    assert doc["issue"] == 287
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [285, 224]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "activateLocalVerdicts": 1,
        "holdVerdicts": 10,
        "rejectVerdicts": 1,
        "positiveScenarios": 2,
        "negativeScenarios": 10,
        "failClosedScenarios": 10,
    }
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["inProcessRuntimeOnly"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["providerApiAccess"] is False
    assert doc["boundaries"]["liveMcpInvocation"] is False
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["dockerStarted"] is False
    assert doc["boundaries"]["surfpoolStarted"] is False
    assert doc["boundaries"]["coolifyDeployment"] is False
    assert doc["boundaries"]["walletAccess"] is False
    assert doc["boundaries"]["paymentAccess"] is False
    assert doc["boundaries"]["facilitatorAccess"] is False
    assert doc["boundaries"]["settlementAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert doc["boundaries"]["packagePublished"] is False
    assert doc["boundaries"]["archivePublished"] is False
    assert doc["boundaries"]["publicPublished"] is False
    assert doc["boundaries"]["externalSpend"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["runtime-activation-evidence-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "activate-local"
    assert positive["activationEvidenceId"] == "reddiagent-beta-0-local-runtime-activation-evidence"
    assert positive["sourceSmoke"]["fixture"]["path"] == "tests/fixtures/beta-e2e-acceptance-smoke.json"
    assert positive["sourceSmoke"]["fixture"]["hashMatches"] is True
    assert positive["sourceSmoke"]["acceptedResultId"] == "e2e-acceptance-smoke-accept-pass"
    assert positive["sourceSmoke"]["acceptedVerdict"] == "accept"
    assert positive["selectedRuntimePath"]["adlPath"] == "examples/simple-agent.yaml"
    assert positive["selectedRuntimePath"]["runtimeFixture"]["path"] == "tests/fixtures/local-executable-runtime-prototype.json"
    assert positive["selectedRuntimePath"]["runtimeFixture"]["hashMatches"] is True
    assert positive["selectedRuntimePath"]["runtimeScenarioId"] == "simple-agent-dry-run"
    assert positive["localCommandTranscript"]["exitCode"] == 0
    assert positive["localCommandTranscript"]["traceEvents"] == gate.REQUIRED_TRACE_EVENTS
    assert positive["traceEvalSummary"]["completionStatus"] == "pass"
    assert positive["traceEvalSummary"]["requiredGateStatus"] == "pass"
    assert positive["traceEvalSummary"]["toolExecution"] is None
    assert positive["operatorControlState"]["runtimeEnabled"] is False
    assert positive["operatorControlState"]["disableSwitchAvailable"] is True
    assert positive["rollbackDisableProof"]["liveRuntimeEnabledAfterRollback"] is False
    assert "true live runtime/service activation" in positive["nextStepCue"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "e2eSmokeFixture.exists" in finding_paths["missing-e2e-artifact-denied"]
    assert "e2eSmokeFixture.sha256" in finding_paths["stale-e2e-hash-denied"]
    assert "runtimeFixture.sha256" in finding_paths["stale-runtime-hash-denied"]
    assert "selectedAdlPath" in finding_paths["wrong-runtime-path-denied"]
    assert "operatorControlState.disableSwitchAvailable" in finding_paths["missing-control-state-denied"]
    assert "rollbackDisableProof.rollbackCommand" in finding_paths["missing-rollback-proof-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-command-denied"]
    assert "localCommands[1]" in finding_paths["unsafe-command-denied"]
    assert "localCommands" in finding_paths["unsafe-command-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "liveRuntimeRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "serviceStartRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "dockerStartRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "liveMcpRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "paymentRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "devnetRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert "mainnetRequested" in finding_paths["runtime-container-live-rails-reject-denied"]
    assert results["runtime-container-live-rails-reject-denied"]["verdict"] == "reject"
    assert "nextStepCue" in finding_paths["unsafe-activation-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedArtifactHashes": []}), "e2eSmokeFixture.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"activationEvidenceId": "stale"}), "activationEvidenceId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["solana-test-validator"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["docker pull reddiagent/test:latest"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"localCommands": ["curl https://reddiagent-devnet.preview.reddi.tech/"]}), "localCommands[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorControlState": {"runtimeEnabled": True}}), "operatorControlState.manualApprovalRecorded")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableProof": {"disableCommand": "live-runtime:disable"}}), "rollbackDisableProof.disableCommand")

    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-e2e-acceptance-smoke.json",
        "e2eSmokeFixturePath",
        "tests/fixtures/beta-e2e-acceptance-smoke.json",
        lambda e2e: e2e.update({"status": "fail"}),
        "e2eSmokeFixture.status",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "beta-e2e-acceptance-smoke.json",
        "e2eSmokeFixturePath",
        "tests/fixtures/beta-e2e-acceptance-smoke.json",
        lambda e2e: e2e["results"][0].update({"verdict": "hold"}),
        "e2eSmokeFixture.results.verdict",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "local-executable-runtime-prototype.json",
        "runtimeFixturePath",
        "tests/fixtures/local-executable-runtime-prototype.json",
        lambda runtime: runtime.update({"status": "fail"}),
        "runtimeFixture.status",
    )
    assert_artifact_mutation_fails(
        ROOT / "tests" / "fixtures" / "local-executable-runtime-prototype.json",
        "runtimeFixturePath",
        "tests/fixtures/local-executable-runtime-prototype.json",
        lambda runtime: runtime["scenarios"][0].update({"toolExecution": {"mode": "local-fixture"}}),
        "runtimeFixture.scenarios.toolExecution",
    )

    with tempfile.TemporaryDirectory(prefix="beta-runtime-activation-out-") as tmp:
        written = run_gate("--evidence-output-dir", tmp)
        paths = written["localEvidenceWrite"]
        manifest = Path(paths["manifestPath"])
        assert manifest.exists()
        loaded = json.loads(manifest.read_text())
        assert loaded["activationEvidenceId"] == positive["activationEvidenceId"]
        assert loaded["sourceSmoke"]["fixture"]["hashMatches"] is True
        assert loaded["selectedRuntimePath"]["runtimeFixture"]["hashMatches"] is True
        assert loaded["traceEvalSummary"]["completionStatus"] == "pass"
        assert paths["manifestSha256"] == gate.sha256_text(manifest.read_text())

    print("PASS beta runtime activation evidence gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
