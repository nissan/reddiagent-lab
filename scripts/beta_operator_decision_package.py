#!/usr/bin/env python3
"""Build a deterministic local beta operator decision package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-decision-package-scenarios.json"
PINNED_REVIEW = ROOT / "tests" / "fixtures" / "beta-review-ui.json"
PINNED_PACKAGE = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_review_ui  # noqa: E402


ALLOWED_DECISIONS = {"approve", "hold", "rollback"}
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
    "authorization",
    "credential",
    "credentials",
    "password",
    "paymentProof",
    "privateKey",
    "rawPrompt",
    "rawSecret",
    "secret",
    "token",
    "walletHandle",
}
SENSITIVE_VALUE_MARKERS = (
    "begin private key",
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
            if key in SENSITIVE_KEYS:
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


def current_review_package() -> dict[str, Any]:
    package = load_json(PINNED_PACKAGE)
    current_package = beta_review_ui.beta_operator_dry_run_package.build_report(
        load_json(beta_review_ui.DEFAULT_SCENARIOS)
    )
    review = beta_review_ui.build_review(package, current_package, PINNED_PACKAGE)
    review.pop("html", None)
    return review


def evidence_hashes(review: dict[str, Any]) -> list[dict[str, Any]]:
    hashes = [
        artifact("tests/fixtures/beta-review-ui.json", "Pinned #246 beta review UI/package artifact."),
        artifact("tests/fixtures/beta-operator-dry-run-package.json", "Source operator dry-run package artifact."),
        artifact("tests/fixtures/beta-operator-decision-package-scenarios.json", "Operator decision package scenario inputs."),
    ]
    for panel in review.get("reviewPanels", []):
        if panel.get("id") == "evidence-index":
            hashes.extend(panel.get("rows", []))
    return hashes


def collect_findings(scenario: dict[str, Any], pinned_review: dict[str, Any], current_review: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    decision = scenario.get("decision")
    boundaries = scenario.get("boundaryStatus", {})

    require(pinned_review.get("status") == "pass", "review.status", "Pinned review package evidence must pass.")
    require(current_review == pinned_review, "review.currentEvidence", "Current review package evidence must match the pinned #246 artifact.")
    require(scenario.get("sourcePackagePath") == pinned_review.get("sourcePackage"), "sourcePackagePath", "Source package path must match the reviewed package.")
    require(scenario.get("releaseId") == pinned_review.get("releaseId"), "releaseId", "Decision release id must match the reviewed package.")
    require(scenario.get("selectedAdlPath") == pinned_review.get("selectedAdlPath"), "selectedAdlPath", "Decision ADL path must match the reviewed package.")
    require(bool(scenario.get("operatorIdentity")), "operatorIdentity", "Operator identity is required.")
    require(bool(scenario.get("decisionTimestamp")), "decisionTimestamp", "Decision timestamp or fixture value is required.")
    require(decision in ALLOWED_DECISIONS, "decision", "Decision must be approve, hold, or rollback.")

    if decision == "rollback":
        require(bool(scenario.get("rollbackCue")), "rollbackCue", "Rollback decisions require an explicit rollback cue.")
    if decision in {"approve", "hold"}:
        require("rollbackCue" in scenario, "rollbackCue", "Rollback cue field must be present for audit binding.")

    require(scenario.get("liveRuntimeRequested") is False, "liveRuntimeRequested", "Live runtime requests are out of scope.")
    require(scenario.get("devnetRequested") is False, "devnetRequested", "Devnet requests are not part of this local decision package.")
    require(scenario.get("mainnetRequested") is False, "mainnetRequested", "Mainnet requests require fresh Nissan approval.")
    require(scenario.get("productionEnabled") is False, "productionEnabled", "Production enablement is not allowed.")
    require(scenario.get("mainnetEnabled") is False, "mainnetEnabled", "Mainnet enablement is not allowed.")

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaryStatus.{key}", f"{key} must be false.")
    require(boundaries.get("operatorDecisionPackage") is True, "boundaryStatus.operatorDecisionPackage", "Decision package boundary must be explicit.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaryStatus.deterministicLocalFixturesOnly", "Decision package must be fixture-only.")

    for index, item in enumerate(evidence_hashes(pinned_review)):
        require(item.get("exists") is True, f"evidenceHashes[{index}].exists", "Evidence hash entries must exist.")
        require(bool(item.get("sha256")), f"evidenceHashes[{index}].sha256", "Evidence hash entries must include sha256.")

    findings.extend(sensitive_findings(scenario, "scenario"))
    return findings


def build_result(scenario: dict[str, Any], pinned_review: dict[str, Any], current_review: dict[str, Any]) -> dict[str, Any]:
    findings = collect_findings(scenario, pinned_review, current_review)
    return {
        "id": scenario["id"],
        "kind": scenario["kind"],
        "decision": scenario.get("decision"),
        "status": "pass" if not findings else "fail",
        "expectedStatus": scenario["expectedStatus"],
        "findings": findings,
        "releaseId": scenario.get("releaseId"),
        "selectedAdlPath": scenario.get("selectedAdlPath"),
        "sourcePackagePath": scenario.get("sourcePackagePath"),
        "operatorIdentity": scenario.get("operatorIdentity"),
        "decisionTimestamp": scenario.get("decisionTimestamp"),
        "rollbackCue": scenario.get("rollbackCue"),
        "boundaryStatus": scenario.get("boundaryStatus", {}),
        "liveRuntimeRequested": scenario.get("liveRuntimeRequested"),
        "devnetRequested": scenario.get("devnetRequested"),
        "mainnetRequested": scenario.get("mainnetRequested"),
        "productionEnabled": scenario.get("productionEnabled"),
        "mainnetEnabled": scenario.get("mainnetEnabled"),
        "evidenceHashes": evidence_hashes(pinned_review),
    }


def build_report(doc: dict[str, Any]) -> dict[str, Any]:
    pinned_review = load_json(PINNED_REVIEW)
    current_review = current_review_package()
    results = [build_result(scenario, pinned_review, current_review) for scenario in doc.get("scenarios", [])]
    mismatches = [
        finding(
            f"results[{index}].status",
            f"{result['id']} produced {result['status']} but expected {result['expectedStatus']}",
        )
        for index, result in enumerate(results)
        if result["status"] != result["expectedStatus"]
    ]
    return {
        "mode": "beta-local-operator-decision-package",
        "issue": 256,
        "parentEpic": 220,
        "releaseId": doc.get("releaseId"),
        "status": "pass" if not mismatches else "fail",
        "findings": mismatches,
        "boundaries": {
            "operatorDecisionPackage": True,
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
        "reviewPackageEvidence": {
            "source": "tests/fixtures/beta-review-ui.json",
            "status": pinned_review.get("status"),
            "currentEvidenceMatchesPinned": current_review == pinned_review,
            "sourcePackagePath": pinned_review.get("sourcePackage"),
            "releaseId": pinned_review.get("releaseId"),
            "selectedAdlPath": pinned_review.get("selectedAdlPath"),
        },
        "summary": {
            "approveDecisions": sum(1 for result in results if result["decision"] == "approve"),
            "holdDecisions": sum(1 for result in results if result["decision"] == "hold"),
            "rollbackDecisions": sum(1 for result in results if result["decision"] == "rollback"),
            "positiveScenarios": sum(1 for result in results if result["kind"] == "positive"),
            "negativeScenarios": sum(1 for result in results if result["kind"] == "negative"),
            "failClosedScenarios": sum(1 for result in results if result["status"] == "fail"),
        },
        "mainnetStatement": "Production and mainnet enablement remain not approved; this package records only local beta operator decisions.",
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
