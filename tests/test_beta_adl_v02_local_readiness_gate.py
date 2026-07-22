#!/usr/bin/env python3
"""Check ADL v0.2 local beta readiness gate evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-adl-v02-local-readiness-gate.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_adl_v02_local_readiness_gate  # noqa: E402


def run_gate() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_adl_v02_local_readiness_gate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def runtime_scenario(docs: dict, scenario_id: str) -> dict:
    for scenario in docs["runtimePrototype"]["scenarios"]:
        if scenario.get("id") == scenario_id:
            return scenario
    raise AssertionError(f"missing runtime scenario {scenario_id}")


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    docs = {
        key: beta_adl_v02_local_readiness_gate.load_json(ROOT / path)
        for key, path in beta_adl_v02_local_readiness_gate.REQUIRED_ARTIFACTS.items()
        if path.endswith(".json")
    }
    inventory = beta_adl_v02_local_readiness_gate.artifact_inventory()
    boundaries = dict(beta_adl_v02_local_readiness_gate.build_report(commit="fixture://test")["boundaries"])
    mutator(docs, inventory, boundaries)
    findings = beta_adl_v02_local_readiness_gate.collect_findings(
        docs["releaseHandoff"],
        docs["reviewerWalkthroughSmoke"],
        docs["runtimePrototype"],
        inventory,
        boundaries,
    )
    assert expected_path in {finding["path"] for finding in findings}


def inventory_key_for_index_zero() -> str:
    return sorted(beta_adl_v02_local_readiness_gate.REQUIRED_ARTIFACTS)[0]


def main() -> int:
    doc = run_gate()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "adl-v02-local-beta-readiness-gate"
    assert doc["issue"] == 341
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337, 339]
    assert doc["status"] == "pass"
    assert doc["baselineDecision"] == "ready"
    assert doc["readinessId"] == "reddiagent-beta-0-adl-v02-local-readiness-gate"
    assert "mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["boundaries"]["offlinePassFailGate"] is True
    assert doc["boundaries"]["consumesHandoffAndWalkthroughOnly"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    for field in beta_adl_v02_local_readiness_gate.REQUIRED_BOUNDARY_FALSE:
        assert doc["boundaries"][field] is False

    inventory = {item["key"]: item for item in doc["artifactInventory"]}
    assert set(inventory) == set(beta_adl_v02_local_readiness_gate.REQUIRED_ARTIFACTS)
    assert all(item["exists"] and item["sha256"] and item["sizeBytes"] for item in inventory.values())
    assert inventory["releaseHandoff"]["path"] == "tests/fixtures/beta-release-handoff.json"
    assert inventory["reviewerWalkthroughSmoke"]["path"] == "tests/fixtures/beta-reviewer-walkthrough-smoke.json"
    assert inventory["validRuntimeAdl"]["path"] == "examples/v0.2/memory-observability-agent.yaml"
    assert inventory["invalidDiagnosticAdl"]["path"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"

    baseline = doc["adlV02RuntimeBaseline"]
    assert baseline["validRuntimeExample"] == {
        "id": "adl-v02-memory-observability-dry-run",
        "adl": "examples/v0.2/memory-observability-agent.yaml",
        "command": "python scripts/run_local_agent.py examples/v0.2/memory-observability-agent.yaml",
        "status": "pass",
        "exitCode": 0,
        "completionStatus": "pass",
        "safetyGate": "supported-adl-v02-local-runtime",
    }
    assert baseline["invalidDiagnosticSample"]["adl"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"
    assert baseline["invalidDiagnosticSample"]["exitCode"] == 1
    assert baseline["invalidDiagnosticSample"]["stableFields"] == ["code", "severity", "category", "path", "line", "column"]
    assert baseline["invalidDiagnosticSample"]["diagnostics"] == [
        {
            "code": "adl_v0_2_schema.required.extensions_x402_intents_0_authority",
            "severity": "error",
            "category": "payment",
            "path": "extensions.x402.intents.0.authority",
            "line": 22,
            "column": 9,
        }
    ]

    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: docs["releaseHandoff"].update({"refreshIssue": 0}),
        "releaseHandoff.refreshIssue",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: docs["reviewerWalkthroughSmoke"].update({"status": "fail"}),
        "reviewerWalkthroughSmoke.status",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: runtime_scenario(docs, "adl-v02-memory-observability-dry-run").update({"exitCode": 1}),
        "runtimePrototype.validRuntimeExample.exitCode",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: runtime_scenario(docs, "invalid-adl-v02-payment-diagnostics")["validationDiagnostics"][0].pop("line"),
        "runtimePrototype.invalidDiagnosticSample.diagnostics[0].line",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: boundaries.update({"fullHistoricalBetaChainReplay": True}),
        "boundaries.fullHistoricalBetaChainReplay",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, boundaries: inventory[0].update({"sha256": ""}),
        f"artifactInventory.{inventory_key_for_index_zero()}.sha256",
    )

    print("PASS ADL v0.2 local beta readiness gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
