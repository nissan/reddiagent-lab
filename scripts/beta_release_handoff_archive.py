#!/usr/bin/env python3
"""Build deterministic local beta release handoff archives."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-handoff-scenarios.json"
PINNED_ACCEPTANCE_BUNDLE = ROOT / "tests" / "fixtures" / "beta-activation-acceptance.json"
PINNED_RUNTIME_PROTOTYPE = ROOT / "tests" / "fixtures" / "local-executable-runtime-prototype.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_activation_acceptance_bundle  # noqa: E402


ALLOWED_HANDOFF_OUTCOMES = {"accepted", "hold", "rollback-required"}
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
    "deploymentPublished",
    "packagePublished",
)
SENSITIVE_KEYS = beta_activation_acceptance_bundle.SENSITIVE_KEYS | {
    "handoffPayload",
    "releasePayload",
    "credentialPayload",
    "deploymentSecret",
}
SENSITIVE_KEY_NORMALIZED = beta_activation_acceptance_bundle.SENSITIVE_KEY_NORMALIZED | {
    "handoffpayload",
    "releasepayload",
    "credentialpayload",
    "deploymentsecret",
}
HANDOFF_CLAIM_MARKERS = (
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
    "deployed to production",
    "deployment completed",
    "published package",
    "release activated",
)
ADL_V02_VALID_RUNTIME_SCENARIO_ID = "adl-v02-memory-observability-dry-run"
ADL_V02_INVALID_DIAGNOSTIC_SCENARIO_ID = "invalid-adl-v02-payment-diagnostics"
STABLE_DIAGNOSTIC_FIELDS = ("code", "severity", "category", "path", "line", "column")


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
                findings.append(finding(child_path, "Credential-like, private, or live handoff payload key is not allowed."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in beta_activation_acceptance_bundle.beta_activation_rehearsal_package.beta_activation_preflight_gate.SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like or private payload value is not allowed."))
    return findings


def handoff_claim_findings(handoff: Any) -> list[dict[str, str]]:
    if not isinstance(handoff, str):
        return []
    lowered = handoff.lower()
    return [
        finding("nextStepHandoff", f"Next-step handoff must not claim activation, deployment, production, or mainnet completion via marker `{marker}`.")
        for marker in HANDOFF_CLAIM_MARKERS
        if marker in lowered
    ]


def current_acceptance_bundle() -> dict[str, Any]:
    return beta_activation_acceptance_bundle.build_report(
        load_json(beta_activation_acceptance_bundle.DEFAULT_SCENARIOS)
    )


def runtime_scenario_by_id(runtime: dict[str, Any], scenario_id: str) -> dict[str, Any] | None:
    for scenario in runtime.get("scenarios", []):
        if scenario.get("id") == scenario_id:
            return scenario
    return None


def adl_v02_runtime_evidence(runtime_prototype_path: Path = PINNED_RUNTIME_PROTOTYPE) -> dict[str, Any]:
    runtime = load_json(runtime_prototype_path)
    valid = runtime_scenario_by_id(runtime, ADL_V02_VALID_RUNTIME_SCENARIO_ID) or {}
    invalid = runtime_scenario_by_id(runtime, ADL_V02_INVALID_DIAGNOSTIC_SCENARIO_ID) or {}
    diagnostics = invalid.get("validationDiagnostics") or []
    stable_diagnostics = [
        {field: diagnostic.get(field) for field in STABLE_DIAGNOSTIC_FIELDS if field in diagnostic}
        for diagnostic in diagnostics
        if isinstance(diagnostic, dict)
    ]
    return {
        "source": "tests/fixtures/local-executable-runtime-prototype.json",
        "sha256": digest(runtime_prototype_path),
        "validRuntimeExample": {
            "id": valid.get("id"),
            "adl": valid.get("adl"),
            "command": valid.get("command"),
            "status": valid.get("status"),
            "exitCode": valid.get("exitCode"),
            "completionStatus": (valid.get("completion") or {}).get("status"),
            "safetyGate": valid.get("safetyGate"),
        },
        "invalidDiagnosticSample": {
            "id": invalid.get("id"),
            "adl": invalid.get("adl"),
            "command": invalid.get("command"),
            "status": invalid.get("status"),
            "exitCode": invalid.get("exitCode"),
            "safetyGate": invalid.get("safetyGate"),
            "stableFields": list(STABLE_DIAGNOSTIC_FIELDS),
            "diagnostics": stable_diagnostics,
        },
        "boundaries": {
            "deterministicLocalFixturesOnly": True,
            "liveRuntimeActivation": False,
            "networkAccess": False,
            "credentialAccess": False,
            "providerApiAccess": False,
            "paymentAccess": False,
            "devnetAccess": False,
            "mainnetAccess": False,
            "deploymentPublished": False,
        },
    }


def result_by_id(bundle: dict[str, Any], result_id: str | None) -> dict[str, Any] | None:
    for result in bundle.get("results", []):
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


def evidence_hashes(acceptance: dict[str, Any]) -> list[dict[str, Any]]:
    hashes = [
        artifact("tests/fixtures/beta-release-handoff-scenarios.json", "Release handoff scenario inputs."),
        artifact("tests/fixtures/beta-activation-acceptance.json", "Pinned #262 activation acceptance bundle."),
        artifact("tests/fixtures/beta-activation-acceptance-scenarios.json", "Activation acceptance scenario inputs."),
        artifact("tests/fixtures/local-executable-runtime-prototype.json", "Pinned ADL v0.2 runtime and diagnostic evidence from #335."),
        artifact("examples/v0.2/memory-observability-agent.yaml", "Schema-valid ADL v0.2 runtime handoff example."),
        artifact("examples/invalid/adl-v0.2-x402-missing-authority.yaml", "Invalid ADL v0.2 diagnostic handoff sample."),
    ]
    for item in acceptance.get("evidenceHashes", []):
        if item not in hashes:
            hashes.append(item)
    return hashes


def operator_transcript(scenario: dict[str, Any], outcome: str | None, status: str) -> list[dict[str, Any]]:
    release_id = scenario.get("releaseId")
    adl_path = scenario.get("selectedAdlPath")
    dry_status = "pass" if status == "pass" else "fail"
    exit_code = 0 if status == "pass" else 3
    transcript = [
        {
            "step": 1,
            "command": f"operator:inspect-acceptance --release {release_id} --adl {adl_path} --dry-run",
            "event": "handoff.acceptance_inspected",
            "stdoutStatus": dry_status,
            "exitCode": exit_code,
            "liveRuntimeEnabled": False,
            "deploymentPublished": False,
        }
    ]
    if outcome == "accepted":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:prepare-release-handoff --release {release_id} --cue {scenario.get('acceptedActivationCue')} --dry-run",
                "event": "handoff.release_acceptance_archived",
                "stdoutStatus": dry_status,
                "exitCode": exit_code,
                "liveRuntimeEnabled": False,
                "deploymentPublished": False,
            }
        )
    elif outcome == "hold":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:prepare-release-hold --release {release_id} --dry-run",
                "event": "handoff.release_hold_archived",
                "stdoutStatus": dry_status,
                "exitCode": exit_code,
                "liveRuntimeEnabled": False,
                "deploymentPublished": False,
            }
        )
    elif outcome == "rollback-required":
        transcript.append(
            {
                "step": 2,
                "command": f"operator:prepare-release-rollback --release {release_id} --cue {scenario.get('rollbackCue')} --dry-run",
                "event": "handoff.rollback_required_archived",
                "stdoutStatus": dry_status,
                "exitCode": exit_code,
                "liveRuntimeEnabled": False,
                "deploymentPublished": False,
            }
        )
    transcript.append(
        {
            "step": 3,
            "command": f"operator:handoff-next-step --release {release_id} --dry-run",
            "event": "handoff.no_runtime_or_deployment_claim",
            "stdoutStatus": dry_status,
            "exitCode": exit_code,
            "liveRuntimeEnabled": False,
            "deploymentPublished": False,
        }
    )
    return transcript


def operator_checklist(status: str, outcome: str | None) -> list[dict[str, str]]:
    checks = [
        ("acceptance-current", "Current acceptance evidence matches pinned #262 bundle."),
        ("identity-bound", "Operator and reviewer identities are bound."),
        ("source-paths-bound", "Acceptance, rehearsal, preflight, decision, review, and runtime package paths are inherited."),
        ("hashes-bound", "Evidence hashes are present for the acceptance chain."),
        ("dry-run-only", "Every handoff command is explicitly dry-run only."),
        ("no-runtime-or-deployment", "The archive claims no runtime enablement, deployment, production, mainnet, or activation completion."),
        ("next-step-handoff", "Next-step handoff states review or preparation only before any separately approved runtime action."),
    ]
    if outcome == "accepted":
        checks.append(("accepted-activation-cue", "Accepted handoff archives include an accepted activation cue."))
    if outcome == "rollback-required":
        checks.append(("rollback-evidence", "Rollback-required archives include rollback cue and disable evidence."))
    return [{"id": check_id, "label": label, "status": "pass" if status == "pass" else "blocked"} for check_id, label in checks]


def expected_acceptance_outcome(outcome: str | None) -> str | None:
    return {"accepted": "accept", "hold": "hold", "rollback-required": "rollback-required"}.get(outcome)


def collect_findings(
    scenario: dict[str, Any],
    pinned_acceptance: dict[str, Any],
    current_acceptance: dict[str, Any],
    runtime_evidence: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    outcome = scenario.get("handoffOutcome")
    acceptance = result_by_id(pinned_acceptance, scenario.get("sourceAcceptanceResultId"))
    boundaries = scenario.get("boundaryStatus", {})
    rollback_evidence = scenario.get("rollbackDisableEvidence", {})

    require(pinned_acceptance.get("status") == "pass", "acceptanceBundle.status", "Pinned activation acceptance bundle must pass.")
    require(current_acceptance == pinned_acceptance, "acceptanceBundle.currentEvidence", "Current acceptance evidence must match the pinned #262 artifact.")
    require(runtime_evidence.get("validRuntimeExample", {}).get("status") == "pass", "adlV02RuntimeEvidence.validRuntimeExample.status", "ADL v0.2 runtime example must pass.")
    require(runtime_evidence.get("validRuntimeExample", {}).get("completionStatus") == "pass", "adlV02RuntimeEvidence.validRuntimeExample.completionStatus", "ADL v0.2 runtime completion must pass.")
    require(runtime_evidence.get("invalidDiagnosticSample", {}).get("status") == "pass", "adlV02RuntimeEvidence.invalidDiagnosticSample.status", "Invalid ADL v0.2 diagnostic sample must be captured successfully.")
    require(runtime_evidence.get("invalidDiagnosticSample", {}).get("exitCode") == 1, "adlV02RuntimeEvidence.invalidDiagnosticSample.exitCode", "Invalid ADL v0.2 diagnostic sample must fail validation without runtime activation.")
    diagnostics = runtime_evidence.get("invalidDiagnosticSample", {}).get("diagnostics", [])
    require(bool(diagnostics), "adlV02RuntimeEvidence.invalidDiagnosticSample.diagnostics", "Invalid ADL v0.2 diagnostic sample must include stable diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"adlV02RuntimeEvidence.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")
    require(scenario.get("sourceAcceptanceBundlePath") == "tests/fixtures/beta-activation-acceptance.json", "sourceAcceptanceBundlePath", "Source acceptance bundle path must match the pinned #262 artifact.")
    require(outcome in ALLOWED_HANDOFF_OUTCOMES, "handoffOutcome", "Handoff outcome must be accepted, hold, or rollback-required.")
    require(acceptance is not None, "sourceAcceptanceResultId", "Handoff must bind to a source acceptance result.")
    require(scenario.get("releaseId") == pinned_acceptance.get("releaseId"), "releaseId", "Handoff release id must match the acceptance bundle.")
    require(bool(scenario.get("selectedAdlPath")), "selectedAdlPath", "Selected ADL path is required.")
    require(bool(scenario.get("operatorIdentity")), "operatorIdentity", "Operator identity is required.")
    require(bool(scenario.get("handoffTimestamp")), "handoffTimestamp", "Handoff timestamp or fixture value is required.")
    require(bool(scenario.get("reviewerIdentity")) or bool(scenario.get("localApprovalFixture")), "reviewerIdentity", "Reviewer identity or local approval fixture is required.")

    if acceptance:
        require(acceptance.get("status") == "pass", "sourceAcceptance.status", "Source acceptance result must pass before handoff.")
        require(acceptance.get("acceptanceOutcome") == expected_acceptance_outcome(outcome), "handoffOutcome", "Handoff outcome must match the bound source acceptance outcome.")
        require(acceptance.get("releaseId") == scenario.get("releaseId"), "sourceAcceptance.releaseId", "Source acceptance release id must match handoff release.")
        require(acceptance.get("selectedAdlPath") == scenario.get("selectedAdlPath"), "selectedAdlPath", "Selected ADL path must match the source acceptance.")
        require(acceptance.get("sourceRehearsalPackagePath") == scenario.get("sourceRehearsalPackagePath"), "sourceRehearsalPackagePath", "Rehearsal package path must match source acceptance.")
        require(acceptance.get("sourcePreflightPackagePath") == scenario.get("sourcePreflightPackagePath"), "sourcePreflightPackagePath", "Preflight package path must match source acceptance.")
        require(acceptance.get("sourceDecisionPackagePath") == scenario.get("sourceDecisionPackagePath"), "sourceDecisionPackagePath", "Decision package path must match source acceptance.")
        require(acceptance.get("sourceReviewPackagePath") == scenario.get("sourceReviewPackagePath"), "sourceReviewPackagePath", "Review package path must match source acceptance.")
        require(acceptance.get("sourceRuntimePackagePath") == scenario.get("sourceRuntimePackagePath"), "sourceRuntimePackagePath", "Runtime package path must match source acceptance.")
        require(acceptance.get("operatorIdentity") == scenario.get("operatorIdentity"), "operatorIdentity", "Operator identity must match source acceptance.")
        require(acceptance.get("reviewerIdentity") == scenario.get("reviewerIdentity"), "reviewerIdentity", "Reviewer identity must match source acceptance.")
        require(acceptance.get("acceptedActivationCue") == scenario.get("acceptedActivationCue"), "acceptedActivationCue", "Accepted activation cue must match source acceptance.")
        require(acceptance.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackCue", "Rollback cue must match source acceptance.")

    if outcome == "accepted":
        require(bool(scenario.get("acceptedActivationCue")), "acceptedActivationCue", "Accepted handoff archives require an accepted activation cue.")
    if outcome == "rollback-required":
        require(bool(scenario.get("rollbackCue")), "rollbackCue", "Rollback-required handoff archives require a rollback cue.")
        require(isinstance(rollback_evidence, dict), "rollbackDisableEvidence", "Rollback/disable evidence is required.")
        if isinstance(rollback_evidence, dict):
            require(rollback_evidence.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackDisableEvidence.rollbackCue", "Rollback evidence must bind to the handoff rollback cue.")
            require(rollback_evidence.get("disableVerified") is True, "rollbackDisableEvidence.disableVerified", "Disable evidence must be verified.")
            require(rollback_evidence.get("dryRunOnly") is True, "rollbackDisableEvidence.dryRunOnly", "Rollback/disable evidence must be dry-run only.")
            require(rollback_evidence.get("liveRuntimeEnabled") is False, "rollbackDisableEvidence.liveRuntimeEnabled", "Rollback/disable evidence must not enable live runtime.")

    require(scenario.get("liveRuntimeRequested") is False, "liveRuntimeRequested", "Live runtime requests are out of scope for this handoff archive.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet requests are not part of this local handoff archive.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet requests require fresh Nissan approval.")
    require(scenario.get("productionEnabled") is False, "productionEnabled", "Production enablement is not allowed.")
    require(scenario.get("mainnetEnabled") is False, "mainnetEnabled", "Mainnet enablement is not allowed.")
    require(scenario.get("deploymentRequested") is False, "deploymentRequested", "Deployment requests are not allowed.")
    require(scenario.get("deploymentClaimed") is False, "deploymentClaimed", "Deployment completion claims are not allowed.")
    require(scenario.get("claimsActivationOccurred") is False, "claimsActivationOccurred", "Handoff archives must not claim activation occurred.")
    require(scenario.get("claimsLiveRuntimeEnablement") is False, "claimsLiveRuntimeEnablement", "Handoff archives must not claim live runtime enablement.")

    handoff = scenario.get("nextStepHandoff", "")
    require(isinstance(handoff, str) and bool(handoff.strip()), "nextStepHandoff", "Next-step handoff text is required.")
    lowered_handoff = handoff.lower() if isinstance(handoff, str) else ""
    require("no live runtime enablement" in lowered_handoff, "nextStepHandoff", "Next-step handoff must explicitly avoid live runtime enablement claims.")
    require("no deployment" in lowered_handoff, "nextStepHandoff", "Next-step handoff must explicitly avoid deployment claims.")
    require("no activation is claimed" in lowered_handoff, "nextStepHandoff", "Next-step handoff must explicitly avoid activation claims.")
    findings.extend(handoff_claim_findings(handoff))

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaryStatus.{key}", f"{key} must be false.")
    require(boundaries.get("releaseHandoffArchive") is True, "boundaryStatus.releaseHandoffArchive", "Release handoff archive boundary must be explicit.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaryStatus.deterministicLocalFixturesOnly", "Release handoff must be fixture-only.")

    for index, item in enumerate(evidence_hashes(acceptance or {})):
        require(item.get("exists") is True, f"evidenceHashes[{index}].exists", "Evidence hash entries must exist.")
        require(bool(item.get("sha256")), f"evidenceHashes[{index}].sha256", "Evidence hash entries must include sha256.")

    findings.extend(sensitive_findings(scenario, "scenario"))
    return findings


def handoff_status(outcome: str | None, status: str) -> str:
    if status == "fail":
        return "blocked-handoff"
    if outcome == "accepted":
        return "handoff-accepted"
    if outcome == "hold":
        return "handoff-held"
    if outcome == "rollback-required":
        return "handoff-rollback-required"
    return "blocked-handoff"


def build_result(
    scenario: dict[str, Any],
    pinned_acceptance: dict[str, Any],
    current_acceptance: dict[str, Any],
    runtime_evidence: dict[str, Any],
) -> dict[str, Any]:
    findings = collect_findings(scenario, pinned_acceptance, current_acceptance, runtime_evidence)
    acceptance = result_by_id(pinned_acceptance, scenario.get("sourceAcceptanceResultId")) or {}
    status = "pass" if not findings else "fail"
    outcome = scenario.get("handoffOutcome")
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "handoffOutcome": outcome,
        "handoffStatus": handoff_status(outcome, status),
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "releaseId": scenario.get("releaseId"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "sourceAcceptanceBundlePath": scenario.get("sourceAcceptanceBundlePath"),
        "sourceAcceptanceResultId": scenario.get("sourceAcceptanceResultId"),
        "sourceAcceptanceOutcome": acceptance.get("acceptanceOutcome"),
        "sourceRehearsalPackagePath": scenario.get("sourceRehearsalPackagePath"),
        "sourcePreflightPackagePath": scenario.get("sourcePreflightPackagePath"),
        "sourceDecisionPackagePath": scenario.get("sourceDecisionPackagePath"),
        "sourceReviewPackagePath": scenario.get("sourceReviewPackagePath"),
        "sourceRuntimePackagePath": scenario.get("sourceRuntimePackagePath"),
        "adlV02RuntimeEvidence": runtime_evidence,
        "operatorIdentity": scenario.get("operatorIdentity"),
        "reviewerIdentity": scenario.get("reviewerIdentity"),
        "localApprovalFixture": scenario.get("localApprovalFixture"),
        "handoffTimestamp": scenario.get("handoffTimestamp"),
        "sourceAcceptanceTimestamp": acceptance.get("acceptanceTimestamp"),
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
        "deploymentRequested": scenario.get("deploymentRequested"),
        "deploymentClaimed": scenario.get("deploymentClaimed"),
        "claimsActivationOccurred": scenario.get("claimsActivationOccurred"),
        "claimsLiveRuntimeEnablement": scenario.get("claimsLiveRuntimeEnablement"),
        "evidenceHashes": evidence_hashes(acceptance),
        "liveRuntimeEnablementClaim": "none",
        "deploymentClaim": "none",
        "activationClaim": "none",
    }


def build_report(doc: dict[str, Any], acceptance_bundle_path: Path = PINNED_ACCEPTANCE_BUNDLE) -> dict[str, Any]:
    pinned_acceptance = load_json(acceptance_bundle_path)
    current_acceptance = current_acceptance_bundle()
    runtime_evidence = adl_v02_runtime_evidence()
    defaults = doc.get("defaults", {})
    results = [
        build_result(merge_scenario(defaults, scenario), pinned_acceptance, current_acceptance, runtime_evidence)
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
        "mode": "beta-local-release-handoff-archive",
        "issue": 264,
        "refreshIssue": 337,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "releaseHandoffArchive": True,
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
            "deploymentPublished": False,
            "packagePublished": False,
        },
        "sourcePackageEvidence": {
            "acceptanceBundle": {
                "source": "tests/fixtures/beta-activation-acceptance.json",
                "status": pinned_acceptance.get("status"),
                "currentEvidenceMatchesPinned": current_acceptance == pinned_acceptance,
                "sha256": digest(acceptance_bundle_path),
            },
            "adlV02RuntimeEvidence": runtime_evidence,
        },
        "summary": {
            "acceptedArchives": sum(1 for result in results if result["handoffOutcome"] == "accepted"),
            "holdArchives": sum(1 for result in results if result["handoffOutcome"] == "hold"),
            "rollbackRequiredArchives": sum(1 for result in results if result["handoffOutcome"] == "rollback-required"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["kind"] == "negative" and result["status"] == "fail"),
        },
        "mainnetStatement": "This local release handoff archive does not enable production, deploy, activate runtime, or run mainnet; mainnet remains blocked until fresh Nissan approval.",
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        default=str(DEFAULT_SCENARIOS),
        help="Path to release handoff scenario JSON. Defaults to the pinned fixture input.",
    )
    parser.add_argument(
        "--acceptance-bundle",
        default=str(PINNED_ACCEPTANCE_BUNDLE),
        help="Path to the pinned #262 activation acceptance bundle.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    doc = load_json(Path(args.scenarios))
    report = build_report(doc, Path(args.acceptance_bundle))
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
