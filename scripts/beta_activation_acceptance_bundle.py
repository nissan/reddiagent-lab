#!/usr/bin/env python3
"""Build a deterministic local beta activation acceptance bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-acceptance-scenarios.json"
PINNED_REHEARSAL_PACKAGE = ROOT / "tests" / "fixtures" / "beta-activation-rehearsal.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_rehearsal_package  # noqa: E402


ALLOWED_ACCEPTANCE_OUTCOMES = {"accept", "hold", "rollback-required"}
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
SENSITIVE_KEYS = beta_activation_rehearsal_package.SENSITIVE_KEYS | {
    "acceptancePayload",
    "activationPayload",
    "credentialPayload",
    "runtimeSecret",
}
SENSITIVE_KEY_NORMALIZED = beta_activation_rehearsal_package.SENSITIVE_KEY_NORMALIZED | {
    "acceptancepayload",
    "activationpayload",
    "credentialpayload",
    "runtimesecret",
}
HANDOFF_ACTIVATION_CLAIM_MARKERS = (
    "activation completed",
    "activation occurred",
    "runtime activation completed",
    "runtime activation occurred",
    "runtime activation succeeded",
    "runtime enabled",
    "live runtime enabled",
    "live runtime activation",
    "production enabled",
    "production gateway enabled",
    "mainnet enabled",
    "mainnet activation",
)


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
        if any(marker in lowered for marker in beta_activation_rehearsal_package.beta_activation_preflight_gate.SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like or private payload value is not allowed."))
    return findings


def handoff_activation_claim_findings(handoff: Any) -> list[dict[str, str]]:
    if not isinstance(handoff, str):
        return []
    lowered = handoff.lower()
    return [
        finding("nextStepHandoff", f"Next-step handoff must not claim activation, production, or mainnet enablement via marker `{marker}`.")
        for marker in HANDOFF_ACTIVATION_CLAIM_MARKERS
        if marker in lowered
    ]


def current_rehearsal_package() -> dict[str, Any]:
    return beta_activation_rehearsal_package.build_report(
        load_json(beta_activation_rehearsal_package.DEFAULT_SCENARIOS)
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


def evidence_hashes(rehearsal: dict[str, Any]) -> list[dict[str, Any]]:
    hashes = [
        artifact("tests/fixtures/beta-activation-acceptance-scenarios.json", "Activation acceptance scenario inputs."),
        artifact("tests/fixtures/beta-activation-rehearsal.json", "Pinned #260 activation rehearsal package."),
        artifact("tests/fixtures/beta-activation-rehearsal-scenarios.json", "Activation rehearsal scenario inputs."),
    ]
    for item in rehearsal.get("evidenceHashes", []):
        if item not in hashes:
            hashes.append(item)
    return hashes


def operator_transcript(scenario: dict[str, Any], outcome: str | None, status: str) -> list[dict[str, Any]]:
    release_id = scenario.get("releaseId")
    adl_path = scenario.get("selectedAdlPath")
    activation_cue = scenario.get("acceptedActivationCue")
    rollback_cue = scenario.get("rollbackCue")
    transcript = [
        {
            "step": 1,
            "command": f"operator:inspect-rehearsal --release {release_id} --adl {adl_path} --dry-run",
            "event": "acceptance.rehearsal_inspected",
            "stdoutStatus": "pass" if status == "pass" else "fail",
            "exitCode": 0 if status == "pass" else 3,
            "liveRuntimeEnabled": False,
        }
    ]
    if outcome == "accept":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:accept-activation --release {release_id} --cue {activation_cue} --dry-run",
                "event": "acceptance.activation_cue_accepted",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    elif outcome == "hold":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:hold-activation --release {release_id} --dry-run",
                "event": "acceptance.hold_recorded",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    elif outcome == "rollback-required":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:require-rollback --release {release_id} --cue {rollback_cue} --dry-run",
                "event": "acceptance.rollback_required_recorded",
                "stdoutStatus": "pass" if status == "pass" else "fail",
                "exitCode": 0 if status == "pass" else 3,
                "liveRuntimeEnabled": False,
            }
        )
    transcript.append(
        {
            "step": 3,
            "command": f"operator:handoff-next-step --release {release_id} --dry-run",
            "event": "acceptance.no_live_enablement_handoff",
            "stdoutStatus": "pass" if status == "pass" else "fail",
            "exitCode": 0 if status == "pass" else 3,
            "liveRuntimeEnabled": False,
        }
    )
    return transcript


def operator_checklist(status: str, outcome: str | None) -> list[dict[str, str]]:
    checks = [
        ("rehearsal-current", "Current rehearsal evidence matches pinned #260 package."),
        ("local-approval", "Reviewer identity or local approval fixture is present."),
        ("dry-run-only", "Every acceptance command is explicitly dry-run only."),
        ("rollback-disable-evidence", "Rollback and disable evidence remains bound before acceptance passes."),
        ("no-live-enable-claim", "The package makes no live runtime enablement claim."),
        ("next-step-handoff", "Next-step handoff says no live runtime enablement is claimed."),
    ]
    if outcome == "accept":
        checks.append(("accepted-activation-cue", "Accepted activation bundles include an accepted activation cue."))
    if outcome == "rollback-required":
        checks.append(("rollback-cue", "Rollback-required bundles include a rollback cue."))
    return [{"id": check_id, "label": label, "status": "pass" if status == "pass" else "blocked"} for check_id, label in checks]


def collect_findings(
    scenario: dict[str, Any],
    pinned_rehearsal: dict[str, Any],
    current_rehearsal: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    outcome = scenario.get("acceptanceOutcome")
    boundaries = scenario.get("boundaryStatus", {})
    rollback_evidence = scenario.get("rollbackDisableEvidence", {})
    rehearsal = result_by_id(pinned_rehearsal, scenario.get("sourceRehearsalResultId"))

    require(pinned_rehearsal.get("status") == "pass", "rehearsalPackage.status", "Pinned activation rehearsal package must pass.")
    require(current_rehearsal == pinned_rehearsal, "rehearsalPackage.currentEvidence", "Current rehearsal evidence must match the pinned #260 artifact.")
    require(scenario.get("sourceRehearsalPackagePath") == "tests/fixtures/beta-activation-rehearsal.json", "sourceRehearsalPackagePath", "Source rehearsal package path must match the pinned #260 artifact.")
    require(outcome in ALLOWED_ACCEPTANCE_OUTCOMES, "acceptanceOutcome", "Acceptance outcome must be accept, hold, or rollback-required.")
    require(rehearsal is not None, "sourceRehearsalResultId", "Acceptance must bind to a source rehearsal result.")
    require(scenario.get("releaseId") == pinned_rehearsal.get("releaseId"), "releaseId", "Acceptance release id must match the rehearsal package.")
    require(bool(scenario.get("selectedAdlPath")), "selectedAdlPath", "Selected ADL path is required.")
    require(bool(scenario.get("operatorIdentity")), "operatorIdentity", "Operator identity is required.")
    require(bool(scenario.get("acceptanceTimestamp")), "acceptanceTimestamp", "Acceptance timestamp or fixture value is required.")
    require(bool(scenario.get("reviewerIdentity")) or bool(scenario.get("localApprovalFixture")), "reviewerIdentity", "Reviewer identity or local approval fixture is required.")

    if rehearsal:
        require(rehearsal.get("status") == "pass", "sourceRehearsal.status", "Source rehearsal result must pass before acceptance.")
        expected_rehearsal_outcome = {
            "accept": "approve",
            "hold": "hold",
            "rollback-required": "rollback",
        }.get(outcome)
        require(rehearsal.get("rehearsalOutcome") == expected_rehearsal_outcome, "acceptanceOutcome", "Acceptance outcome must match the bound source rehearsal outcome.")
        require(rehearsal.get("releaseId") == scenario.get("releaseId"), "sourceRehearsal.releaseId", "Source rehearsal release id must match acceptance release.")
        require(rehearsal.get("selectedAdlPath") == scenario.get("selectedAdlPath"), "selectedAdlPath", "Selected ADL path must match the source rehearsal.")
        require(rehearsal.get("operatorIdentity") == scenario.get("operatorIdentity"), "operatorIdentity", "Operator identity must match the source rehearsal.")
        require(rehearsal.get("sourcePreflightPackagePath") == scenario.get("sourcePreflightPackagePath"), "sourcePreflightPackagePath", "Preflight package path must match source rehearsal.")
        require(rehearsal.get("sourceDecisionPackagePath") == scenario.get("sourceDecisionPackagePath"), "sourceDecisionPackagePath", "Decision package path must match source rehearsal.")
        require(rehearsal.get("sourceReviewPackagePath") == scenario.get("sourceReviewPackagePath"), "sourceReviewPackagePath", "Review package path must match source rehearsal.")
        require(rehearsal.get("sourceRuntimePackagePath") == scenario.get("sourceRuntimePackagePath"), "sourceRuntimePackagePath", "Runtime package path must match source rehearsal.")
        require(rehearsal.get("activationCue") == scenario.get("acceptedActivationCue"), "acceptedActivationCue", "Accepted activation cue must match source rehearsal.")
        require(rehearsal.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackCue", "Rollback cue must match source rehearsal.")

    if outcome == "accept":
        require(bool(scenario.get("acceptedActivationCue")), "acceptedActivationCue", "Accept bundles require an accepted activation cue.")
    if outcome == "rollback-required":
        require(bool(scenario.get("rollbackCue")), "rollbackCue", "Rollback-required bundles require an explicit rollback cue.")

    require(isinstance(rollback_evidence, dict), "rollbackDisableEvidence", "Rollback/disable evidence is required.")
    if isinstance(rollback_evidence, dict):
        require(rollback_evidence.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackDisableEvidence.rollbackCue", "Rollback evidence must bind to the acceptance rollback cue.")
        require(rollback_evidence.get("disableVerified") is True, "rollbackDisableEvidence.disableVerified", "Disable evidence must be verified.")
        require(rollback_evidence.get("dryRunOnly") is True, "rollbackDisableEvidence.dryRunOnly", "Rollback/disable evidence must be dry-run only.")
        require(rollback_evidence.get("liveRuntimeEnabled") is False, "rollbackDisableEvidence.liveRuntimeEnabled", "Rollback/disable evidence must not enable live runtime.")

    require(scenario.get("liveRuntimeRequested") is False, "liveRuntimeRequested", "Live runtime requests are out of scope for this acceptance bundle.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet requests are not part of this local acceptance bundle.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet requests require fresh Nissan approval.")
    require(scenario.get("productionEnabled") is False, "productionEnabled", "Production enablement is not allowed.")
    require(scenario.get("mainnetEnabled") is False, "mainnetEnabled", "Mainnet enablement is not allowed.")
    require(scenario.get("claimsLiveRuntimeEnablement") is False, "claimsLiveRuntimeEnablement", "Acceptance packages must not claim live runtime enablement.")

    handoff = scenario.get("nextStepHandoff", "")
    require(isinstance(handoff, str) and bool(handoff.strip()), "nextStepHandoff", "Next-step handoff text is required.")
    require("no live runtime enablement" in handoff.lower(), "nextStepHandoff", "Next-step handoff must explicitly avoid live runtime enablement claims.")
    findings.extend(handoff_activation_claim_findings(handoff))

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaryStatus.{key}", f"{key} must be false.")
    require(boundaries.get("activationAcceptanceBundle") is True, "boundaryStatus.activationAcceptanceBundle", "Activation acceptance boundary must be explicit.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaryStatus.deterministicLocalFixturesOnly", "Activation acceptance must be fixture-only.")

    for index, item in enumerate(evidence_hashes(rehearsal or {})):
        require(item.get("exists") is True, f"evidenceHashes[{index}].exists", "Evidence hash entries must exist.")
        require(bool(item.get("sha256")), f"evidenceHashes[{index}].sha256", "Evidence hash entries must include sha256.")

    findings.extend(sensitive_findings(scenario, "scenario"))
    return findings


def acceptance_status(outcome: str | None, status: str) -> str:
    if status == "fail":
        return "blocked-acceptance"
    if outcome == "accept":
        return "acceptance-ready"
    if outcome == "hold":
        return "acceptance-held"
    if outcome == "rollback-required":
        return "rollback-required"
    return "blocked-acceptance"


def build_result(
    scenario: dict[str, Any],
    pinned_rehearsal: dict[str, Any],
    current_rehearsal: dict[str, Any],
) -> dict[str, Any]:
    findings = collect_findings(scenario, pinned_rehearsal, current_rehearsal)
    rehearsal = result_by_id(pinned_rehearsal, scenario.get("sourceRehearsalResultId")) or {}
    status = "pass" if not findings else "fail"
    outcome = scenario.get("acceptanceOutcome")
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "acceptanceOutcome": outcome,
        "acceptanceStatus": acceptance_status(outcome, status),
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "releaseId": scenario.get("releaseId"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "sourceRehearsalPackagePath": scenario.get("sourceRehearsalPackagePath"),
        "sourceRehearsalResultId": scenario.get("sourceRehearsalResultId"),
        "sourceRehearsalOutcome": rehearsal.get("rehearsalOutcome"),
        "sourcePreflightPackagePath": scenario.get("sourcePreflightPackagePath"),
        "sourceDecisionPackagePath": scenario.get("sourceDecisionPackagePath"),
        "sourceReviewPackagePath": scenario.get("sourceReviewPackagePath"),
        "sourceRuntimePackagePath": scenario.get("sourceRuntimePackagePath"),
        "operatorIdentity": scenario.get("operatorIdentity"),
        "reviewerIdentity": scenario.get("reviewerIdentity"),
        "localApprovalFixture": scenario.get("localApprovalFixture"),
        "acceptanceTimestamp": scenario.get("acceptanceTimestamp"),
        "acceptedActivationCue": scenario.get("acceptedActivationCue"),
        "rollbackCue": scenario.get("rollbackCue"),
        "rollbackDisableEvidence": scenario.get("rollbackDisableEvidence"),
        "operatorTranscript": operator_transcript(scenario, outcome, status),
        "operatorChecklist": operator_checklist(status, outcome),
        "nextStepHandoff": scenario.get("nextStepHandoff"),
        "boundaryStatus": scenario.get("boundaryStatus", {}),
        "liveRuntimeRequested": scenario.get("liveRuntimeRequested"),
        "devnetRequested": scenario.get("devnetRequested"),
        "mainnetRequested": scenario.get("mainnetRequested"),
        "productionEnabled": scenario.get("productionEnabled"),
        "mainnetEnabled": scenario.get("mainnetEnabled"),
        "claimsLiveRuntimeEnablement": scenario.get("claimsLiveRuntimeEnablement"),
        "evidenceHashes": evidence_hashes(rehearsal),
        "liveRuntimeEnablementClaim": "none",
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    pinned_rehearsal = load_json(PINNED_REHEARSAL_PACKAGE)
    current_rehearsal = current_rehearsal_package()
    defaults = doc.get("defaults", {})
    results = [
        build_result(merge_scenario(defaults, scenario), pinned_rehearsal, current_rehearsal)
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
        "mode": "beta-local-activation-acceptance-bundle",
        "issue": 262,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "activationAcceptanceBundle": True,
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
            "rehearsalPackage": {
                "source": "tests/fixtures/beta-activation-rehearsal.json",
                "status": pinned_rehearsal.get("status"),
                "currentEvidenceMatchesPinned": current_rehearsal == pinned_rehearsal,
                "sha256": digest(PINNED_REHEARSAL_PACKAGE),
            }
        },
        "summary": {
            "acceptBundles": sum(1 for result in results if result["acceptanceOutcome"] == "accept"),
            "holdBundles": sum(1 for result in results if result["acceptanceOutcome"] == "hold"),
            "rollbackRequiredBundles": sum(1 for result in results if result["acceptanceOutcome"] == "rollback-required"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "mainnetStatement": "This local activation acceptance bundle does not enable production or mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        default=str(DEFAULT_SCENARIOS),
        help="Path to activation acceptance scenario JSON. Defaults to the pinned fixture input.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    doc = load_json(Path(args.scenarios))
    report = build_report(doc)
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
