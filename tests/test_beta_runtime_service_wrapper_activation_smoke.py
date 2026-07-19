#!/usr/bin/env python3
"""Beta runtime service-wrapper activation smoke checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-wrapper-activation-smoke.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-runtime-service-wrapper-activation-smoke-scenarios.json"
PINNED_295_FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-activation-live-run-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_runtime_activation_evidence_gate as gate  # noqa: E402
import beta_runtime_service_wrapper_activation_smoke as wrapper_smoke  # noqa: E402


def run_smoke(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_runtime_service_wrapper_activation_smoke.py", *extra_args],
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
    return wrapper_smoke.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = wrapper_smoke.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_295_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_295_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_295_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = wrapper_smoke.build_result(scenario, gate.source_commit())
    finally:
        PINNED_295_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_smoke()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-runtime-service-wrapper-activation-smoke"
    assert doc["issue"] == 297
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [295, 293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "failClosedScenarios": 11,
        "holdVerdicts": 12,
        "negativeScenarios": 11,
        "positiveScenarios": 2,
        "rollbackVerdicts": 1,
    }
    for boundary, expected in wrapper_smoke.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["service-wrapper-hold-pass"]
    evidence = positive["runEvidence"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "hold"
    assert evidence["sourceMergeCommit"] == wrapper_smoke.PINNED_295_MERGE_COMMIT
    assert evidence["prior295Evidence"]["fixture"]["path"] == wrapper_smoke.PINNED_295_FIXTURE_PATH
    assert evidence["prior295Evidence"]["fixture"]["sha256"] == wrapper_smoke.PINNED_295_FIXTURE_SHA256
    assert evidence["prior295Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior295Evidence"]["report"]["path"] == wrapper_smoke.PINNED_295_REPORT_PATH
    assert evidence["prior295Evidence"]["report"]["sha256"] == wrapper_smoke.PINNED_295_REPORT_SHA256
    assert evidence["prior295Evidence"]["prior293Fixture"]["sha256"] == wrapper_smoke.PINNED_293_FIXTURE_SHA256
    assert evidence["prior295Evidence"]["approvalPacketFixture"]["sha256"] == wrapper_smoke.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["activationScope"] == {
        "adlPath": "examples/simple-agent.yaml",
        "reviewedCommand": "python scripts/run_local_agent.py examples/simple-agent.yaml",
        "serviceWrapper": "local-ephemeral-json-state",
        "toolExecution": None,
        "liveMutation": False,
        "networkExposure": "none",
    }
    state = evidence["serviceWrapperState"]
    assert state["before"]["enabled"] is False
    assert state["afterEnable"]["enabled"] is True
    assert state["afterEnable"]["externalProcessPid"] is None
    assert state["afterDisable"]["enabled"] is False
    assert state["afterRollback"]["enabled"] is False
    assert evidence["boundedTranscript"]["mode"] == "local-service-wrapper-state-smoke"
    assert evidence["traceEvalSummary"]["completionStatus"] == "pass"
    assert evidence["traceEvalSummary"]["toolExecution"] is None
    assert all(evidence["currentOperatorApprovalState"][name] is True for name in wrapper_smoke.REQUIRED_OPERATOR_APPROVALS)
    assert evidence["operatorDecision"]["decision"] == "hold"
    assert evidence["operatorDecision"]["liveActionAuthorized"] is False
    assert evidence["rollbackDisableVerification"]["wrapperEnabledAfterRollback"] is False
    assert evidence["rollbackDisableVerification"]["externalProcessStarted"] is False
    assert evidence["auditTrail"] == [
        "state-before-disabled",
        "enable-local-wrapper-state",
        "disable-local-wrapper-state",
        "rollback-local-wrapper-state",
    ]
    assert evidence["riskVerdict"] == "hold-before-external-service-mutation"
    assert "separate bounded operator run" in evidence["nextStepCue"]
    assert results["service-wrapper-rollback-pass"]["verdict"] == "rollback"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior295Fixture.expectedSha256" in finding_paths["stale-prior-295-fixture-denied"]
    assert "prior295Report.expectedSha256" in finding_paths["stale-prior-295-report-denied"]
    assert "currentOperatorApprovalState.separate_live_activation_run_approval" in finding_paths["missing-current-operator-approval-denied"]
    assert "activationScope" in finding_paths["wrong-wrapper-scope-denied"]
    assert "serviceWrapperState.afterEnable" in finding_paths["unsafe-service-state-denied"]
    assert "externalProcessStarted" in finding_paths["unsafe-service-state-denied"]
    assert "boundedTranscript" in finding_paths["unsafe-transcript-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-transcript-denied"]
    assert "traceEvalSummary" in finding_paths["missing-trace-eval-denied"]
    assert "rollbackDisableVerification.disableCommand" in finding_paths["missing-rollback-disable-denied"]
    assert "rollbackDisableVerification.wrapperEnabledAfterRollback" in finding_paths["missing-rollback-disable-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-payload-denied"]
    assert "hostMutationRequested" in finding_paths["live-rails-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-denied"]
    assert "coolifyDeploymentRequested" in finding_paths["live-rails-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-denied"]
    assert "providerApiAccessRequested" in finding_paths["live-rails-denied"]
    assert "paymentRequested" in finding_paths["live-rails-denied"]
    assert "devnetRequested" in finding_paths["live-rails-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-denied"]
    assert "activationCompleted" in finding_paths["unsafe-completion-claim-denied"]
    assert "nextStepCue" in finding_paths["unsafe-completion-claim-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceMergeCommit": "bad"}), "sourceMergeCommit")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "private_key"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorDecision": {"decision": "activate", "liveActionAuthorized": True}}), "operatorDecision")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"boundedTranscript": {"mode": "host-service", "command": "launchctl start reddiagent", "exitCode": 0}}), "boundedTranscript")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"traceEvalSummary": {}}), "traceEvalSummary")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableVerification": {}}), "rollbackDisableVerification.disableCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Activation completed."}), "nextStepCue")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["afterEnable"].update({"mutationScope": "host-process"}), "serviceWrapperState.afterEnable.mutationScope")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["afterDisable"].update({"externalProcessPid": 12345}), "serviceWrapperState.afterDisable.externalProcessPid")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["afterRollback"].update({"externalProcessPid": 12345}), "serviceWrapperState.afterRollback.externalProcessPid")

    assert_prior_295_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior295Fixture.status")
    assert_prior_295_mutation_fails(lambda prior: prior.update({"follows": [293]}), "prior295Fixture.follows")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "activate"}), "prior295Fixture.results.verdict")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior293Evidence"]["fixture"].update({"sha256": "bad"}), "prior295Fixture.results.prior293Evidence.fixture")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior293Evidence"]["approvalPacketFixture"].update({"sha256": "bad"}), "prior295Fixture.results.prior293Evidence.approvalPacketFixture")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["activationScope"].update({"adlPath": "examples/tool-agent.yaml"}), "prior295Fixture.results.activationScope")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["currentOperatorApprovalState"].update({"runtime_owner_approval": False}), "prior295Fixture.results.currentOperatorApprovalState.runtime_owner_approval")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"traceEvalSummary": {}}), "prior295Fixture.results.traceEvalSummary")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["rollbackDisableVerification"].update({"liveRuntimeEnabledAfterRollback": True}), "prior295Fixture.results.rollbackDisableVerification")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["operatorDecision"].update({"liveActionAuthorized": True}), "prior295Fixture.results.operatorDecision")
    assert_prior_295_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"riskVerdict": "activate"}), "prior295Fixture.results.riskVerdict")

    print("PASS beta runtime service-wrapper activation smoke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
