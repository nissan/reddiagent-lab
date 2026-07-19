#!/usr/bin/env python3
"""External-service approval-intake checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-service-approval-intake.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-approval-intake-scenarios.json"
PINNED_303_FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-service-activation-micro-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_service_approval_intake as intake  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_intake(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_external_service_approval_intake.py", *extra_args],
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
    return intake.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = intake.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_approved_response_fails(response_text: str, expected_path: str, **updates) -> None:
    scenario = positive_scenario()
    scenario["nissanResponse"].update(
        {
            "status": "approved",
            "approver": "Nissan",
            "responseText": response_text,
            "timestamp": "2026-07-20T02:36:00+10:00",
            "source": "telegram:-5218935737:constructed-test",
            "fresh": True,
            "scope": "exact-303-local-free-bounded-scope",
        }
    )
    scenario["nissanResponse"].update(updates)
    result = intake.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert result["verdict"] == "hold-fail-closed"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_303_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_303_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_303_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = intake.build_result(scenario, gate.source_commit())
    finally:
        PINNED_303_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_intake()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-external-service-approval-intake"
    assert doc["issue"] == 305
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [303, 301, 299, 297, 295, 293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "approveDecisions": 0,
        "failClosedScenarios": 9,
        "holdDecisions": 10,
        "negativeScenarios": 9,
        "positiveScenarios": 1,
    }
    for boundary, expected in intake.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    hold = results["approval-intake-absent-response-hold-pass"]
    evidence = hold["runEvidence"]
    assert hold["status"] == "pass"
    assert hold["verdict"] == "hold-fail-closed"
    assert hold["runEvidence"]["riskVerdict"] == "hold-fail-closed-without-fresh-nissan-approval"
    assert evidence["sourceMergeCommit"] == intake.PINNED_303_MERGE_COMMIT
    assert evidence["prior303Evidence"]["fixture"]["path"] == intake.PINNED_303_FIXTURE_PATH
    assert evidence["prior303Evidence"]["fixture"]["sha256"] == intake.PINNED_303_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior303Evidence"]["prior301Fixture"]["sha256"] == intake.micro_gate.PINNED_301_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["prior299Fixture"]["sha256"] == intake.micro_gate.bounded_gate.PINNED_299_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["prior297Fixture"]["sha256"] == intake.micro_gate.bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["prior295Fixture"]["sha256"] == intake.micro_gate.bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["prior293Fixture"]["sha256"] == intake.micro_gate.bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256
    assert evidence["prior303Evidence"]["approvalPacketFixture"]["sha256"] == intake.micro_gate.bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["approvalPrompt"] == intake.REQUIRED_APPROVAL_PROMPT
    assert evidence["nissanResponse"]["status"] == "absent"
    assert evidence["timestampSourceFields"]["responseTimestamp"] is None
    assert evidence["timestampSourceFields"]["responseSource"] is None
    assert evidence["boundedScopeEcho"]["adlPath"] == "examples/simple-agent.yaml"
    assert evidence["boundedScopeEcho"]["estimatedCostUsd"] == "0.00"
    assert evidence["preconditionEcho"]["pinned303HashMatches"] is True
    assert evidence["preconditionEcho"]["pinned301Consumed"] is True
    assert evidence["approveOrHoldDecision"]["decision"] == "hold-fail-closed"
    assert evidence["approveOrHoldDecision"]["liveActionAuthorized"] is False
    assert evidence["approveOrHoldDecision"]["stopBeforeMutation"] is True

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior303Fixture.expectedSha256" in finding_paths["stale-prior-303-fixture-denied"]
    assert "nissanResponse.status" in finding_paths["ambiguous-response-denied"]
    assert "nissanResponse.fresh" in finding_paths["stale-approval-denied"]
    assert "nissanResponse.scope" in finding_paths["broader-scope-denied"]
    assert "nissanResponse.providerEscalation" in finding_paths["provider-escalation-denied"]
    assert "nissanResponse.productionEscalation" in finding_paths["provider-escalation-denied"]
    assert "nissanResponse.devnetEscalation" in finding_paths["devnet-mainnet-escalation-denied"]
    assert "nissanResponse.mainnetEscalation" in finding_paths["devnet-mainnet-escalation-denied"]
    assert "nissanResponse.costEscalation" in finding_paths["cost-privacy-legal-escalation-denied"]
    assert "nissanResponse.privacyEscalation" in finding_paths["cost-privacy-legal-escalation-denied"]
    assert "nissanResponse.legalEscalation" in finding_paths["cost-privacy-legal-escalation-denied"]
    assert "approvalPrompt" in finding_paths["wrong-prompt-denied"]
    assert "actualServiceMutation" in finding_paths["unsafe-boundary-denied"]
    assert "providerApiAccess" in finding_paths["unsafe-boundary-denied"]
    assert "devnetAccess" in finding_paths["unsafe-boundary-denied"]
    assert "mainnetAccess" in finding_paths["unsafe-boundary-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceMergeCommit": "bad"}), "sourceMergeCommit")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"approvalPrompt": "Approve mainnet?"}), "approvalPrompt")
    assert_positive_mutation_fails(lambda scenario: scenario["nissanResponse"].update({"status": "maybe"}), "nissanResponse.status")
    assert_positive_mutation_fails(lambda scenario: scenario["nissanResponse"].update({"status": "approved", "fresh": False}), "nissanResponse.fresh")
    assert_positive_mutation_fails(lambda scenario: scenario["nissanResponse"].update({"status": "approved", "scope": "broader"}), "nissanResponse.scope")
    assert_positive_mutation_fails(lambda scenario: scenario["nissanResponse"].update({"status": "approved", "providerEscalation": True}), "nissanResponse.providerEscalation")
    assert_positive_mutation_fails(lambda scenario: scenario["boundedScopeEcho"].update({"mainnetEscalation": True}), "boundedScopeEcho")
    assert_positive_mutation_fails(lambda scenario: scenario["preconditionEcho"].update({"lineagePreserved": False}), "preconditionEcho.lineagePreserved")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"intakeCommand": "docker run reddiagent"}), "intakeCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "api_key=secret"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"stopBeforeMutation": False}), "stopBeforeMutation")
    assert_approved_response_fails("I approve exactly this local free bounded scope only.", "nissanResponse.status")
    assert_approved_response_fails("I approve mainnet too.", "nissanResponse.escalation")
    assert_approved_response_fails("I approve provider API product call.", "nissanResponse.escalation")
    assert_approved_response_fails("I approve devnet run too.", "nissanResponse.escalation")
    assert_approved_response_fails(
        "I approve exactly this local free bounded scope only.",
        "nissanResponse.status",
        timestamp="2026-07-17T16:07:00+10:00",
    )

    assert_prior_303_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior303Fixture.status")
    assert_prior_303_mutation_fails(lambda prior: prior.update({"follows": [301]}), "prior303Fixture.follows")
    assert_prior_303_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "activate"}), "prior303Fixture.results.verdict")
    assert_prior_303_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["nissanApproval"].update({"approvalPrompt": "Approve mainnet?"}), "prior303Fixture.results.nissanApproval.approvalPrompt")
    assert_prior_303_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior301Evidence"]["fixture"].update({"sha256": "bad"}), "prior303Fixture.results.prior301Evidence.fixture")
    assert_prior_303_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior301Evidence"]["prior299Fixture"].update({"sha256": "bad"}), "prior303Fixture.results.prior301Evidence.prior299Fixture")
    assert_prior_303_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["askHoldDecision"].update({"liveActionAuthorized": True}), "prior303Fixture.results.askHoldDecision")

    print("PASS beta external-service approval intake")
    return 0


if __name__ == "__main__":
    sys.exit(main())
