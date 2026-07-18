#!/usr/bin/env python3
"""Build a deterministic local beta activation rehearsal package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-rehearsal-scenarios.json"
PINNED_PREFLIGHT_PACKAGE = ROOT / "tests" / "fixtures" / "beta-activation-preflight.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_preflight_gate  # noqa: E402


ALLOWED_REHEARSAL_OUTCOMES = {"approve", "hold", "rollback"}
REQUIRED_BOUNDARY_FALSE = (
    "liveRuntimeActivation",
    "networkAccess",
    "credentialAccess",
    "mcpInvocation",
    "paymentAccess",
    "providerApiAccess",
    "devnetAccess",
    "productionGatewayAccess",
    "mainnetAccess",
    "externalSpend",
)
SENSITIVE_KEYS = beta_activation_preflight_gate.SENSITIVE_KEYS | {
    "activationPayload",
    "credentialPayload",
    "runtimeSecret",
}
SENSITIVE_KEY_NORMALIZED = beta_activation_preflight_gate.SENSITIVE_KEY_NORMALIZED | {
    "activationpayload",
    "credentialpayload",
    "runtimesecret",
}


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


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def sensitive_findings(value: Any, path: str = "$") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized_key = key.lower().replace("_", "").replace("-", "")
            if key in SENSITIVE_KEYS or normalized_key in SENSITIVE_KEY_NORMALIZED:
                findings.append(finding(child_path, "Credential-like, private, or live activation payload key is not allowed."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in beta_activation_preflight_gate.SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like or private payload value is not allowed."))
    return findings


def current_preflight_package() -> dict[str, Any]:
    return beta_activation_preflight_gate.build_report(
        load_json(beta_activation_preflight_gate.DEFAULT_SCENARIOS)
    )


def result_by_id(package: dict[str, Any], result_id: str | None) -> dict[str, Any] | None:
    for result in package.get("results", []):
        if result.get("id") == result_id:
            return result
    return None


def merge_scenario(defaults: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def evidence_hashes(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    hashes = [
        artifact("tests/fixtures/beta-activation-rehearsal-scenarios.json", "Activation rehearsal scenario inputs."),
        artifact("tests/fixtures/beta-activation-preflight.json", "Pinned #258 activation preflight package."),
        artifact("tests/fixtures/beta-activation-preflight-scenarios.json", "Activation preflight scenario inputs."),
    ]
    for item in preflight.get("evidenceHashes", []):
        if item not in hashes:
            hashes.append(item)
    return hashes


def operator_transcript(scenario: dict[str, Any], outcome: str | None, status: str) -> list[dict[str, Any]]:
    release_id = scenario.get("releaseId")
    adl_path = scenario.get("selectedAdlPath")
    activation_cue = scenario.get("activationCue")
    rollback_cue = scenario.get("rollbackCue")
    transcript = [
        {
            "step": 1,
            "command": f"operator:inspect-preflight --release {release_id} --adl {adl_path} --dry-run",
            "event": "rehearsal.preflight_inspected",
            "stdoutStatus": "pass" if status == "pass" else "fail",
            "exitCode": 0 if status == "pass" else 3,
            "liveRuntimeEnabled": False,
        }
    ]
    if outcome == "approve":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:activate --release {release_id} --cue {activation_cue} --dry-run",
                "event": "rehearsal.activation_cue_recorded",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    elif outcome == "hold":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:hold --release {release_id} --dry-run",
                "event": "rehearsal.hold_cue_recorded",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    elif outcome == "rollback":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:rollback --release {release_id} --cue {rollback_cue} --dry-run",
                "event": "rehearsal.rollback_cue_recorded",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    transcript.append(
        {
            "step": 3,
            "command": f"operator:disable-check --release {release_id} --dry-run",
            "event": "rehearsal.rollback_disable_evidence_verified",
            "stdoutStatus": "pass" if status == "pass" else "fail",
            "exitCode": 0 if status == "pass" else 3,
            "liveRuntimeEnabled": False,
        }
    )
    return transcript


def operator_checklist(scenario: dict[str, Any], outcome: str | None, status: str) -> list[dict[str, Any]]:
    checks = [
        ("preflight-current", "Current preflight evidence matches pinned #258 package."),
        ("dry-run-only", "Every operator command is explicitly dry-run only."),
        ("rollback-disable-evidence", "Rollback and disable evidence is present before any activation rehearsal passes."),
        ("no-live-enable-claim", "The package makes no live runtime enablement claim."),
    ]
    if outcome == "approve":
        checks.append(("activation-cue", "Approve rehearsals include an activation cue."))
    if outcome == "rollback":
        checks.append(("rollback-cue", "Rollback rehearsals include a rollback cue."))
    return [{"id": check_id, "label": label, "status": "pass" if status == "pass" else "blocked"} for check_id, label in checks]


def collect_findings(
    scenario: dict[str, Any],
    pinned_preflight: dict[str, Any],
    current_preflight: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    outcome = scenario.get("rehearsalOutcome")
    boundaries = scenario.get("boundaryStatus", {})
    rollback_evidence = scenario.get("rollbackDisableEvidence", {})
    preflight = result_by_id(pinned_preflight, scenario.get("preflightResultId"))

    require(pinned_preflight.get("status") == "pass", "preflightPackage.status", "Pinned activation preflight package must pass.")
    require(current_preflight == pinned_preflight, "preflightPackage.currentEvidence", "Current preflight evidence must match the pinned #258 artifact.")
    require(scenario.get("sourcePreflightPackagePath") == "tests/fixtures/beta-activation-preflight.json", "sourcePreflightPackagePath", "Source preflight package path must match the pinned #258 artifact.")
    require(outcome in ALLOWED_REHEARSAL_OUTCOMES, "rehearsalOutcome", "Rehearsal outcome must be approve, hold, or rollback.")
    require(preflight is not None, "preflightResultId", "Rehearsal must bind to a source preflight result.")
    require(scenario.get("releaseId") == pinned_preflight.get("releaseId"), "releaseId", "Rehearsal release id must match the preflight package.")
    require(bool(scenario.get("selectedAdlPath")), "selectedAdlPath", "Selected ADL path is required.")
    require(bool(scenario.get("operatorIdentity")), "operatorIdentity", "Operator identity is required.")
    require(bool(scenario.get("rehearsalTimestamp")), "rehearsalTimestamp", "Rehearsal timestamp or fixture value is required.")

    if preflight:
        require(preflight.get("status") == "pass", "preflightResult.status", "Source preflight result must pass before rehearsal.")
        require(preflight.get("preflightOutcome") == outcome, "rehearsalOutcome", "Rehearsal outcome must match the bound source preflight outcome.")
        require(preflight.get("releaseId") == scenario.get("releaseId"), "preflightResult.releaseId", "Source preflight release id must match rehearsal release.")
        require(preflight.get("selectedAdlPath") == scenario.get("selectedAdlPath"), "selectedAdlPath", "Selected ADL path must match the source preflight.")
        require(preflight.get("operatorIdentity") == scenario.get("operatorIdentity"), "operatorIdentity", "Operator identity must match the source preflight.")
        require(preflight.get("sourceDecisionPackagePath") == scenario.get("sourceDecisionPackagePath"), "sourceDecisionPackagePath", "Decision package path must match source preflight.")
        require(preflight.get("sourceReviewPackagePath") == scenario.get("sourceReviewPackagePath"), "sourceReviewPackagePath", "Review package path must match source preflight.")
        require(preflight.get("sourceRuntimePackagePath") == scenario.get("sourceRuntimePackagePath"), "sourceRuntimePackagePath", "Runtime package path must match source preflight.")
        require(preflight.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackCue", "Rollback cue must match source preflight.")

    if outcome == "approve":
        require(bool(scenario.get("activationCue")), "activationCue", "Approve rehearsals require an explicit activation cue.")
    if outcome == "rollback":
        require(bool(scenario.get("rollbackCue")), "rollbackCue", "Rollback rehearsals require an explicit rollback cue.")
    if outcome in {"approve", "hold"}:
        require("rollbackCue" in scenario, "rollbackCue", "Rollback cue field must be present for audit binding.")

    require(isinstance(rollback_evidence, dict), "rollbackDisableEvidence", "Rollback/disable evidence is required.")
    if isinstance(rollback_evidence, dict):
        require(rollback_evidence.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackDisableEvidence.rollbackCue", "Rollback evidence must bind to the rehearsal rollback cue.")
        require(rollback_evidence.get("disableVerified") is True, "rollbackDisableEvidence.disableVerified", "Disable evidence must be verified.")
        require(rollback_evidence.get("dryRunOnly") is True, "rollbackDisableEvidence.dryRunOnly", "Rollback/disable evidence must be dry-run only.")
        require(rollback_evidence.get("liveRuntimeEnabled") is False, "rollbackDisableEvidence.liveRuntimeEnabled", "Rollback/disable evidence must not enable live runtime.")

    require(scenario.get("liveRuntimeRequested") is False, "liveRuntimeRequested", "Live runtime requests are out of scope for this rehearsal.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet requests are not part of this local rehearsal.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet requests require fresh Nissan approval.")
    require(scenario.get("productionEnabled") is False, "productionEnabled", "Production enablement is not allowed.")
    require(scenario.get("mainnetEnabled") is False, "mainnetEnabled", "Mainnet enablement is not allowed.")
    require(scenario.get("claimsLiveRuntimeEnablement") is False, "claimsLiveRuntimeEnablement", "Rehearsal packages must not claim live runtime enablement.")

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaryStatus.{key}", f"{key} must be false.")
    require(boundaries.get("activationRehearsalPackage") is True, "boundaryStatus.activationRehearsalPackage", "Activation rehearsal boundary must be explicit.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaryStatus.deterministicLocalFixturesOnly", "Activation rehearsal must be fixture-only.")

    for index, item in enumerate(evidence_hashes(preflight or {})):
        require(item.get("exists") is True, f"evidenceHashes[{index}].exists", "Evidence hash entries must exist.")
        require(bool(item.get("sha256")), f"evidenceHashes[{index}].sha256", "Evidence hash entries must include sha256.")

    findings.extend(sensitive_findings(scenario, "scenario"))
    return findings


def rehearsal_status(outcome: str | None, status: str) -> str:
    if status == "fail":
        return "blocked-rehearsal"
    if outcome == "approve":
        return "approve-rehearsal-ready"
    if outcome == "hold":
        return "hold-rehearsal-ready"
    if outcome == "rollback":
        return "rollback-rehearsal-ready"
    return "blocked-rehearsal"


def build_result(
    scenario: dict[str, Any],
    pinned_preflight: dict[str, Any],
    current_preflight: dict[str, Any],
) -> dict[str, Any]:
    findings = collect_findings(scenario, pinned_preflight, current_preflight)
    preflight = result_by_id(pinned_preflight, scenario.get("preflightResultId")) or {}
    status = "pass" if not findings else "fail"
    outcome = scenario.get("rehearsalOutcome")
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "rehearsalOutcome": outcome,
        "rehearsalStatus": rehearsal_status(outcome, status),
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "releaseId": scenario.get("releaseId"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "sourcePreflightPackagePath": scenario.get("sourcePreflightPackagePath"),
        "sourceDecisionPackagePath": scenario.get("sourceDecisionPackagePath"),
        "sourceReviewPackagePath": scenario.get("sourceReviewPackagePath"),
        "sourceRuntimePackagePath": scenario.get("sourceRuntimePackagePath"),
        "preflightResultId": scenario.get("preflightResultId"),
        "preflightOutcome": preflight.get("preflightOutcome"),
        "operatorIdentity": scenario.get("operatorIdentity"),
        "rehearsalTimestamp": scenario.get("rehearsalTimestamp"),
        "activationCue": scenario.get("activationCue"),
        "rollbackCue": scenario.get("rollbackCue"),
        "rollbackDisableEvidence": scenario.get("rollbackDisableEvidence"),
        "operatorTranscript": operator_transcript(scenario, outcome, status),
        "operatorChecklist": operator_checklist(scenario, outcome, status),
        "boundaryStatus": scenario.get("boundaryStatus", {}),
        "liveRuntimeRequested": scenario.get("liveRuntimeRequested"),
        "devnetRequested": scenario.get("devnetRequested"),
        "mainnetRequested": scenario.get("mainnetRequested"),
        "productionEnabled": scenario.get("productionEnabled"),
        "mainnetEnabled": scenario.get("mainnetEnabled"),
        "claimsLiveRuntimeEnablement": scenario.get("claimsLiveRuntimeEnablement"),
        "evidenceHashes": evidence_hashes(preflight),
        "liveRuntimeEnablementClaim": "none",
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    pinned_preflight = load_json(PINNED_PREFLIGHT_PACKAGE)
    current_preflight = current_preflight_package()
    defaults = doc.get("defaults", {})
    results = [
        build_result(merge_scenario(defaults, scenario), pinned_preflight, current_preflight)
        for scenario in doc.get("scenarios", [])
    ]
    mismatches = [
        finding(
            f"results[{index}].status",
            f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}",
        )
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"]
    ]
    return {
        "mode": "beta-local-activation-rehearsal-package",
        "issue": 260,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "activationRehearsalPackage": True,
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
        "sourcePackageEvidence": {
            "preflightPackage": {
                "source": "tests/fixtures/beta-activation-preflight.json",
                "status": pinned_preflight.get("status"),
                "currentEvidenceMatchesPinned": current_preflight == pinned_preflight,
            }
        },
        "summary": {
            "approveRehearsals": sum(1 for result in results if result["rehearsalOutcome"] == "approve"),
            "holdRehearsals": sum(1 for result in results if result["rehearsalOutcome"] == "hold"),
            "rollbackRehearsals": sum(1 for result in results if result["rehearsalOutcome"] == "rollback"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["status"] == "fail"),
        },
        "mainnetStatement": "This local activation rehearsal does not enable production or mainnet; mainnet remains blocked until fresh Nissan approval.",
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
