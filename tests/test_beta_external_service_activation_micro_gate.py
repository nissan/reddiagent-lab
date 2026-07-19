#!/usr/bin/env python3
"""External-service activation approval micro-gate checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-service-activation-micro-gate.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-activation-micro-gate-scenarios.json"
PINNED_301_FIXTURE = ROOT / "tests" / "fixtures" / "beta-bounded-external-service-activation-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_service_activation_micro_gate as micro_gate  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_gate(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_external_service_activation_micro_gate.py", *extra_args],
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
    return micro_gate.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = micro_gate.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_301_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_301_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_301_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = micro_gate.build_result(scenario, gate.source_commit())
    finally:
        PINNED_301_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_gate()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-external-service-activation-micro-gate"
    assert doc["issue"] == 303
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [301, 299, 297, 295, 293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "askHoldVerdicts": 12,
        "failClosedScenarios": 11,
        "negativeScenarios": 11,
        "positiveScenarios": 1,
    }
    for boundary, expected in micro_gate.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    positive = results["external-service-activation-micro-gate-ask-hold-pass"]
    evidence = positive["runEvidence"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "ask-nissan-and-hold"
    assert evidence["sourceMergeCommit"] == micro_gate.PINNED_301_MERGE_COMMIT
    assert evidence["prior301Evidence"]["fixture"]["path"] == micro_gate.PINNED_301_FIXTURE_PATH
    assert evidence["prior301Evidence"]["fixture"]["sha256"] == micro_gate.PINNED_301_FIXTURE_SHA256
    assert evidence["prior301Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior301Evidence"]["prior299Fixture"]["sha256"] == micro_gate.bounded_gate.PINNED_299_FIXTURE_SHA256
    assert evidence["prior301Evidence"]["prior297Fixture"]["sha256"] == micro_gate.bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256
    assert evidence["prior301Evidence"]["prior295Fixture"]["sha256"] == micro_gate.bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256
    assert evidence["prior301Evidence"]["prior293Fixture"]["sha256"] == micro_gate.bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256
    assert evidence["prior301Evidence"]["approvalPacketFixture"]["sha256"] == micro_gate.bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["proposedRunScope"]["adlPath"] == "examples/simple-agent.yaml"
    assert evidence["proposedRunScope"]["estimatedCostUsd"] == "0.00"
    assert evidence["preconditions"]["mainnetBlocked"] is True
    assert evidence["nissanApproval"]["required"] is True
    assert evidence["nissanApproval"]["status"] == "pending"
    assert evidence["nissanApproval"]["approved"] is False
    assert evidence["commandTranscriptTemplate"]["mode"] == "external-service-activation-micro-gate"
    assert evidence["traceEvalRequirements"]["toolExecution"] is None
    assert evidence["traceEvalRequirements"]["mustRejectMainnet"] is True
    assert evidence["serviceWrapperExpectations"]["before"]["enabled"] is False
    assert evidence["serviceWrapperExpectations"]["after"]["enabled"] is False
    assert evidence["rollbackDisablePlan"]["verifiedNoPersistence"] is True
    assert evidence["askHoldDecision"]["decision"] == "ask-nissan-and-hold"
    assert evidence["askHoldDecision"]["liveActionAuthorized"] is False
    assert evidence["riskVerdict"] == "hold-fail-closed-until-nissan-approval"

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior301Fixture.expectedSha256" in finding_paths["stale-prior-301-fixture-denied"]
    assert "nissanApproval" in finding_paths["missing-nissan-approval-fields-denied"]
    assert "nissanApproval" in finding_paths["premature-nissan-approval-denied"]
    assert "proposedRunScope" in finding_paths["broad-scope-denied"]
    assert "commandTranscriptTemplate" in finding_paths["unsafe-transcript-denied"]
    assert "commandTranscriptTemplate.command[0]" in finding_paths["unsafe-transcript-denied"]
    assert "localCommands[0]" in finding_paths["unsafe-transcript-denied"]
    assert "traceEvalRequirements" in finding_paths["missing-trace-requirements-denied"]
    assert "serviceWrapperExpectations" in finding_paths["unsafe-wrapper-expectations-denied"]
    assert "rollbackDisablePlan" in finding_paths["missing-rollback-plan-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-payload-denied"]
    assert "hostMutationRequested" in finding_paths["live-rails-denied"]
    assert "dockerStartRequested" in finding_paths["live-rails-denied"]
    assert "providerApiAccessRequested" in finding_paths["live-rails-denied"]
    assert "liveMcpRequested" in finding_paths["live-rails-denied"]
    assert "paymentRequested" in finding_paths["live-rails-denied"]
    assert "devnetRequested" in finding_paths["live-rails-denied"]
    assert "mainnetRequested" in finding_paths["live-rails-denied"]
    assert "askHoldDecision" in finding_paths["unsafe-ask-hold-decision-denied"]
    assert "riskVerdict" in finding_paths["unsafe-ask-hold-decision-denied"]
    assert "nextStepCue" in finding_paths["unsafe-ask-hold-decision-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceMergeCommit": "bad"}), "sourceMergeCommit")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "private_key"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nissanApproval": {"approved": True}}), "nissanApproval")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"proposedRunScope": {"adlPath": "examples/tool-agent.yaml"}}), "proposedRunScope")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"commandTranscriptTemplate": {"mode": "host-service", "command": "launchctl start reddiagent", "expectedExitCode": 0}}), "commandTranscriptTemplate")
    assert_positive_mutation_fails(lambda scenario: scenario["commandTranscriptTemplate"].update({"command": "docker run reddiagent"}), "commandTranscriptTemplate")
    assert_positive_mutation_fails(lambda scenario: scenario["commandTranscriptTemplate"].update({"command": "docker run reddiagent"}), "commandTranscriptTemplate.command[0]")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"traceEvalRequirements": {}}), "traceEvalRequirements")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"rollbackDisablePlan": {}}), "rollbackDisablePlan")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Activation completed."}), "nextStepCue")
    assert_positive_mutation_fails(lambda scenario: scenario["serviceWrapperExpectations"]["after"].update({"externalProcessPid": 12345}), "serviceWrapperExpectations")
    assert_positive_mutation_fails(lambda scenario: scenario["askHoldDecision"].update({"liveActionAuthorized": True}), "askHoldDecision")

    assert_prior_301_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior301Fixture.status")
    assert_prior_301_mutation_fails(lambda prior: prior.update({"follows": [299]}), "prior301Fixture.follows")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "activate"}), "prior301Fixture.results.verdict")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior299Evidence"]["fixture"].update({"sha256": "bad"}), "prior301Fixture.results.prior299Evidence.fixture")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior299Evidence"]["prior297Fixture"].update({"sha256": "bad"}), "prior301Fixture.results.prior299Evidence.prior297Fixture")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior299Evidence"]["prior295Fixture"].update({"sha256": "bad"}), "prior301Fixture.results.prior299Evidence.prior295Fixture")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior299Evidence"]["prior293Fixture"].update({"sha256": "bad"}), "prior301Fixture.results.prior299Evidence.prior293Fixture")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior299Evidence"]["approvalPacketFixture"].update({"sha256": "bad"}), "prior301Fixture.results.prior299Evidence.approvalPacketFixture")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"riskVerdict": "activate"}), "prior301Fixture.results.riskVerdict")
    assert_prior_301_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["activationDecision"].update({"liveActionAuthorized": True}), "prior301Fixture.results.activationDecision")

    print("PASS beta external-service activation micro-gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
