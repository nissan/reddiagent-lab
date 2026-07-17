#!/usr/bin/env python3
"""Build a deterministic local beta release-candidate evidence bundle."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-local-runtime-rc-gate-scenarios.json"
READINESS_EVIDENCE = ROOT / "tests" / "fixtures" / "beta-release-readiness.json"
OPERATOR_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-control-scenarios.json"
REQUIRED_OPERATOR_CONTROLS = {
    "enable-runtime-path",
    "disable-runtime-path",
    "pause-provider-calls",
    "pause-mcp-invocation",
    "pause-payment-handoff",
    "force-local-only-mode",
}


sys.path.insert(0, str(ROOT / "scripts"))
import beta_operator_control_harness  # noqa: E402
import beta_release_readiness  # noqa: E402
import local_runtime_prototype  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def first_operator_pass(operator_report: dict[str, Any]) -> dict[str, Any] | None:
    for result in operator_report.get("results", []):
        if result.get("kind") == "positive" and result.get("completionStatus") == "pass":
            return result
    return None


def runtime_scenario(runtime_report: dict[str, Any], scenario_id: str) -> dict[str, Any] | None:
    for scenario in runtime_report.get("scenarios", []):
        if scenario.get("id") == scenario_id:
            return scenario
    return None


def readiness_doc_for_scenario(base: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    doc = copy.deepcopy(base)
    if scenario.get("staleReadinessReleaseId"):
        doc["releaseId"] = scenario["staleReadinessReleaseId"]
    if scenario.get("missingRollbackStopEvidence"):
        doc.setdefault("rollback", {})["stopFirst"] = False
    if scenario.get("mainnetRequested"):
        doc.setdefault("approvals", {})["mainnetApproved"] = True
    return doc


def collect_scenario_findings(
    scenario: dict[str, Any],
    readiness_doc: dict[str, Any],
    readiness_report: dict[str, Any],
    operator_report: dict[str, Any],
    runtime_report: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append({"path": path, "reason": reason})

    release_id = scenario.get("releaseId")
    require(readiness_report.get("status") == "pass", "readiness.status", "Readiness evidence must pass.")
    require(
        readiness_doc.get("releaseId") == release_id,
        "readiness.releaseId",
        "Readiness evidence must match the selected release.",
    )
    require(operator_report.get("status") == "pass", "operator.status", "Operator-control harness must pass.")
    require(runtime_report.get("status") == "pass", "runtime.status", "Local runtime prototype evidence must pass.")

    controls = set(scenario.get("operatorControls", []))
    missing_controls = sorted(REQUIRED_OPERATOR_CONTROLS - controls)
    require(not missing_controls, "operatorControls", f"Missing operator controls: {', '.join(missing_controls)}")
    require(scenario.get("runtimeMode") == "local-only", "runtimeMode", "Runtime mode must be local-only.")
    require(scenario.get("environment") == "local", "environment", "Environment must be local.")
    require(scenario.get("mainnetRequested") is not True, "mainnetRequested", "Mainnet request is not approved.")
    require(
        readiness_doc.get("approvals", {}).get("mainnetApproved") is False,
        "readiness.approvals.mainnetApproved",
        "Mainnet must remain explicitly not approved.",
    )
    require(
        "separate signoff" in str(readiness_doc.get("approvals", {}).get("mainnetStatement", "")).lower(),
        "readiness.approvals.mainnetStatement",
        "Mainnet statement must require separate signoff.",
    )
    require(readiness_doc.get("rollback", {}).get("stopFirst") is True, "rollback.stopFirst", "Rollback must stop runtime paths first.")

    selected_runtime = runtime_scenario(runtime_report, scenario.get("runtimeScenarioId", ""))
    require(selected_runtime is not None, "runtimeScenarioId", "Selected local runtime scenario must exist.")
    if selected_runtime:
        require(selected_runtime.get("status") == "pass", "runtimeScenario.status", "Selected local runtime scenario must pass.")
        require(
            selected_runtime.get("completion", {}).get("status") == "pass",
            "runtimeScenario.completion.status",
            "Selected local runtime completion must pass.",
        )

    return findings


def build_evidence_for_scenario(
    scenario: dict[str, Any],
    readiness_base: dict[str, Any],
    operator_base: dict[str, Any],
    runtime_report: dict[str, Any],
) -> dict[str, Any]:
    readiness_doc = readiness_doc_for_scenario(readiness_base, scenario)
    readiness_report = beta_release_readiness.build_report(readiness_doc)
    operator_report = beta_operator_control_harness.build_report(operator_base)
    findings = collect_scenario_findings(scenario, readiness_doc, readiness_report, operator_report, runtime_report)
    operator_pass = first_operator_pass(operator_report)
    selected_runtime = runtime_scenario(runtime_report, scenario.get("runtimeScenarioId", ""))
    positive_trace = operator_pass.get("traceEvents", []) if operator_pass else []
    cost_event = next((event for event in positive_trace if event.get("event") == "cost.estimated"), {})
    privacy = positive_trace[0].get("privacyRedactions", {}) if positive_trace else {}

    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": "pass" if not findings else "fail",
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "selectedRuntime": {
            "scenarioId": scenario.get("runtimeScenarioId"),
            "adl": selected_runtime.get("adl") if selected_runtime else None,
            "command": selected_runtime.get("command") if selected_runtime else None,
            "completionStatus": selected_runtime.get("completion", {}).get("status") if selected_runtime else None,
            "traceEvents": selected_runtime.get("traceEvents") if selected_runtime else None,
        },
        "operatorControlEvidence": {
            "source": "tests/fixtures/beta-operator-control-harness.json",
            "resultId": operator_pass.get("id") if operator_pass else None,
            "requiredControls": sorted(REQUIRED_OPERATOR_CONTROLS),
            "traceEvents": positive_trace,
        },
        "readinessEvidence": {
            "source": "tests/fixtures/beta-release-readiness.json",
            "releaseId": readiness_doc.get("releaseId"),
            "status": readiness_report.get("status"),
            "entryCriteria": readiness_report.get("summary", {}).get("entryCriteria"),
            "exitCriteria": readiness_report.get("summary", {}).get("exitCriteria"),
        },
        "costEstimate": {
            "amountUsd": cost_event.get("amountUsd"),
            "ceilingUsd": cost_event.get("ceilingUsd"),
            "withinCeiling": cost_event.get("withinCeiling"),
        },
        "privacyRedaction": privacy,
        "rollbackStopEvidence": {
            "stopFirst": readiness_doc.get("rollback", {}).get("stopFirst"),
            "mainnetRollback": readiness_doc.get("rollback", {}).get("mainnetRollback"),
            "operatorRollbackEvents": [
                event for event in positive_trace if event.get("event") in {"rollback.started", "rollback.completed"}
            ],
        },
        "mainnetApproval": {
            "approved": readiness_doc.get("approvals", {}).get("mainnetApproved"),
            "statement": readiness_doc.get("approvals", {}).get("mainnetStatement"),
            "requested": scenario.get("mainnetRequested") is True,
        },
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    readiness_base = load_json(READINESS_EVIDENCE)
    operator_base = load_json(OPERATOR_SCENARIOS)
    runtime_report = local_runtime_prototype.build_report()
    results = [
        build_evidence_for_scenario(scenario, readiness_base, operator_base, runtime_report)
        for scenario in doc.get("scenarios", [])
    ]
    fixture_mismatches = [
        {
            "path": f"results[{index}].status",
            "reason": f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}",
        }
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"]
    ]
    return {
        "mode": "beta-local-runtime-release-candidate-gate",
        "issue": 237,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not fixture_mismatches and all(result["status"] == result["expectedStatus"] for result in results) else "fail",
        "findings": fixture_mismatches,
        "boundaries": {
            "localRuntimeExecutionAllowed": True,
            "deterministicLocalFixturesOnly": True,
            "networkAccess": False,
            "credentialAccess": False,
            "mcpInvocation": False,
            "paymentAccess": False,
            "providerApiAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "externalSpend": False,
        },
        "mainnetStatement": "Mainnet deployment, settlement, and runtime execution are not approved; separate Nissan signoff is required.",
        "summary": {
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["status"] == "fail"),
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="?", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(load_json(Path(args.scenarios)))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 3


if __name__ == "__main__":
    sys.exit(main())
