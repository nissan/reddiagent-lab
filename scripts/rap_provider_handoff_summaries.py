#!/usr/bin/env python3
"""Emit UI-safe RAP bridge and provider adapter handoff summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import provider_adapter_codegen_plan
import rap_bridge_report


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
}
DEFAULT_RAP_FIXTURE = ROOT / "tests" / "fixtures" / "rap-bridge-x402-paid-mcp-ready.json"
DEFAULT_PROVIDER_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "tool-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
    ROOT / "examples" / "mcp-readonly-agent.yaml",
]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def blocked_live_action_warnings() -> list[str]:
    return [
        "no live RAP bridge execution",
        "no provider or local model call",
        "no MCP server resolution or invocation",
        "no credential lookup or storage",
        "no wallet, facilitator, payment rail, or settlement access",
    ]


def rap_summary(path: Path) -> dict:
    report = rap_bridge_report.report(path)
    conformance = report["dryRunBridgeConformance"]
    receipt_reputation = report["receiptReputationConformance"]
    validation_refs = list(
        dict.fromkeys(
            [
                "tests/test_rap_bridge_report.py",
                "tests/RAP-BRIDGE-REPORT.md",
                *conformance.get("evidenceRefs", []),
            ]
        )
    )
    return {
        "kind": "rap-bridge",
        "label": "RAP bridge handoff",
        "source": report["source"],
        "status": report["status"],
        "readiness": "report-ready" if report["bridgeReady"] else "blocked",
        "uiBadge": "ready-static-report" if report["bridgeReady"] else "blocked-static-report",
        "summary": {
            "bridgeReady": report["bridgeReady"],
            "rapReadyCount": len(report["rapReady"]),
            "metadataOnlySections": [entry["section"] for entry in report["metadataOnly"]],
            "unsafeCount": len(report["unsafe"]),
            "unsupportedCount": len(report["unsupported"]),
            "conformanceStatus": conformance["status"],
            "receiptReputationStatus": receipt_reputation["status"],
        },
        "blockedLiveActionWarnings": blocked_live_action_warnings(),
        "validationRefs": validation_refs,
        **BOUNDARY_FLAGS,
    }


def provider_summary(examples: list[Path]) -> dict:
    plan = provider_adapter_codegen_plan.build_plan(
        examples,
        provider_adapter_codegen_plan.TARGETS,
    )
    fixture = plan["adapterManifestFixture"]
    target_manifests = fixture["targetManifests"]
    required_secrets = sorted(
        {
            secret
            for manifest in target_manifests
            for secret in manifest["targetSupportMetadata"]["requiredSecretRefs"]
        }
    )
    hosted_services = sorted(
        {
            service
            for manifest in target_manifests
            for service in manifest["targetSupportMetadata"]["hostedServiceRefs"]
        }
    )
    blockers = [
        {
            "target": manifest["target"],
            "ids": [blocker["id"] for blocker in manifest["blockers"]],
        }
        for manifest in target_manifests
    ]
    return {
        "kind": "provider-adapter",
        "label": "Provider adapter handoff",
        "source": "tests/fixtures/provider-adapter-codegen-manifest.json",
        "status": fixture["fixtureStatus"],
        "readiness": "blocked-before-codegen",
        "uiBadge": "blocked-static-plan",
        "summary": {
            "targetCount": len(target_manifests),
            "targets": [manifest["target"] for manifest in target_manifests],
            "plannedFileCount": sum(len(manifest["plannedFiles"]) for manifest in target_manifests),
            "requiredSecretRefs": required_secrets,
            "hostedServiceRefs": hosted_services,
            "validationGateIds": [gate["id"] for gate in fixture["manifestValidationGates"]],
            "blockers": blockers,
            "generationAllowed": False,
        },
        "blockedLiveActionWarnings": blocked_live_action_warnings(),
        "validationRefs": [
            "tests/test_provider_adapter_codegen_plan.py",
            "tests/PROVIDER-ADAPTER-CODEGEN-PLAN-REPORT.md",
            "tests/fixtures/provider-adapter-codegen-manifest.json",
        ],
        **BOUNDARY_FLAGS,
    }


def build_fixture(rap_fixture: Path, provider_examples: list[Path]) -> dict:
    resolved_examples = [
        path if path.is_absolute() else ROOT / path
        for path in provider_examples
    ]
    summaries = [
        rap_summary(rap_fixture),
        provider_summary(resolved_examples),
    ]
    return {
        "format": "ui-safe-rap-provider-handoff-summaries",
        "generatedFrom": "scripts/rap_provider_handoff_summaries.py",
        "authoritativeCheck": "tests/test_rap_provider_handoff_summaries.py",
        "guardrails": {
            "uiSafe": True,
            "staticFixtureOnly": True,
            "redactsSecrets": True,
            **BOUNDARY_FLAGS,
        },
        "summaries": summaries,
    }


def render_json(fixture: dict) -> str:
    return json.dumps(fixture, indent=2) + "\n"


def write_or_print(content: str, output: Path | None) -> None:
    if output is None:
        print(content, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rap-fixture",
        type=Path,
        default=DEFAULT_RAP_FIXTURE,
        help="Static RAP bridge fixture to summarize.",
    )
    parser.add_argument(
        "--provider-example",
        action="append",
        type=Path,
        default=[],
        help="ADL example for provider adapter handoff summaries. Repeat to override defaults.",
    )
    parser.add_argument("--output", type=Path, help="Write JSON to a file instead of stdout.")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    examples = args.provider_example or DEFAULT_PROVIDER_EXAMPLES
    fixture = build_fixture(args.rap_fixture, examples)
    write_or_print(render_json(fixture), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
