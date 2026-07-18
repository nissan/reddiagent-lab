#!/usr/bin/env python3
"""Build a deterministic local beta activation preflight gate package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-activation-preflight-scenarios.json"
PINNED_DECISION_PACKAGE = ROOT / "tests" / "fixtures" / "beta-operator-decision-package.json"
PINNED_REVIEW_PACKAGE = ROOT / "tests" / "fixtures" / "beta-review-ui.json"
PINNED_RUNTIME_PACKAGE = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_operator_decision_package  # noqa: E402
import beta_operator_dry_run_package  # noqa: E402
import beta_review_ui  # noqa: E402


ALLOWED_PREFLIGHT_OUTCOMES = {"approve", "hold", "rollback"}
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
SENSITIVE_KEYS = {
    "apiKey",
    "api_key",
    "authToken",
    "authorization",
    "credential",
    "credentials",
    "password",
    "paymentProof",
    "privateKey",
    "private_key",
    "rawPrompt",
    "rawSecret",
    "secret",
    "token",
    "walletHandle",
}
SENSITIVE_KEY_NORMALIZED = {
    "apikey",
    "authorization",
    "authtoken",
    "credential",
    "credentials",
    "password",
    "paymentproof",
    "privatekey",
    "rawprompt",
    "rawsecret",
    "secret",
    "token",
    "wallethandle",
}
SENSITIVE_VALUE_MARKERS = (
    "begin private key",
    "bearer ",
    "sk-",
    "ghp_",
    "xoxb-",
    "authorization:",
    "api_key=",
    "password=",
    "private_key=",
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
                findings.append(finding(child_path, "Credential-like or private payload key is not allowed."))
            findings.extend(sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like or private payload value is not allowed."))
    return findings


def current_runtime_package() -> dict[str, Any]:
    return beta_operator_dry_run_package.build_report(
        load_json(beta_operator_dry_run_package.DEFAULT_SCENARIOS)
    )


def current_review_package() -> dict[str, Any]:
    runtime_package = load_json(PINNED_RUNTIME_PACKAGE)
    review = beta_review_ui.build_review(runtime_package, current_runtime_package(), PINNED_RUNTIME_PACKAGE)
    review.pop("html", None)
    return review


def current_decision_package() -> dict[str, Any]:
    return beta_operator_decision_package.build_report(
        load_json(beta_operator_decision_package.DEFAULT_SCENARIOS)
    )


def result_by_id(package: dict[str, Any], result_id: str | None) -> dict[str, Any] | None:
    for result in package.get("results", []):
        if result.get("id") == result_id:
            return result
    return None


def evidence_hashes(decision: dict[str, Any]) -> list[dict[str, Any]]:
    hashes = [
        artifact("tests/fixtures/beta-activation-preflight-scenarios.json", "Activation preflight scenario inputs."),
        artifact("tests/fixtures/beta-operator-decision-package.json", "Pinned #256 operator decision package."),
        artifact("tests/fixtures/beta-operator-decision-package-scenarios.json", "Operator decision package scenario inputs."),
        artifact("tests/fixtures/beta-review-ui.json", "Pinned #246 review UI/package artifact."),
        artifact("tests/fixtures/beta-operator-dry-run-package.json", "Pinned #240 runtime package artifact."),
    ]
    for item in decision.get("evidenceHashes", []):
        if item not in hashes:
            hashes.append(item)
    return hashes


def collect_findings(
    scenario: dict[str, Any],
    pinned_decision: dict[str, Any],
    current_decision: dict[str, Any],
    pinned_review: dict[str, Any],
    current_review: dict[str, Any],
    pinned_runtime: dict[str, Any],
    current_runtime: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    outcome = scenario.get("preflightOutcome")
    boundaries = scenario.get("boundaryStatus", {})
    decision = result_by_id(pinned_decision, scenario.get("decisionPackageResultId"))

    require(pinned_decision.get("status") == "pass", "decisionPackage.status", "Pinned operator decision package must pass.")
    require(current_decision == pinned_decision, "decisionPackage.currentEvidence", "Current decision package evidence must match the pinned #256 artifact.")
    require(pinned_review.get("status") == "pass", "reviewPackage.status", "Pinned review package evidence must pass.")
    require(current_review == pinned_review, "reviewPackage.currentEvidence", "Current review package evidence must match the pinned #246 artifact.")
    require(pinned_runtime.get("status") == "pass", "runtimePackage.status", "Pinned runtime package evidence must pass.")
    require(current_runtime == pinned_runtime, "runtimePackage.currentEvidence", "Current runtime package evidence must match the pinned #240 artifact.")

    require(scenario.get("sourceDecisionPackagePath") == "tests/fixtures/beta-operator-decision-package.json", "sourceDecisionPackagePath", "Source decision package path must match the pinned #256 artifact.")
    require(scenario.get("sourceReviewPackagePath") == pinned_decision.get("reviewPackageEvidence", {}).get("source"), "sourceReviewPackagePath", "Source review package path must match the #256 decision evidence.")
    require(scenario.get("sourceRuntimePackagePath") == pinned_decision.get("reviewPackageEvidence", {}).get("sourcePackagePath"), "sourceRuntimePackagePath", "Source runtime package path must match the #256 decision evidence.")
    require(scenario.get("releaseId") == pinned_decision.get("releaseId"), "releaseId", "Preflight release id must match the decision package.")
    require(scenario.get("selectedAdlPath") == pinned_decision.get("reviewPackageEvidence", {}).get("selectedAdlPath"), "selectedAdlPath", "Preflight ADL path must match the decision package.")
    require(bool(scenario.get("operatorIdentity")), "operatorIdentity", "Operator identity is required.")
    require(bool(scenario.get("sourceDecisionTimestamp")), "sourceDecisionTimestamp", "Source decision timestamp or fixture value is required.")
    require(bool(scenario.get("preflightTimestamp")), "preflightTimestamp", "Preflight timestamp or fixture value is required.")
    require(outcome in ALLOWED_PREFLIGHT_OUTCOMES, "preflightOutcome", "Preflight outcome must be approve, hold, or rollback.")
    require(decision is not None, "decisionPackageResultId", "Preflight must bind to a source decision package result.")

    if decision:
        require(decision.get("status") == "pass", "decisionPackageResult.status", "Source decision result must pass before activation preflight.")
        require(decision.get("decision") == outcome, "preflightOutcome", "Preflight outcome must match the bound source decision.")
        require(decision.get("releaseId") == scenario.get("releaseId"), "decisionPackageResult.releaseId", "Source decision release id must match the preflight release.")
        require(decision.get("selectedAdlPath") == scenario.get("selectedAdlPath"), "decisionPackageResult.selectedAdlPath", "Source decision ADL path must match the preflight ADL path.")
        require(decision.get("sourcePackagePath") == scenario.get("sourceRuntimePackagePath"), "decisionPackageResult.sourcePackagePath", "Source decision runtime package path must match the preflight runtime package.")
        require(decision.get("operatorIdentity") == scenario.get("operatorIdentity"), "operatorIdentity", "Operator identity must match the source decision.")
        require(decision.get("decisionTimestamp") == scenario.get("sourceDecisionTimestamp"), "sourceDecisionTimestamp", "Source decision timestamp must match the decision package result.")
        require(decision.get("rollbackCue") == scenario.get("rollbackCue"), "rollbackCue", "Rollback cue must match the source decision.")

    if outcome == "rollback":
        require(bool(scenario.get("rollbackCue")), "rollbackCue", "Rollback preflights require an explicit rollback cue.")
    if outcome in {"approve", "hold"}:
        require("rollbackCue" in scenario, "rollbackCue", "Rollback cue field must be present for audit binding.")

    require(scenario.get("liveRuntimeRequested") is False, "liveRuntimeRequested", "Live runtime requests are out of scope for this preflight.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet requests are not part of this local activation preflight.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet requests require fresh Nissan approval.")
    require(scenario.get("productionEnabled") is False, "productionEnabled", "Production enablement is not allowed.")
    require(scenario.get("mainnetEnabled") is False, "mainnetEnabled", "Mainnet enablement is not allowed.")

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaryStatus.{key}", f"{key} must be false.")
    require(boundaries.get("activationPreflightPackage") is True, "boundaryStatus.activationPreflightPackage", "Activation preflight boundary must be explicit.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaryStatus.deterministicLocalFixturesOnly", "Activation preflight must be fixture-only.")

    for index, item in enumerate(evidence_hashes(decision or {})):
        require(item.get("exists") is True, f"evidenceHashes[{index}].exists", "Evidence hash entries must exist.")
        require(bool(item.get("sha256")), f"evidenceHashes[{index}].sha256", "Evidence hash entries must include sha256.")

    findings.extend(sensitive_findings(scenario, "scenario"))
    return findings


def activation_status(outcome: str | None, status: str) -> str:
    if status == "fail":
        return "blocked-preflight"
    if outcome == "approve":
        return "approve-preflight"
    if outcome == "hold":
        return "hold-preflight"
    if outcome == "rollback":
        return "rollback-preflight"
    return "blocked-preflight"


def build_result(
    scenario: dict[str, Any],
    pinned_decision: dict[str, Any],
    current_decision: dict[str, Any],
    pinned_review: dict[str, Any],
    current_review: dict[str, Any],
    pinned_runtime: dict[str, Any],
    current_runtime: dict[str, Any],
) -> dict[str, Any]:
    findings = collect_findings(
        scenario,
        pinned_decision,
        current_decision,
        pinned_review,
        current_review,
        pinned_runtime,
        current_runtime,
    )
    decision = result_by_id(pinned_decision, scenario.get("decisionPackageResultId")) or {}
    status = "pass" if not findings else "fail"
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "preflightOutcome": scenario.get("preflightOutcome"),
        "activationStatus": activation_status(scenario.get("preflightOutcome"), status),
        "status": status,
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "releaseId": scenario.get("releaseId"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "sourceDecisionPackagePath": scenario.get("sourceDecisionPackagePath"),
        "sourceReviewPackagePath": scenario.get("sourceReviewPackagePath"),
        "sourceRuntimePackagePath": scenario.get("sourceRuntimePackagePath"),
        "decisionPackageResultId": scenario.get("decisionPackageResultId"),
        "operatorIdentity": scenario.get("operatorIdentity"),
        "sourceDecisionTimestamp": scenario.get("sourceDecisionTimestamp"),
        "preflightTimestamp": scenario.get("preflightTimestamp"),
        "rollbackCue": scenario.get("rollbackCue"),
        "boundaryStatus": scenario.get("boundaryStatus", {}),
        "liveRuntimeRequested": scenario.get("liveRuntimeRequested"),
        "devnetRequested": scenario.get("devnetRequested"),
        "mainnetRequested": scenario.get("mainnetRequested"),
        "productionEnabled": scenario.get("productionEnabled"),
        "mainnetEnabled": scenario.get("mainnetEnabled"),
        "sourceDecision": {
            "status": decision.get("status"),
            "decision": decision.get("decision"),
            "operatorIdentity": decision.get("operatorIdentity"),
            "decisionTimestamp": decision.get("decisionTimestamp"),
        },
        "evidenceHashes": evidence_hashes(decision),
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    pinned_decision = load_json(PINNED_DECISION_PACKAGE)
    current_decision = current_decision_package()
    pinned_review = load_json(PINNED_REVIEW_PACKAGE)
    current_review = current_review_package()
    pinned_runtime = load_json(PINNED_RUNTIME_PACKAGE)
    current_runtime = current_runtime_package()
    results = [
        build_result(
            scenario,
            pinned_decision,
            current_decision,
            pinned_review,
            current_review,
            pinned_runtime,
            current_runtime,
        )
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
        "mode": "beta-local-activation-preflight-gate",
        "issue": 258,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "activationPreflightPackage": True,
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
            "decisionPackage": {
                "source": "tests/fixtures/beta-operator-decision-package.json",
                "status": pinned_decision.get("status"),
                "currentEvidenceMatchesPinned": current_decision == pinned_decision,
            },
            "reviewPackage": {
                "source": "tests/fixtures/beta-review-ui.json",
                "status": pinned_review.get("status"),
                "currentEvidenceMatchesPinned": current_review == pinned_review,
            },
            "runtimePackage": {
                "source": "tests/fixtures/beta-operator-dry-run-package.json",
                "status": pinned_runtime.get("status"),
                "currentEvidenceMatchesPinned": current_runtime == pinned_runtime,
            },
        },
        "summary": {
            "approvePreflights": sum(1 for result in results if result["preflightOutcome"] == "approve"),
            "holdPreflights": sum(1 for result in results if result["preflightOutcome"] == "hold"),
            "rollbackPreflights": sum(1 for result in results if result["preflightOutcome"] == "rollback"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["status"] == "fail"),
        },
        "mainnetStatement": "This local activation preflight does not enable production or mainnet; mainnet remains blocked until fresh Nissan approval.",
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
