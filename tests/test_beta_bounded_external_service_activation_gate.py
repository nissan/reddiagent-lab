#!/usr/bin/env python3
"""Bounded external-service activation gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-bounded-external-service-activation-gate.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-bounded-external-service-activation-gate-scenarios.json"
PINNED_299_FIXTURE = ROOT / "tests" / "fixtures" / "beta-runtime-service-wrapper-operator-run-package.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_bounded_external_service_activation_gate as activation_gate  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_bounded_external_service_activation_gate.py", *extra_args],
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
    return activation_gate.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = activation_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_299_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_299_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_299_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = activation_gate.build_result(scenario, gate.source_commit())
    finally:
        PINNED_299_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_gate()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-bounded-external-service-activation-gate"
    assert doc["issue"] == 301
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [299, 297, 295, 293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "failClosedScenarios": 11,
        "holdVerdicts": 12,
        "negativeScenarios": 11,
        "positiveScenarios": 2,
        "rollbackVerdicts": 1,
    }
    for boundary, expected in activation_gate.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["bounded-external-activation-hold-pass"]
    evidence = positive["runEvidence"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "hold"
    assert evidence["sourceMergeCommit"] == activation_gate.PINNED_299_MERGE_COMMIT
    assert evidence["prior299Evidence"]["fixture"]["path"] == activation_gate.PINNED_299_FIXTURE_PATH
    assert evidence["prior299Evidence"]["fixture"]["sha256"] == activation_gate.PINNED_299_FIXTURE_SHA256
    assert evidence["prior299Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior299Evidence"]["report"]["path"] == activation_gate.PINNED_299_REPORT_PATH
    assert evidence["prior299Evidence"]["report"]["sha256"] == activation_gate.PINNED_299_REPORT_SHA256
    assert evidence["prior299Evidence"]["prior297Fixture"]["sha256"] == activation_gate.operator_run.PINNED_297_FIXTURE_SHA256
    assert evidence["prior299Evidence"]["prior295Fixture"]["sha256"] == activation_gate.operator_run.PINNED_295_FIXTURE_SHA256
    assert evidence["prior299Evidence"]["prior293Fixture"]["sha256"] == activation_gate.operator_run.PINNED_293_FIXTURE_SHA256
    assert evidence["prior299Evidence"]["approvalPacketFixture"]["sha256"] == activation_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["activationScope"]["adlPath"] == "examples/simple-agent.yaml"
    assert evidence["activationScope"]["representedActivation"] == "local-temporary-json-gate"
    assert evidence["activationScope"]["liveMutation"] is False
    assert evidence["commandTranscript"]["mode"] == "bounded-external-service-activation-gate"
    assert evidence["traceEvalSummary"]["completionStatus"] == "pass"
    assert evidence["traceEvalSummary"]["toolExecution"] is None
    assert evidence["serviceWrapperState"]["before"]["enabled"] is False
    assert evidence["serviceWrapperState"]["afterRepresentedActivation"]["enabled"] is True
    assert evidence["serviceWrapperState"]["afterRepresentedActivation"]["externalProcessPid"] is None
    assert evidence["serviceWrapperState"]["afterHold"]["enabled"] is False
    assert evidence["serviceWrapperState"]["afterRollback"]["enabled"] is False
    assert evidence["activationDecision"]["decision"] == "hold"
    assert evidence["activationDecision"]["liveActionAuthorized"] is False
    assert evidence["rollbackDisableVerification"]["wrapperEnabledAfterRollback"] is False
    assert evidence["rollbackDisableVerification"]["externalProcessStarted"] is False
    assert evidence["rollbackDisableVerification"]["persistentMutation"] is False
    assert evidence["auditTrail"] == [
        "load-pinned-299-evidence",
        "record-before-disabled",
        "represent-local-temporary-activation",
        "hold-disable-local-state",
        "rollback-local-state",
    ]
    assert evidence["riskVerdict"] == "hold-fail-closed-before-real-external-service-activation"
    assert "separate Nissan-approved micro-gate" in evidence["nextStepCue"]
    assert results["bounded-external-activation-rollback-pass"]["verdict"] == "rollback"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior299Fixture.expectedSha256" in finding_paths["stale-prior-299-fixture-denied"]
    assert "prior299Report.expectedSha256" in finding_paths["stale-prior-299-report-denied"]
    assert "currentOperatorApprovalState.security_reviewer_approval" in finding_paths["missing-current-operator-approval-denied"]
    assert "activationScope" in finding_paths["wrong-activation-scope-denied"]
    assert "serviceWrapperState" in finding_paths["unsafe-service-state-denied"]
    assert "persistentMutation" in finding_paths["unsafe-service-state-denied"]
    assert "commandTranscript" in finding_paths["unsafe-transcript-denied"]
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
    assert_positive_mutation_fails(lambda scenario: scenario.update({"activationDecision": {"decision": "activate", "liveActionAuthorized": True}}), "activationDecision")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"commandTranscript": {"mode": "host-service", "command": "launchctl start reddiagent", "exitCode": 0}}), "commandTranscript")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"traceEvalSummary": {}}), "traceEvalSummary")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisableVerification": {}}), "rollbackDisableVerification.disableCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Activation completed."}), "nextStepCue")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["before"].update({"externalProcessPid": 12345}), "serviceWrapperState")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["afterRepresentedActivation"].update({"mutationScope": "host-process"}), "serviceWrapperState")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperState"]["afterRollback"].update({"externalProcessPid": 12345}), "serviceWrapperState")

    assert_prior_299_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior299Fixture.status")
    assert_prior_299_mutation_fails(lambda prior: prior.update({"follows": [297]}), "prior299Fixture.follows")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "activate"}), "prior299Fixture.results.verdict")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior297Evidence"]["fixture"].update({"sha256": "bad"}), "prior299Fixture.results.prior297Evidence.fixture")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior297Evidence"]["prior295Fixture"].update({"sha256": "bad"}), "prior299Fixture.results.prior297Evidence.prior295Fixture")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior297Evidence"]["prior293Fixture"].update({"sha256": "bad"}), "prior299Fixture.results.prior297Evidence.prior293Fixture")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior297Evidence"]["approvalPacketFixture"].update({"sha256": "bad"}), "prior299Fixture.results.prior297Evidence.approvalPacketFixture")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["activationScope"].update({"adlPath": "examples/tool-agent.yaml"}), "prior299Fixture.results.activationScope")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["currentOperatorApprovalState"].update({"runtime_owner_approval": False}), "prior299Fixture.results.currentOperatorApprovalState.runtime_owner_approval")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"traceEvalSummary": {}}), "prior299Fixture.results.traceEvalSummary")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["rollbackDisableVerification"].update({"wrapperEnabledAfterRollback": True}), "prior299Fixture.results.rollbackDisableVerification")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["operatorDecision"].update({"liveActionAuthorized": True}), "prior299Fixture.results.operatorDecision")
    assert_prior_299_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"riskVerdict": "activate"}), "prior299Fixture.results.riskVerdict")

    print("PASS beta bounded external-service activation gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
