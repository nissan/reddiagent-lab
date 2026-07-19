#!/usr/bin/env python3
"""External-service approval authorization checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-service-approval-authorization.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-external-service-approval-authorization-scenarios.json"
PINNED_305_FIXTURE = ROOT / "tests" / "fixtures" / "beta-external-service-approval-intake.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_external_service_approval_authorization as authz  # noqa: E402
import beta_runtime_activation_evidence_gate as gate  # noqa: E402


def run_authz(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_external_service_approval_authorization.py", *extra_args],
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
    return authz.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = authz.build_result(scenario, gate.source_commit())
    assert result["status"] == "fail"
    assert result["verdict"] == "hold-fail-closed"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_prior_305_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    original = PINNED_305_FIXTURE.read_text()
    source = json.loads(original)
    mutator(source)
    try:
        PINNED_305_FIXTURE.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        result = authz.build_result(scenario, gate.source_commit())
    finally:
        PINNED_305_FIXTURE.write_text(original)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_authz()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_dynamic(doc) == normalize_dynamic(fixture)
    assert doc["mode"] == "beta-external-service-approval-authorization"
    assert doc["issue"] == 307
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [305, 303, 301, 299, 297, 295, 293, 291, 289, 287, 285]
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["summary"] == {
        "approveDecisions": 1,
        "positiveScenarios": 1,
        "negativeScenarios": 9,
        "failClosedScenarios": 9,
    }
    for boundary, expected in authz.boundary_values().items():
        assert doc["boundaries"][boundary] is expected
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    results = {result["id"]: result for result in doc["results"]}
    approved = results["approval-authorization-telegram-16856-pass"]
    evidence = approved["runEvidence"]
    assert approved["status"] == "pass"
    assert approved["verdict"] == "approve-exact-bounded-scope"
    assert evidence["sourceMergeCommit"] == authz.PINNED_305_MERGE_COMMIT
    assert evidence["prior305Evidence"]["fixture"]["path"] == authz.PINNED_305_FIXTURE_PATH
    assert evidence["prior305Evidence"]["fixture"]["sha256"] == authz.PINNED_305_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["fixture"]["hashMatches"] is True
    assert evidence["prior305Evidence"]["prior303Fixture"]["sha256"] == authz.intake.PINNED_303_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["prior301Fixture"]["sha256"] == authz.intake.micro_gate.PINNED_301_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["prior299Fixture"]["sha256"] == authz.intake.micro_gate.bounded_gate.PINNED_299_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["prior297Fixture"]["sha256"] == authz.intake.micro_gate.bounded_gate.operator_run.PINNED_297_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["prior295Fixture"]["sha256"] == authz.intake.micro_gate.bounded_gate.operator_run.PINNED_295_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["prior293Fixture"]["sha256"] == authz.intake.micro_gate.bounded_gate.operator_run.PINNED_293_FIXTURE_SHA256
    assert evidence["prior305Evidence"]["approvalPacketFixture"]["sha256"] == authz.intake.micro_gate.bounded_gate.operator_run.PINNED_291_APPROVAL_PACKET_SHA256
    assert evidence["approvalPrompt"] == authz.intake.REQUIRED_APPROVAL_PROMPT
    assert evidence["telegramApproval"]["source"] == authz.REQUIRED_APPROVAL_SOURCE
    assert evidence["telegramApproval"]["timestamp"] == authz.REQUIRED_APPROVAL_TIMESTAMP
    assert evidence["telegramApproval"]["responseText"] == authz.REQUIRED_APPROVAL_TEXT
    assert evidence["telegramApproval"]["scope"] == authz.REQUIRED_APPROVAL_SCOPE
    assert evidence["authorizationDecision"]["nextBoundedLaneAuthorized"] is True
    assert evidence["authorizationDecision"]["realMutationAuthorizedByThisArtifact"] is False
    assert evidence["authorizationDecision"]["mainnetAuthorized"] is False
    assert evidence["riskVerdict"] == authz.REQUIRED_RISK_VERDICT

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "prior305Fixture.expectedSha256" in finding_paths["stale-prior-305-fixture-denied"]
    assert "telegramApproval.source" in finding_paths["wrong-telegram-source-denied"]
    assert "telegramApproval.timestamp" in finding_paths["stale-timestamp-denied"]
    assert "telegramApproval.fresh" in finding_paths["stale-timestamp-denied"]
    assert "approvalPrompt" in finding_paths["wrong-prompt-denied"]
    assert "telegramApproval.prompt" in finding_paths["wrong-prompt-denied"]
    assert "telegramApproval.scope" in finding_paths["broader-scope-denied"]
    assert "telegramApproval.providerEscalation" in finding_paths["provider-devnet-mainnet-escalation-denied"]
    assert "telegramApproval.devnetEscalation" in finding_paths["provider-devnet-mainnet-escalation-denied"]
    assert "telegramApproval.mainnetEscalation" in finding_paths["provider-devnet-mainnet-escalation-denied"]
    assert "actualServiceMutation" in finding_paths["unsafe-boundary-denied"]
    assert "providerApiAccess" in finding_paths["unsafe-boundary-denied"]
    assert "devnetAccess" in finding_paths["unsafe-boundary-denied"]
    assert "mainnetAccess" in finding_paths["unsafe-boundary-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-payload-denied"]
    assert "authorizationCommand" in finding_paths["unsafe-command-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"sourceMergeCommit": "bad"}), "sourceMergeCommit")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"approvalPrompt": "Approve mainnet?"}), "approvalPrompt")
    assert_positive_mutation_fails(lambda scenario: scenario["telegramApproval"].update({"source": "telegram:-5218935737:16855"}), "telegramApproval.source")
    assert_positive_mutation_fails(lambda scenario: scenario["telegramApproval"].update({"timestamp": "2026-07-17T16:07:00+10:00"}), "telegramApproval.timestamp")
    assert_positive_mutation_fails(lambda scenario: scenario["telegramApproval"].update({"fresh": False}), "telegramApproval.fresh")
    assert_positive_mutation_fails(lambda scenario: scenario["telegramApproval"].update({"scope": "broader"}), "telegramApproval.scope")
    assert_positive_mutation_fails(lambda scenario: scenario["telegramApproval"].update({"mainnetEscalation": True}), "telegramApproval.mainnetEscalation")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"actualServiceMutation": True}), "actualServiceMutation")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"authorizationCommand": "docker run reddiagent"}), "authorizationCommand")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "api_key=secret"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"nextStepCue": "Mainnet activation completed."}), "nextStepCue")

    assert_prior_305_mutation_fails(lambda prior: prior.update({"status": "fail"}), "prior305Fixture.status")
    assert_prior_305_mutation_fails(lambda prior: prior.update({"follows": [303]}), "prior305Fixture.follows")
    assert_prior_305_mutation_fails(lambda prior: prior["results"][0].update({"verdict": "approve"}), "prior305Fixture.results.verdict")
    assert_prior_305_mutation_fails(lambda prior: prior["results"][0]["runEvidence"].update({"approvalPrompt": "Approve mainnet?"}), "prior305Fixture.results.approvalPrompt")
    assert_prior_305_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior303Evidence"]["fixture"].update({"sha256": "bad"}), "prior305Fixture.results.prior303Evidence.fixture")
    assert_prior_305_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["prior303Evidence"]["prior299Fixture"].update({"sha256": "bad"}), "prior305Fixture.results.prior303Evidence.prior299Fixture")
    assert_prior_305_mutation_fails(lambda prior: prior["results"][0]["runEvidence"]["approveOrHoldDecision"].update({"liveActionAuthorized": True}), "prior305Fixture.results.approveOrHoldDecision")

    print("PASS beta external-service approval authorization")
    return 0


if __name__ == "__main__":
    sys.exit(main())
