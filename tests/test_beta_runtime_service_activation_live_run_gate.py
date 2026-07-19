#!/usr/bin/env python3
"""Beta runtime service activation live-run gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-live-run-gate.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-live-run-gate-scenarios.json"
PINNED_293_FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-evidence-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_activation_live_run_gate as live_gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_service_activation_live_run_gate.py", *extra_args],
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
    return live_gate.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = live_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_293_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_293_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_293_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = live_gate.build_result(scenario, gate.source_commit())
    finally:
        PINNED_293_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_gate()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-runtime-service-activation-live-run-gate"
    assert doc["issue"] == 295
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "failClosedScenarios": 11,
        "holdVerdicts": 12,
        "negativeScenarios": 11,
        "positiveScenarios": 2,
        "rollbackVerdicts": 1,
    }
    for boundary, expected in live_gate.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["bounded-live-run-hold-pass"]
    evidence = positive["runEvidence"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "hold"
    assert evidence["sourceMergeCommit"] == live_gate.PINNED_293_MERGE_COMMIT
    assert evidence["prior293Evidence"]["fixture"]["path"] == live_gate.PINNED_293_FIXTURE_PATH
    assert evidence["prior293Evidence"]["fixture"]["sha256"] == live_gate.PINNED_293_FIXTURE_SHA256
    assert evidence["prior293Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior293Evidence"]["report"]["path"] == live_gate.PINNED_293_REPORT_PATH
    assert evidence["prior293Evidence"]["report"]["sha256"] == live_gate.PINNED_293_REPORT_SHA256
    assert evidence["prior293Evidence"]["approvalPacketFixture"]["sha256"] == live_gate.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["prior293Evidence"]["selectedRuntimePath"]["adlPath"] == "examples/simple-agent.yaml"
    assert evidence["activationScope"] == {
        "adlPath": "examples/simple-agent.yaml",
        "reviewedCommand": "python scripts/run_local_agent.py examples/simple-agent.yaml",
        "toolExecution": None,
        "liveMutation": False,
        "networkExposure": "none",
    }
    assert evidence["boundedTranscript"]["mode"] == "bounded-local-live-run-substitute"
    assert evidence["traceEvalSummary"]["completionStatus"] == "pass"
    assert evidence["traceEvalSummary"]["toolExecution"] is None
    assert all(evidence["currentOperatorApprovalState"][name] is True for name in live_gate.REQUIRED_OPERATOR_APPROVALS)
    assert evidence["operatorDecision"]["decision"] == "hold"
    assert evidence["operatorDecision"]["liveActionAuthorized"] is False
    assert evidence["rollbackDisableVerification"]["liveRuntimeEnabledAfterRollback"] is False
    assert evidence["riskVerdict"] == "hold-before-actual-service-activation"
    assert "actual service activation remains blocked" in evidence["nextStepCue"]
    assert results["bounded-live-run-rollback-pass"]["verdict"] == "rollback"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior293Fixture.expectedSha256" in finding_paths["stale-prior-293-fixture-denied"]
    assert "prior293Report.expectedSha256" in finding_paths["stale-prior-293-report-denied"]
    assert "currentOperatorApprovalState.separate_live_activation_run_approval" in finding_paths["missing-current-operator-approval-denied"]
    assert "activationScope" in finding_paths["wrong-activation-scope-denied"]
    assert "actualServiceMutation" in finding_paths["unsafe-service-mutation-denied"]
    assert "operatorDecision" in finding_paths["unsafe-service-mutation-denied"]
    assert "boundedTranscript" in finding_paths["unsafe-transcript-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-transcript-denied"]
    assert "traceEvalSummary" in finding_paths["missing-trace-eval-denied"]
    assert "rollbackDisableVerification.disableCommand" in finding_paths["missing-rollback-disable-denied"]
    assert "rollbackDisableVerification.liveRuntimeEnabledAfterRollback" in finding_paths["missing-rollback-disable-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-payload-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-denied"]
    assert "coolifyDeploymentRequested" in finding_paths["live-rails-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-denied"]
    assert "paymentRequested" in finding_paths["live-rails-denied"]
    assert "devnetRequested" in finding_paths["live-rails-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-denied"]
    assert "activationCompleted" in finding_paths["unsafe-completion-claim-denied"]
    assert "nextStepCue" in finding_paths["unsafe-completion-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceMergeCommit": "bad"}), "sourceMergeCommit")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "private_key"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorDecision": {"decision": "activate", "liveActionAuthorized": True}}), "operatorDecision")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"boundedTranscript": {"mode": "live-service", "command": "launchctl start reddiagent", "exitCode": 0}}), "boundedTranscript")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"traceEvalSummary": {}}), "traceEvalSummary")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableVerification": {}}), "rollbackDisableVerification.disableCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Activation completed."}), "nextStepCue")

    assert_prior_293_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior293Fixture.status")
    assert_prior_293_mutation_fails(lambda prior: prior.update({"follows": [291]}), "prior293Fixture.follows")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "activated"}), "prior293Fixture.results.verdict")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["approvalPacketEvidence"]["fixture"].update({"sha256": "bad"}), "prior293Fixture.results.approvalPacketEvidence.fixture")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["selectedRuntimePath"].update({"adlPath": "examples/tool-agent.yaml"}), "prior293Fixture.results.selectedRuntimePath")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["operatorApprovalsRecorded"].update({"runtime_owner_approval": False}), "prior293Fixture.results.operatorApprovalsRecorded.runtime_owner_approval")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"traceEvalSummary": {}}), "prior293Fixture.results.traceEvalSummary")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["rollbackDisableVerification"].update({"liveRuntimeEnabledAfterRollback": True}), "prior293Fixture.results.rollbackDisableVerification")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["activationDecision"].update({"liveActionAuthorized": True}), "prior293Fixture.results.activationDecision.liveActionAuthorized")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["boundedRunTranscript"].update({"mode": "live-service"}), "prior293Fixture.results.boundedRunTranscript.mode")
    assert_prior_293_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"riskVerdict": "activate"}), "prior293Fixture.results.riskVerdict")

    print("PASS beta runtime service activation live-run gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
