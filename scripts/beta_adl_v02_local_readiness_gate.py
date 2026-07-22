#!/usr/bin/env python3
"""Build deterministic ADL v0.2 local beta readiness gate evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
import beta_reviewer_walkthrough_smoke  # noqa: E402


REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_READINESS_ID = "reddiagent-beta-0-adl-v02-local-readiness-gate"
REQUIRED_HANDOFF_ISSUE = 337
REQUIRED_WALKTHROUGH_ISSUE = 339
CURRENT_ISSUE = 341
PARENT_EPIC = 220
REQUIRED_VALID_ADL = beta_reviewer_walkthrough_smoke.REQUIRED_VALID_ADL
REQUIRED_INVALID_ADL = beta_reviewer_walkthrough_smoke.REQUIRED_INVALID_ADL
STABLE_DIAGNOSTIC_FIELDS = beta_reviewer_walkthrough_smoke.STABLE_DIAGNOSTIC_FIELDS
REQUIRED_ARTIFACTS = {
    "releaseHandoff": "tests/fixtures/beta-release-handoff.json",
    "reviewerWalkthroughSmoke": "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
    "runtimePrototype": "tests/fixtures/local-executable-runtime-prototype.json",
    "validRuntimeAdl": REQUIRED_VALID_ADL,
    "invalidDiagnosticAdl": REQUIRED_INVALID_ADL,
}
REQUIRED_BOUNDARY_FALSE = beta_reviewer_walkthrough_smoke.REQUIRED_BOUNDARY_FALSE + (
    "productionGatewayMutation",
    "fullHistoricalBetaChainReplay",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def artifact_inventory(paths: dict[str, str] = REQUIRED_ARTIFACTS) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for key, path_text in sorted(paths.items()):
        path = ROOT / path_text
        exists = path.exists() and path.is_file()
        inventory.append(
            {
                "key": key,
                "path": path_text,
                "exists": exists,
                "sha256": digest(path) if exists else None,
                "sizeBytes": path.stat().st_size if exists else None,
            }
        )
    return inventory


def runtime_scenario(runtime: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in runtime.get("scenarios", []):
        if scenario.get("id") == scenario_id:
            return scenario
    return {}


def stable_diagnostics(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    invalid = runtime_scenario(runtime, "invalid-adl-v02-payment-diagnostics")
    diagnostics = invalid.get("validationDiagnostics", [])
    return [
        {field: diagnostic.get(field) for field in STABLE_DIAGNOSTIC_FIELDS if field in diagnostic}
        for diagnostic in diagnostics
        if isinstance(diagnostic, dict)
    ]


def handoff_runtime_evidence(handoff: dict[str, Any]) -> dict[str, Any]:
    direct = handoff.get("sourcePackageEvidence", {}).get("adlV02RuntimeEvidence")
    if isinstance(direct, dict):
        return direct
    for result in handoff.get("results", []):
        evidence = result.get("adlV02RuntimeEvidence") if isinstance(result, dict) else None
        if isinstance(evidence, dict):
            return evidence
    return {}


def collect_findings(
    handoff: dict[str, Any],
    walkthrough: dict[str, Any],
    runtime: dict[str, Any],
    inventory: list[dict[str, Any]],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    for item in inventory:
        require(item["exists"] is True, f"artifactInventory.{item['key']}.exists", f"`{item['path']}` must exist.")
        require(bool(item["sha256"]), f"artifactInventory.{item['key']}.sha256", f"`{item['path']}` must have a sha256 pin.")

    require(handoff.get("mode") == "beta-local-release-handoff-archive", "releaseHandoff.mode", "Readiness must consume the #337 handoff artifact.")
    require(handoff.get("refreshIssue") == REQUIRED_HANDOFF_ISSUE, "releaseHandoff.refreshIssue", "Release handoff must be refreshed by #337.")
    require(handoff.get("status") == "pass", "releaseHandoff.status", "Release handoff must be passing.")

    require(walkthrough.get("mode") == "beta-local-reviewer-walkthrough-smoke", "reviewerWalkthroughSmoke.mode", "Readiness must consume the #339 walkthrough smoke artifact.")
    require(walkthrough.get("issue") == REQUIRED_WALKTHROUGH_ISSUE, "reviewerWalkthroughSmoke.issue", "Reviewer walkthrough smoke must come from #339.")
    require(REQUIRED_HANDOFF_ISSUE in walkthrough.get("follows", []), "reviewerWalkthroughSmoke.follows", "Reviewer walkthrough smoke must follow #337.")
    require(walkthrough.get("status") == "pass", "reviewerWalkthroughSmoke.status", "Reviewer walkthrough smoke must be passing.")
    require(walkthrough.get("walkthroughId") == beta_reviewer_walkthrough_smoke.REQUIRED_WALKTHROUGH_ID, "reviewerWalkthroughSmoke.walkthroughId", "Reviewer walkthrough smoke ID must stay stable.")

    valid = runtime_scenario(runtime, "adl-v02-memory-observability-dry-run")
    invalid = runtime_scenario(runtime, "invalid-adl-v02-payment-diagnostics")
    diagnostics = stable_diagnostics(runtime)
    handoff_runtime = handoff_runtime_evidence(handoff)
    walkthrough_review = walkthrough.get("adlV02RuntimeReview", {})
    walkthrough_invalid = walkthrough_review.get("invalidDiagnosticSample", {}) if isinstance(walkthrough_review, dict) else {}
    walkthrough_valid = walkthrough_review.get("validRuntimeExample", {}) if isinstance(walkthrough_review, dict) else {}

    require(valid.get("adl") == REQUIRED_VALID_ADL, "runtimePrototype.validRuntimeExample.adl", "Valid ADL v0.2 runtime example path must match the current beta baseline.")
    require(valid.get("status") == "pass", "runtimePrototype.validRuntimeExample.status", "Valid ADL v0.2 runtime example must pass.")
    require(valid.get("exitCode") == 0, "runtimePrototype.validRuntimeExample.exitCode", "Valid ADL v0.2 runtime example must exit zero.")
    require((valid.get("completion") or {}).get("status") == "pass", "runtimePrototype.validRuntimeExample.completion.status", "Valid ADL v0.2 completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "runtimePrototype.invalidDiagnosticSample.adl", "Invalid ADL v0.2 diagnostic sample path must match the current beta baseline.")
    require(invalid.get("exitCode") == 1, "runtimePrototype.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail validation.")
    require(bool(diagnostics), "runtimePrototype.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"runtimePrototype.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    require(handoff_runtime.get("validRuntimeExample", {}).get("adl") == REQUIRED_VALID_ADL, "releaseHandoff.adlV02RuntimeEvidence.validRuntimeExample.adl", "Release handoff must expose the valid ADL v0.2 example.")
    require(handoff_runtime.get("invalidDiagnosticSample", {}).get("adl") == REQUIRED_INVALID_ADL, "releaseHandoff.adlV02RuntimeEvidence.invalidDiagnosticSample.adl", "Release handoff must expose the invalid ADL v0.2 diagnostic sample.")
    require(handoff_runtime.get("invalidDiagnosticSample", {}).get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "releaseHandoff.adlV02RuntimeEvidence.invalidDiagnosticSample.stableFields", "Release handoff must preserve stable diagnostic fields.")
    require(walkthrough_valid.get("adl") == REQUIRED_VALID_ADL, "reviewerWalkthroughSmoke.adlV02RuntimeReview.validRuntimeExample.adl", "Reviewer walkthrough must expose the valid ADL v0.2 example.")
    require(walkthrough_invalid.get("adl") == REQUIRED_INVALID_ADL, "reviewerWalkthroughSmoke.adlV02RuntimeReview.invalidDiagnosticSample.adl", "Reviewer walkthrough must expose the invalid ADL v0.2 sample.")
    require(walkthrough_invalid.get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS), "reviewerWalkthroughSmoke.adlV02RuntimeReview.invalidDiagnosticSample.stableFields", "Reviewer walkthrough must preserve stable diagnostic fields.")

    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"{key} must remain false.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaries.deterministicLocalFixturesOnly", "Readiness gate must be deterministic fixture review.")
    require(boundaries.get("offlinePassFailGate") is True, "boundaries.offlinePassFailGate", "Readiness gate must be an offline pass/fail gate.")
    require(boundaries.get("consumesHandoffAndWalkthroughOnly") is True, "boundaries.consumesHandoffAndWalkthroughOnly", "Readiness gate must consume #337/#339 evidence without replaying the full chain.")
    return findings


def build_report(commit: str | None = None) -> dict[str, Any]:
    docs = {
        key: load_json(ROOT / path)
        for key, path in REQUIRED_ARTIFACTS.items()
        if path.endswith(".json")
    }
    inventory = artifact_inventory()
    boundaries = {
        "offlinePassFailGate": True,
        "consumesHandoffAndWalkthroughOnly": True,
        "deterministicLocalFixturesOnly": True,
        "fullHistoricalBetaChainReplay": False,
        "liveRuntimeActivation": False,
        "networkAccess": False,
        "credentialAccess": False,
        "providerApiAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "walletAccess": False,
        "facilitatorAccess": False,
        "settlementAccess": False,
        "devnetAccess": False,
        "mainnetAccess": False,
        "deploymentPublished": False,
        "packagePublished": False,
        "archivePublished": False,
        "publicPublished": False,
        "externalSpend": False,
        "productionGatewayMutation": False,
    }
    findings = collect_findings(
        docs["releaseHandoff"],
        docs["reviewerWalkthroughSmoke"],
        docs["runtimePrototype"],
        inventory,
        boundaries,
    )
    runtime = docs["runtimePrototype"]
    valid = runtime_scenario(runtime, "adl-v02-memory-observability-dry-run")
    invalid = runtime_scenario(runtime, "invalid-adl-v02-payment-diagnostics")
    diagnostics = stable_diagnostics(runtime)
    return {
        "mode": "adl-v02-local-beta-readiness-gate",
        "issue": CURRENT_ISSUE,
        "parentEpic": PARENT_EPIC,
        "follows": [REQUIRED_HANDOFF_ISSUE, REQUIRED_WALKTHROUGH_ISSUE],
        "readinessId": REQUIRED_READINESS_ID,
        "releaseId": REQUIRED_RELEASE_ID,
        "status": "pass" if not findings else "fail",
        "baselineDecision": "ready" if not findings else "hold",
        "sourceCommit": commit or "fixture://adl-v02-local-beta-readiness-gate",
        "findings": findings,
        "passCriteria": [
            "#337 release handoff fixture is present, passing, and refreshed for ADL v0.2 runtime evidence.",
            "#339 reviewer walkthrough smoke fixture is present, passing, and linked to #337.",
            "Valid ADL v0.2 runtime example is pinned and passing.",
            "Invalid ADL v0.2 diagnostic sample is pinned and fail-closed with stable diagnostic fields.",
            "Artifact inventory includes inspectable paths, sizes, and sha256 hashes for offline review.",
            "Guardrail boundaries stay local/free/deterministic with no live activation, network, provider, payment, deployment, publishing, devnet, or mainnet action.",
        ],
        "artifactInventory": inventory,
        "baselineArtifacts": {
            "releaseHandoff": "tests/fixtures/beta-release-handoff.json",
            "reviewerWalkthroughSmoke": "tests/fixtures/beta-reviewer-walkthrough-smoke.json",
            "runtimePrototype": "tests/fixtures/local-executable-runtime-prototype.json",
            "validRuntimeAdl": REQUIRED_VALID_ADL,
            "invalidDiagnosticAdl": REQUIRED_INVALID_ADL,
        },
        "adlV02RuntimeBaseline": {
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
                "diagnostics": diagnostics,
            },
        },
        "excludedSteps": [
            "full historical beta chain replay",
            "live runtime activation",
            "hosted deployment or fetch",
            "Docker, Surfpool, or Coolify mutation",
            "credential lookup or storage",
            "provider/model/API product call",
            "live MCP invocation",
            "wallet/payment/facilitator/settlement action",
            "devnet or mainnet run",
            "package or archive publishing",
            "production gateway mutation",
        ],
        "boundaries": boundaries,
        "mainnetStatement": "This readiness gate is local/free/deterministic fixture review only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated readiness gate report JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    payload = dump_json(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
