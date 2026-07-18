#!/usr/bin/env python3
"""Build an operator-facing local beta dry-run review package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package-scenarios.json"
PINNED_RC_GATE = ROOT / "tests" / "fixtures" / "beta-local-runtime-rc-gate.json"
RC_GATE_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-local-runtime-rc-gate-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_local_runtime_rc_gate  # noqa: E402


REQUIRED_BOUNDARIES = {
    "networkAccess": False,
    "credentialAccess": False,
    "mcpInvocation": False,
    "paymentAccess": False,
    "providerApiAccess": False,
    "devnetAccess": False,
    "mainnetAccess": False,
    "externalSpend": False,
}
REQUIRED_STOP_EVENTS = {"runtime.disabled", "rollback.started", "rollback.completed"}
PASS_STATUSES = {"pass", "success"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path_text: str, purpose: str) -> dict[str, Any]:
    path = ROOT / path_text
    return {
        "path": path_text,
        "purpose": purpose,
        "exists": path.exists(),
        "sha256": digest(path) if path.exists() and path.is_file() else None,
    }


def positive_rc_result(rc_gate: dict[str, Any]) -> dict[str, Any] | None:
    for result in rc_gate.get("results", []):
        if result.get("kind") == "positive" and result.get("status") == "pass":
            return result
    return None


def transcript_events(transcript: list[dict[str, Any]]) -> set[str]:
    return {
        str(entry.get("event"))
        for entry in transcript
        if entry.get("event")
    }


def transcript_commands(transcript: list[dict[str, Any]]) -> list[str]:
    return [
        str(entry.get("command"))
        for entry in transcript
        if entry.get("command")
    ]


def transcript_entry_passes(entry: dict[str, Any]) -> bool:
    return entry.get("exitCode") == 0 and str(entry.get("stdoutStatus", "")).lower() in PASS_STATUSES


def passing_commands(transcript: list[dict[str, Any]]) -> set[str]:
    return {
        str(entry.get("command"))
        for entry in transcript
        if entry.get("command") and transcript_entry_passes(entry)
    }


def passing_events(transcript: list[dict[str, Any]]) -> set[str]:
    return {
        str(entry.get("event"))
        for entry in transcript
        if entry.get("event") and transcript_entry_passes(entry)
    }


def collect_findings(
    scenario: dict[str, Any],
    pinned_rc: dict[str, Any],
    current_rc: dict[str, Any],
    rc_positive: dict[str, Any] | None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append({"path": path, "reason": reason})

    operator_id = scenario.get("operatorIdentity")
    selected_adl = scenario.get("selectedAdlPath")
    command_transcript = scenario.get("operatorCommandTranscript", [])
    stop_transcript = scenario.get("stopRollbackDryRunTranscript", [])
    command_lines = transcript_commands(command_transcript)
    passed_command_lines = passing_commands(command_transcript)
    stop_events = transcript_events(stop_transcript)
    passed_stop_events = passing_events(stop_transcript)
    rc_boundaries = pinned_rc.get("boundaries", {})
    package_command = "python scripts/beta_operator_dry_run_package.py"
    selected_runtime_command = rc_positive.get("selectedRuntime", {}).get("command") if rc_positive else None

    require(pinned_rc.get("status") == "pass", "rcGate.status", "Pinned RC gate evidence must pass.")
    require(current_rc == pinned_rc, "rcGate.currentEvidence", "Current RC gate output must match the pinned artifact.")
    require(
        scenario.get("rcGateReleaseId") == pinned_rc.get("releaseId"),
        "rcGate.releaseId",
        "Scenario RC gate release must match the pinned RC gate release.",
    )
    require(bool(operator_id), "operatorIdentity", "Operator identity is required for review evidence.")
    require(bool(selected_adl), "selectedAdlPath", "Selected ADL path is required.")
    if selected_adl:
        require((ROOT / str(selected_adl)).exists(), "selectedAdlPath", "Selected ADL path must exist locally.")
    if rc_positive:
        require(
            selected_adl == rc_positive.get("selectedRuntime", {}).get("adl"),
            "selectedAdlPath",
            "Selected ADL path must match the passing RC gate runtime path.",
        )
    require(
        package_command in command_lines,
        "operatorCommandTranscript",
        "Operator transcript must include the package checker command.",
    )
    require(
        package_command in passed_command_lines,
        "operatorCommandTranscript.packageCommand",
        "Package checker transcript row must exit 0 with pass/success status.",
    )
    require(
        bool(selected_runtime_command and selected_runtime_command in command_lines),
        "operatorCommandTranscript",
        "Operator transcript must include the selected local runtime command from RC evidence.",
    )
    require(
        bool(selected_runtime_command and selected_runtime_command in passed_command_lines),
        "operatorCommandTranscript.selectedRuntimeCommand",
        "Selected local runtime transcript row must exit 0 with pass/success status.",
    )
    require(
        REQUIRED_STOP_EVENTS.issubset(stop_events),
        "stopRollbackDryRunTranscript",
        "Stop/rollback dry-run transcript must include disable, rollback start, and rollback complete events.",
    )
    require(
        REQUIRED_STOP_EVENTS.issubset(passed_stop_events),
        "stopRollbackDryRunTranscript",
        "Every required stop/rollback transcript row must exit 0 with pass/success status.",
    )
    require(scenario.get("runtimeMode") == "local-only", "runtimeMode", "Runtime mode must be local-only.")
    require(scenario.get("environment") == "local", "environment", "Environment must be local.")
    require(scenario.get("liveRuntimeRequested") is not True, "liveRuntimeRequested", "Live runtime requests are out of scope.")
    require(scenario.get("mainnetRequested") is not True, "mainnetRequested", "Mainnet requests require separate Nissan approval.")
    require(
        pinned_rc.get("mainnetStatement") and "not approved" in pinned_rc["mainnetStatement"].lower(),
        "rcGate.mainnetStatement",
        "RC gate must carry explicit mainnet-not-approved language.",
    )
    for key, expected in REQUIRED_BOUNDARIES.items():
        require(rc_boundaries.get(key) is expected, f"rcGate.boundaries.{key}", f"{key} must be {expected}.")

    return findings


def build_result(
    scenario: dict[str, Any],
    pinned_rc: dict[str, Any],
    current_rc: dict[str, Any],
    rc_positive: dict[str, Any] | None,
) -> dict[str, Any]:
    findings = collect_findings(scenario, pinned_rc, current_rc, rc_positive)
    selected_runtime = rc_positive.get("selectedRuntime", {}) if rc_positive else {}
    stop_transcript = scenario.get("stopRollbackDryRunTranscript", [])
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "status": "pass" if not findings else "fail",
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "operatorIdentity": scenario.get("operatorIdentity"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "runtimeMode": scenario.get("runtimeMode"),
        "environment": scenario.get("environment"),
        "liveRuntimeRequested": scenario.get("liveRuntimeRequested", False),
        "mainnetRequested": scenario.get("mainnetRequested", False),
        "operatorCommandTranscript": scenario.get("operatorCommandTranscript", []),
        "stopRollbackDryRunTranscript": stop_transcript,
        "rcGateEvidence": {
            "source": "tests/fixtures/beta-local-runtime-rc-gate.json",
            "releaseId": pinned_rc.get("releaseId"),
            "status": pinned_rc.get("status"),
            "currentEvidenceMatchesPinned": current_rc == pinned_rc,
            "selectedRuntimeCommand": selected_runtime.get("command"),
            "selectedRuntimeCompletion": selected_runtime.get("completionStatus"),
            "mainnetStatement": pinned_rc.get("mainnetStatement"),
        },
        "evidenceIndex": [
            artifact("tests/fixtures/beta-local-runtime-rc-gate.json", "Pinned beta RC gate artifact from #237."),
            artifact("tests/fixtures/beta-local-runtime-rc-gate-scenarios.json", "RC gate scenario inputs."),
            artifact("tests/fixtures/beta-release-readiness.json", "Readiness, approvals, rollback, cost, and privacy evidence."),
            artifact("tests/fixtures/beta-operator-control-harness.json", "Operator-control trace evidence."),
            artifact("tests/fixtures/local-executable-runtime-prototype.json", "Selected local runtime dry-run evidence."),
            artifact("tests/fixtures/beta-operator-dry-run-package-scenarios.json", "Operator package scenario inputs."),
        ],
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    pinned_rc = load_json(PINNED_RC_GATE)
    current_rc = beta_local_runtime_rc_gate.build_report(load_json(RC_GATE_SCENARIOS))
    rc_positive = positive_rc_result(pinned_rc)
    results = [build_result(scenario, pinned_rc, current_rc, rc_positive) for scenario in doc.get("scenarios", [])]
    mismatches = [
        {
            "path": f"results[{index}].status",
            "reason": f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}",
        }
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"]
    ]
    return {
        "mode": "beta-local-operator-dry-run-package",
        "issue": 240,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "operatorFacingLocalDryRun": True,
            "deterministicLocalFixturesOnly": True,
            "liveRuntimeActivation": False,
            "networkAccess": False,
            "credentialAccess": False,
            "mcpInvocation": False,
            "paymentAccess": False,
            "providerApiAccess": False,
            "devnetAccess": False,
            "productionGatewayAccess": False,
            "mainnetAccess": False,
            "externalSpend": False,
        },
        "mainnetStatement": "Mainnet deployment, settlement, and runtime execution remain not approved and require separate Nissan signoff.",
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
