#!/usr/bin/env python3
"""Coolify public devnet demo readiness checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "coolify-devnet-public-demo.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "coolify-devnet-public-demo-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import coolify_devnet_public_demo  # noqa: E402


def normalize_commit(value):
    if isinstance(value, dict):
        return {key: ("<current-git-head>" if key == "sourceCommit" else normalize_commit(child)) for key, child in value.items()}
    if isinstance(value, list):
        return [normalize_commit(child) for child in value]
    return value


def run_demo() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/coolify_devnet_public_demo.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return coolify_devnet_public_demo.merge_scenario(scenarios["defaults"], {"id": "mutation", "kind": "positive"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = coolify_devnet_public_demo.build_result(scenario, "a" * 40)
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_demo()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_commit(doc) == normalize_commit(fixture)
    assert doc["mode"] == "coolify-devnet-public-demo-readiness"
    assert doc["issue"] == 280
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert "Mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["summary"] == {
        "positiveScenarios": 1,
        "negativeScenarios": 6,
        "failClosedScenarios": 6,
    }

    results = {result["id"]: result for result in doc["results"]}
    positive = results["coolify-devnet-public-demo-pass"]
    assert positive["status"] == "pass"
    assert positive["deployment"]["publicUrl"] == "https://reddiagent-devnet.preview.reddi.tech/"
    assert positive["deployment"]["coolifyResourceType"] == "dockerimage"
    assert positive["deployment"]["buildPack"] == "dockerimage"
    assert positive["deployment"]["dockerfilePath"] == "/Dockerfile"
    assert positive["deployment"]["imageName"] == "localhost:5000/reddiagent-devnet-demo"
    assert positive["deployment"]["imageTagPolicy"] == "source-commit-short"
    assert positive["deployment"]["healthPath"] == "/"
    assert positive["deployment"]["devnetCluster"] == "solana-devnet"
    assert "/" in positive["deployment"]["verifiedRoutes"]
    assert "/prosumer-builder-static-export.html" in positive["deployment"]["verifiedRoutes"]
    assert positive["claims"]["devnetDemo"] is True
    assert positive["claims"]["mainnetReady"] is False
    assert positive["boundaries"]["devnetAllowed"] is True
    assert positive["boundaries"]["mainnetAccess"] is False
    assert positive["boundaries"]["paymentRailAccess"] is False
    assert all(item["exists"] and item["sha256"] for item in positive["requiredLocalFileInventory"])
    assert all("value" not in item for item in positive["environmentContract"])

    finding_paths = {result_id: {finding["path"] for finding in result["findings"]} for result_id, result in results.items()}
    assert "claims.mainnetReady" in finding_paths["mainnet-claim-denied"]
    assert "boundaries.mainnetAccess" in finding_paths["mainnet-claim-denied"]
    assert "claims.paymentEnabled" in finding_paths["payment-settlement-denied"]
    assert "claims.settlementEnabled" in finding_paths["payment-settlement-denied"]
    assert "healthPath" in finding_paths["missing-health-route-denied"]
    assert "verifiedRoutes" in finding_paths["missing-health-route-denied"]
    assert "environmentContract[0].value" in finding_paths["credential-value-denied"]
    assert "environmentContract[0].name" in finding_paths["credential-value-denied"]
    assert "boundaries.credentialValuesEmbedded" in finding_paths["credential-value-denied"]
    assert "claims.liveMcpEnabled" in finding_paths["provider-mcp-denied"]
    assert "claims.providerProductCallsEnabled" in finding_paths["provider-mcp-denied"]
    assert "claims.productionReady" in finding_paths["unsafe-production-gateway-denied"]
    assert "boundaries.productionGatewayMutation" in finding_paths["unsafe-production-gateway-denied"]

    assert_positive_mutation_fails(lambda scenario: scenario.update({"publicUrl": "http://example.invalid"}), "publicUrl")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"repo": "https://github.com/reddinft/reddiagent-lab"}), "repo")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"branch": "main"}), "branch")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"publishDirectory": "/"}), "publishDirectory")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"coolifyResourceType": "private-deploy-key"}), "coolifyResourceType")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"buildPack": "static"}), "buildPack")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"imageName": "ghcr.io/reddinft/reddiagent-devnet-demo"}), "imageName")
    assert_positive_mutation_fails(lambda scenario: scenario["claims"].update({"mainnetReady": True}), "claims.mainnetReady")
    assert_positive_mutation_fails(lambda scenario: scenario["boundaries"].update({"mainnetAccess": True}), "boundaries.mainnetAccess")
    assert_positive_mutation_fails(lambda scenario: scenario["environmentContract"][0].update({"value": "devnet"}), "environmentContract[0].value")
    print("PASS Coolify devnet public demo readiness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
