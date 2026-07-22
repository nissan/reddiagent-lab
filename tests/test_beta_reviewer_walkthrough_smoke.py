#!/usr/bin/env python3
"""Check ADL v0.2 beta reviewer walkthrough smoke evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-reviewer-walkthrough-smoke.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_reviewer_walkthrough_smoke  # noqa: E402


def run_walkthrough() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_reviewer_walkthrough_smoke.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_finding_after_mutation(mutator, expected_path: str) -> None:
    report = beta_reviewer_walkthrough_smoke.build_report(commit="fixture://test")
    docs = {
        key: beta_reviewer_walkthrough_smoke.load_json(ROOT / path)
        for key, path in beta_reviewer_walkthrough_smoke.REQUIRED_ARTIFACTS.items()
        if path.endswith(".json")
    }
    inventory = beta_reviewer_walkthrough_smoke.artifact_inventory()
    commands = list(report["reviewerCommands"])
    boundaries = dict(report["boundaries"])
    mutator(docs, inventory, commands, boundaries)
    findings = beta_reviewer_walkthrough_smoke.collect_findings(
        docs["releaseHandoff"],
        docs["onboardingQuickstart"],
        docs["reviewerChecklist"],
        docs["releaseVerification"],
        docs["reviewUi"],
        docs["runtimePrototype"],
        inventory,
        commands,
        boundaries,
    )
    assert expected_path in {finding["path"] for finding in findings}


def runtime_scenario(docs: dict, scenario_id: str) -> dict:
    for scenario in docs["runtimePrototype"]["scenarios"]:
        if scenario.get("id") == scenario_id:
            return scenario
    raise AssertionError(f"missing runtime scenario {scenario_id}")


def main() -> int:
    doc = run_walkthrough()
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-local-reviewer-walkthrough-smoke"
    assert doc["issue"] == 339
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [337]
    assert doc["status"] == "pass"
    assert doc["walkthroughId"] == "reddiagent-beta-0-adl-v02-local-reviewer-walkthrough-smoke"
    assert doc["boundaries"]["reviewerWalkthroughSmoke"] is True
    assert doc["boundaries"]["deterministicLocalFixturesOnly"] is True
    for field in beta_reviewer_walkthrough_smoke.REQUIRED_BOUNDARY_FALSE:
        assert doc["boundaries"][field] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]

    inventory = {item["key"]: item for item in doc["artifactInventory"]}
    assert set(inventory) == set(beta_reviewer_walkthrough_smoke.REQUIRED_ARTIFACTS)
    assert all(item["exists"] and item["sha256"] for item in inventory.values())
    assert inventory["releaseHandoff"]["path"] == "tests/fixtures/beta-release-handoff.json"
    assert inventory["validRuntimeAdl"]["path"] == "examples/v0.2/memory-observability-agent.yaml"
    assert inventory["invalidDiagnosticAdl"]["path"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"

    commands = doc["reviewerCommands"]
    assert "python scripts/beta_release_handoff_archive.py" in commands
    assert "python scripts/beta_release_verification_cli.py" in commands
    assert "python scripts/run_local_agent.py examples/v0.2/memory-observability-agent.yaml" in commands
    assert "python scripts/run_local_agent.py examples/invalid/adl-v0.2-x402-missing-authority.yaml --json-validation-errors" in commands
    assert all("docker" not in command.lower() for command in commands)
    assert all("devnet" not in command.lower() for command in commands)
    assert all("mainnet" not in command.lower() for command in commands)

    review = doc["adlV02RuntimeReview"]
    assert review["validRuntimeExample"] == {
        "id": "adl-v02-memory-observability-dry-run",
        "adl": "examples/v0.2/memory-observability-agent.yaml",
        "command": "python scripts/run_local_agent.py examples/v0.2/memory-observability-agent.yaml",
        "status": "pass",
        "exitCode": 0,
        "completionStatus": "pass",
        "safetyGate": "supported-adl-v02-local-runtime",
    }
    diagnostic_sample = review["invalidDiagnosticSample"]
    assert diagnostic_sample["id"] == "invalid-adl-v02-payment-diagnostics"
    assert diagnostic_sample["adl"] == "examples/invalid/adl-v0.2-x402-missing-authority.yaml"
    assert diagnostic_sample["exitCode"] == 1
    assert diagnostic_sample["stableFields"] == ["code", "severity", "category", "path", "line", "column"]
    assert diagnostic_sample["diagnostics"] == [
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
        lambda docs, inventory, commands, boundaries: docs["releaseHandoff"].update({"refreshIssue": 0}),
        "releaseHandoff.refreshIssue",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, commands, boundaries: runtime_scenario(docs, "invalid-adl-v02-payment-diagnostics").update({"exitCode": 0}),
        "runtimePrototype.invalidDiagnosticSample.exitCode",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, commands, boundaries: runtime_scenario(docs, "invalid-adl-v02-payment-diagnostics")["validationDiagnostics"][0].pop("column"),
        "runtimePrototype.invalidDiagnosticSample.diagnostics[0].column",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, commands, boundaries: commands.append("curl https://example.invalid/review"),
        "reviewerCommands[7]",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, commands, boundaries: boundaries.update({"providerApiAccess": True}),
        "boundaries.providerApiAccess",
    )
    assert_finding_after_mutation(
        lambda docs, inventory, commands, boundaries: inventory[0].update({"sha256": ""}),
        f"artifactInventory.{inventory_key_for_index_zero()}.sha256",
    )

    print("PASS beta reviewer walkthrough smoke")
    return 0


def inventory_key_for_index_zero() -> str:
    return sorted(beta_reviewer_walkthrough_smoke.REQUIRED_ARTIFACTS)[0]


if __name__ == "__main__":
    sys.exit(main())
