#!/usr/bin/env python3
"""Build deterministic local beta reviewer walkthrough smoke evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_RELEASE_ID = "reddiagent-beta-0"
REQUIRED_WALKTHROUGH_ID = "reddiagent-beta-0-adl-v02-local-reviewer-walkthrough-smoke"
REQUIRED_VALID_ADL = "examples/v0.2/memory-observability-agent.yaml"
REQUIRED_INVALID_ADL = "examples/invalid/adl-v0.2-x402-missing-authority.yaml"
STABLE_DIAGNOSTIC_FIELDS = ("code", "severity", "category", "path", "line", "column")
REQUIRED_ARTIFACTS = {
    "releaseHandoff": "tests/fixtures/beta-release-handoff.json",
    "onboardingQuickstart": "tests/fixtures/beta-onboarding-quickstart.json",
    "reviewerChecklist": "tests/fixtures/beta-reviewer-acceptance-checklist.json",
    "releaseVerification": "tests/fixtures/beta-release-verification.json",
    "reviewUi": "tests/fixtures/beta-review-ui.json",
    "runtimePrototype": "tests/fixtures/local-executable-runtime-prototype.json",
    "validRuntimeAdl": REQUIRED_VALID_ADL,
    "invalidDiagnosticAdl": REQUIRED_INVALID_ADL,
}
UNSAFE_COMMAND_MARKERS = {
    "coolify",
    "devnet",
    "here-publish",
    "mainnet",
    "solana-test-validator",
}
UNSAFE_DOCKER_SUBCOMMANDS = {"compose", "container", "pull", "run", "start"}
UNSAFE_PACKAGE_PUBLISH_COMMANDS = {
    ("gh", "release", "upload"),
    ("npm", "publish"),
    ("pnpm", "publish"),
    ("yarn", "publish"),
    ("vercel", "deploy"),
    ("kubectl", "apply"),
    ("openclaw", "gateway"),
}
HOSTED_FETCH_COMMANDS = {"curl", "wget"}
REQUIRED_BOUNDARY_FALSE = (
    "liveRuntimeActivation",
    "networkAccess",
    "credentialAccess",
    "providerApiAccess",
    "mcpInvocation",
    "paymentAccess",
    "walletAccess",
    "facilitatorAccess",
    "settlementAccess",
    "devnetAccess",
    "mainnetAccess",
    "deploymentPublished",
    "packagePublished",
    "archivePublished",
    "publicPublished",
    "externalSpend",
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


def source_commit() -> str:
    return "fixture://beta-reviewer-walkthrough-smoke"


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


def command_findings(commands: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for index, command in enumerate(commands):
        lowered = command.lower()
        for marker in UNSAFE_COMMAND_MARKERS:
            if marker in lowered:
                findings.append(finding(f"reviewerCommands[{index}]", f"Reviewer walkthrough command must not include `{marker}`."))
        try:
            tokens = [token.lower() for token in shlex.split(command)]
        except ValueError:
            tokens = lowered.split()
        if not tokens:
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer walkthrough command must be parseable."))
            continue
        if tokens[0] == "docker" and any(token in UNSAFE_DOCKER_SUBCOMMANDS for token in tokens[1:]):
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer walkthrough must not pull, start, run, or compose Docker containers."))
        if tokens[0] == "docker-compose" and "up" in tokens[1:]:
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer walkthrough must not start Docker Compose services."))
        if tokens[0] in HOSTED_FETCH_COMMANDS and any(token.startswith(("http://", "https://")) for token in tokens[1:]):
            findings.append(finding(f"reviewerCommands[{index}]", "Reviewer walkthrough must not fetch hosted content."))
        for unsafe in UNSAFE_PACKAGE_PUBLISH_COMMANDS:
            if len(tokens) >= len(unsafe) and tuple(tokens[: len(unsafe)]) == unsafe:
                findings.append(finding(f"reviewerCommands[{index}]", f"Reviewer walkthrough must not run `{' '.join(unsafe)}`."))
    return findings


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


def walkthrough_commands() -> list[str]:
    return [
        "python scripts/beta_release_handoff_archive.py",
        "python scripts/beta_onboarding_quickstart_package.py",
        "python scripts/beta_reviewer_acceptance_checklist_package.py",
        "python scripts/beta_release_verification_cli.py",
        "python scripts/local_runtime_prototype.py",
        f"python scripts/run_local_agent.py {REQUIRED_VALID_ADL}",
        f"python scripts/run_local_agent.py {REQUIRED_INVALID_ADL} --json-validation-errors",
    ]


def collect_findings(
    handoff: dict[str, Any],
    quickstart: dict[str, Any],
    checklist: dict[str, Any],
    verification: dict[str, Any],
    review_ui: dict[str, Any],
    runtime: dict[str, Any],
    inventory: list[dict[str, Any]],
    commands: list[str],
    boundaries: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def require(condition: bool, path: str, reason: str) -> None:
        if not condition:
            findings.append(finding(path, reason))

    for item in inventory:
        require(item["exists"] is True, f"artifactInventory.{item['key']}.exists", f"`{item['path']}` must exist.")
        require(bool(item["sha256"]), f"artifactInventory.{item['key']}.sha256", f"`{item['path']}` must have a sha256 pin.")

    require(handoff.get("mode") == "beta-local-release-handoff-archive", "releaseHandoff.mode", "Walkthrough must consume #337 release handoff evidence.")
    require(handoff.get("refreshIssue") == 337, "releaseHandoff.refreshIssue", "Release handoff must be refreshed by #337.")
    require(handoff.get("status") == "pass", "releaseHandoff.status", "Release handoff fixture must pass.")
    require(quickstart.get("mode") == "beta-local-onboarding-quickstart-package", "onboardingQuickstart.mode", "Walkthrough must include the local onboarding quickstart.")
    require(quickstart.get("status") == "pass", "onboardingQuickstart.status", "Onboarding quickstart fixture must pass.")
    require(checklist.get("mode") == "beta-local-reviewer-acceptance-checklist-package", "reviewerChecklist.mode", "Walkthrough must include the reviewer checklist.")
    require(checklist.get("status") == "pass", "reviewerChecklist.status", "Reviewer checklist fixture must pass.")
    require(verification.get("mode") == "beta-local-release-verification-cli", "releaseVerification.mode", "Walkthrough must include release verification output.")
    require(verification.get("status") == "pass", "releaseVerification.status", "Release verification fixture must pass.")
    require(review_ui.get("mode") == "beta-runtime-package-review-ui", "reviewUi.mode", "Walkthrough must include the beta review UI fixture.")
    require(review_ui.get("status") == "pass", "reviewUi.status", "Beta review UI fixture must pass.")

    valid = runtime_scenario(runtime, "adl-v02-memory-observability-dry-run")
    invalid = runtime_scenario(runtime, "invalid-adl-v02-payment-diagnostics")
    diagnostics = stable_diagnostics(runtime)
    require(valid.get("adl") == REQUIRED_VALID_ADL, "runtimePrototype.validRuntimeExample.adl", "Valid ADL v0.2 runtime example path must be included.")
    require(valid.get("status") == "pass", "runtimePrototype.validRuntimeExample.status", "Valid ADL v0.2 runtime example must pass.")
    require((valid.get("completion") or {}).get("status") == "pass", "runtimePrototype.validRuntimeExample.completion.status", "Valid ADL v0.2 completion must pass.")
    require(invalid.get("adl") == REQUIRED_INVALID_ADL, "runtimePrototype.invalidDiagnosticSample.adl", "Invalid ADL v0.2 diagnostic sample path must be included.")
    require(invalid.get("exitCode") == 1, "runtimePrototype.invalidDiagnosticSample.exitCode", "Invalid diagnostic sample must fail validation without runtime activation.")
    require(bool(diagnostics), "runtimePrototype.invalidDiagnosticSample.diagnostics", "Invalid diagnostic sample must include diagnostics.")
    if diagnostics:
        for field in STABLE_DIAGNOSTIC_FIELDS:
            require(field in diagnostics[0], f"runtimePrototype.invalidDiagnosticSample.diagnostics[0].{field}", f"Stable diagnostic field `{field}` is required.")

    handoff_runtime = handoff.get("sourcePackageEvidence", {}).get("adlV02RuntimeEvidence", {})
    require(handoff_runtime.get("validRuntimeExample", {}).get("adl") == REQUIRED_VALID_ADL, "releaseHandoff.adlV02RuntimeEvidence.validRuntimeExample.adl", "Release handoff must expose the valid ADL v0.2 example.")
    require(handoff_runtime.get("invalidDiagnosticSample", {}).get("adl") == REQUIRED_INVALID_ADL, "releaseHandoff.adlV02RuntimeEvidence.invalidDiagnosticSample.adl", "Release handoff must expose the invalid ADL v0.2 diagnostic sample.")
    require(
        handoff_runtime.get("invalidDiagnosticSample", {}).get("stableFields") == list(STABLE_DIAGNOSTIC_FIELDS),
        "releaseHandoff.adlV02RuntimeEvidence.invalidDiagnosticSample.stableFields",
        "Release handoff must preserve the stable diagnostic field contract.",
    )

    findings.extend(command_findings(commands))
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundaries.get(key) is False, f"boundaries.{key}", f"{key} must remain false.")
    require(boundaries.get("deterministicLocalFixturesOnly") is True, "boundaries.deterministicLocalFixturesOnly", "Walkthrough must be fixture-only and deterministic.")
    require(boundaries.get("reviewerWalkthroughSmoke") is True, "boundaries.reviewerWalkthroughSmoke", "Walkthrough smoke boundary must be explicit.")
    return findings


def build_report(commit: str | None = None) -> dict[str, Any]:
    actual_commit = commit or source_commit()
    docs = {key: load_json(ROOT / path) for key, path in REQUIRED_ARTIFACTS.items() if path.endswith(".json")}
    inventory = artifact_inventory()
    commands = walkthrough_commands()
    boundaries = {
        "reviewerWalkthroughSmoke": True,
        "deterministicLocalFixturesOnly": True,
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
    }
    findings = collect_findings(
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
    valid = runtime_scenario(docs["runtimePrototype"], "adl-v02-memory-observability-dry-run")
    invalid = runtime_scenario(docs["runtimePrototype"], "invalid-adl-v02-payment-diagnostics")
    return {
        "mode": "beta-local-reviewer-walkthrough-smoke",
        "issue": 339,
        "parentEpic": 220,
        "follows": [337],
        "walkthroughId": REQUIRED_WALKTHROUGH_ID,
        "releaseId": REQUIRED_RELEASE_ID,
        "status": "pass" if not findings else "fail",
        "sourceCommit": actual_commit,
        "findings": findings,
        "artifactInventory": inventory,
        "reviewerCommands": commands,
        "reviewerPath": [
            "Inspect the #337 release handoff fixture for the pinned ADL v0.2 runtime evidence.",
            "Inspect the onboarding quickstart, reviewer checklist, release verification, and beta review UI fixtures.",
            "Inspect the valid ADL v0.2 runtime example and invalid diagnostic sample directly.",
            "Confirm the invalid diagnostic sample preserves code, severity, category, path, line, and column where available.",
        ],
        "adlV02RuntimeReview": {
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
                "diagnostics": stable_diagnostics(docs["runtimePrototype"]),
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
        "mainnetStatement": "This walkthrough smoke is local/free/deterministic fixture review only. It does not approve or run mainnet; mainnet remains blocked.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the generated walkthrough smoke report JSON.")
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
