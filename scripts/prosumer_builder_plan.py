#!/usr/bin/env python3
"""Static Prosumer Builder MVP plan for ADL examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml

import eve_compatibility
import rap_provider_handoff_summaries
from run_local_agent import build_trace, run_tool_fixtures
from source_check import check_tool_sources, summarize_source_checks


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "tool-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "relayAccess": False,
    "providerAccess": False,
    "credentialAccess": False,
    "toolInvocation": False,
    "toolExecutionAllowed": False,
    "paymentAccess": False,
    "mcpInvocation": False,
    "walletAccess": False,
    "deploymentAllowed": False,
    "bidirectionalImportAllowed": False,
    "publicDistributionAllowed": False,
    "publicBrandingAllowed": False,
}
EXPORT_MATRIX_TARGETS = [
    {
        "target": "agent-spec",
        "label": "Agent Spec",
        "commandTemplate": "python3 scripts/agent_spec_compatibility.py --single {source}",
        "strictCommandTemplate": "python3 scripts/agent_spec_compatibility.py --export-agent-spec --single {source}",
        "authoritativeCheck": "tests/test_agent_spec_compatibility.py",
    },
    {
        "target": "a2a-agent-card",
        "label": "A2A Agent Card",
        "commandTemplate": "python3 scripts/adl_to_a2a_agent_card.py --single {source}",
        "strictCommandTemplate": "python3 scripts/adl_to_a2a_agent_card.py --export-agent-card --single {source}",
        "authoritativeCheck": "tests/test_a2a_agent_card_export.py",
    },
    {
        "target": "agent-skills-skill-md",
        "label": "Agent Skills / SKILL.md",
        "commandTemplate": "python3 scripts/adl_to_agent_skill.py --single {source}",
        "strictCommandTemplate": "python3 scripts/adl_to_agent_skill.py --export-skill-package --single {source}",
        "authoritativeCheck": "tests/test_agent_skill_export.py",
    },
    {
        "target": "starter-manifest",
        "label": "Starter manifest",
        "commandTemplate": "python3 scripts/starter_code_plan.py --single {source}",
        "strictCommandTemplate": None,
        "authoritativeCheck": "tests/test_starter_code_plan.py",
    },
    {
        "target": "provider-compatibility",
        "label": "Provider compatibility",
        "commandTemplate": "python3 scripts/provider_compatibility.py {source}",
        "strictCommandTemplate": None,
        "authoritativeCheck": "tests/test_provider_compatibility_cli.py",
    },
    {
        "target": "rap-bridge",
        "label": "RAP bridge",
        "commandTemplate": "python3 scripts/rap_bridge_report.py tests/fixtures/rap-bridge-x402-paid-mcp-ready.json",
        "strictCommandTemplate": None,
        "authoritativeCheck": "tests/test_rap_bridge_report.py",
    },
    {
        "target": "vercel-eve",
        "label": "Vercel eve",
        "commandTemplate": "python3 scripts/eve_compatibility.py --single {source}",
        "strictCommandTemplate": None,
        "authoritativeCheck": "tests/test_eve_compatibility.py",
    },
    {
        "target": "buzz-static-projection",
        "label": "Buzz static projection",
        "commandTemplate": "python3 scripts/buzz_export.py --single {source} [immutable pins, signed identity binding, governance review, and required evaluation time]",
        "strictCommandTemplate": "python3 scripts/buzz_export.py --single {source} [immutable pins, signed identity binding, governance review, and required evaluation time] --export-package <empty-output-dir>",
        "authoritativeCheck": "tests/test_buzz_export.py",
    },
]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_adl(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def schema_errors(doc: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    rendered = []
    for error in errors:
        loc = ".".join(str(part) for part in error.path) or "<root>"
        rendered.append(f"{loc}: {error.message}")
    return rendered


def builder_job(doc: dict) -> dict:
    metadata = doc.get("metadata") or {}
    return {
        "agentName": metadata.get("name"),
        "description": metadata.get("description"),
        "source": "ADL metadata",
    }


def model_profile(doc: dict) -> dict:
    model = doc.get("model") or {}
    providers = model.get("providers") or {}
    requirements = model.get("requirements") or {}
    return {
        "capability": model.get("capability"),
        "preferredProvider": providers.get("preferred"),
        "fallbackProviders": providers.get("fallbacks", []),
        "toolCalling": bool(requirements.get("toolCalling")),
        "structuredOutput": bool(requirements.get("structuredOutput")),
    }


def tool_profile(doc: dict) -> dict:
    harness = doc.get("harness") or {}
    tools = harness.get("tools") or []
    fixtures = harness.get("toolFixtures") or []
    return {
        "toolCount": len(tools),
        "tools": [
            {
                "id": tool.get("id") or tool.get("toolName"),
                "type": tool.get("type"),
                "description": tool.get("description"),
            }
            for tool in tools
        ],
        "deterministicFixtureCount": len(fixtures),
        "deterministicFixtureIds": [fixture.get("toolId") for fixture in fixtures],
    }


def policy_eval_profile(doc: dict) -> dict:
    harness = doc.get("harness") or {}
    return {
        "policies": [
            {"id": policy.get("id"), "type": policy.get("type"), "rule": policy.get("rule")}
            for policy in harness.get("policies", []) or []
        ],
        "evalGates": [
            {"id": gate.get("id"), "type": gate.get("type"), "rule": gate.get("rule")}
            for gate in harness.get("evalGates", []) or []
        ],
    }


def validation_step(path: Path, errors: list[str]) -> dict:
    return {
        "id": "validate",
        "label": "Validate ADL",
        "status": "pass" if not errors else "fail",
        "command": f"python3 scripts/validate_examples.py --format json {display_path(path)}",
        "errors": errors,
    }


def dry_run_preview(path: Path, doc: dict, errors: list[str]) -> dict:
    command = f"python3 scripts/run_local_agent.py {display_path(path)}"
    harness = doc.get("harness") or {}
    if harness.get("toolFixtures"):
        command += " --execute-tools --fail-on-required-gate"
    if errors:
        return {
            "status": "blocked",
            "command": command,
            "completion": None,
            "trace": [],
            "toolExecution": None,
            "sourceChecks": [],
            "sourceCheckSummary": None,
        }

    tool_results = run_tool_fixtures(doc) if harness.get("toolFixtures") else []
    source_checks = check_tool_sources(tool_results) if tool_results else []
    source_check_summary = summarize_source_checks(source_checks) if tool_results else None
    denied_count = sum(1 for result in tool_results if result["status"] == "denied")
    required_gate_status = "fail" if denied_count or (source_check_summary or {}).get("status") == "fail" else "pass"
    completion_reason = (
        "dry-run transport completed, but required gates failed"
        if required_gate_status == "fail"
        else "dry-run transport completed and required gates passed"
    )
    completion = {
        "transportStatus": "pass",
        "requiredGateStatus": required_gate_status,
        "status": required_gate_status,
        "reason": completion_reason,
    }
    tool_execution = None
    if harness.get("toolFixtures"):
        tool_execution = {
            "mode": "local-fixture",
            "networkAccess": False,
            "paymentAccess": False,
            "deniedCount": denied_count,
            "resultCount": len(tool_results),
            "resultStatuses": [
                {"toolId": result["toolId"], "status": result["status"]}
                for result in tool_results
            ],
        }
    return {
        "status": "ready",
        "command": command,
        "completion": completion,
        "trace": build_trace(
            doc,
            path,
            tool_results,
            source_checks,
            completion_status=completion["status"],
            completion_reason=completion_reason,
        ),
        "toolExecution": tool_execution,
        "sourceChecks": source_checks,
        "sourceCheckSummary": source_check_summary,
    }


def dry_run_step(preview: dict) -> dict:
    return {
        "id": "dry_run",
        "label": "Dry-run locally",
        "status": preview["status"],
        "command": preview["command"],
        "mode": "local-dry-run",
        "completionPreview": preview["completion"],
        "toolExecutionPreview": preview["toolExecution"],
        "sourceChecksPreview": preview["sourceChecks"],
        "sourceCheckSummaryPreview": preview["sourceCheckSummary"],
        "tracePreview": preview["trace"],
    }


def trace_step(errors: list[str], preview: dict) -> dict:
    expected_events = [
        event["event"]
        for event in preview["trace"]
    ] if not errors else [
        "session.started",
        "model.resolved",
        "tools.registered",
        "policies.loaded",
        "evals.loaded",
        "task.dry_run_completed",
    ]
    return {
        "id": "trace",
        "label": "Inspect trace",
        "status": "blocked" if errors else "ready",
        "expectedEvents": expected_events,
    }


def export_readiness_matrix(path: Path, doc: dict, errors: list[str]) -> list[dict]:
    source = display_path(path)
    static_review = unsafe_or_metadata_only(doc)
    harness = doc.get("harness") or {}
    reddi_metadata_sections = [
        section
        for section, value in [
            ("harness.policies", harness.get("policies")),
            ("harness.evalGates", harness.get("evalGates")),
            ("harness.memory", harness.get("memory")),
            ("harness.dataSources", harness.get("dataSources")),
        ]
        if value
    ]
    blocked_by_validation = ["validation_failed"] if errors else []
    has_rap_metadata = bool(
        (doc.get("extensions") or {}).get("x402")
        or (doc.get("extensions") or {}).get("receipts")
        or (doc.get("extensions") or {}).get("reputation")
    )
    rows = []
    for target in EXPORT_MATRIX_TARGETS:
        target_id = target["target"]
        command = target["commandTemplate"].format(source=source)
        strict_template = target.get("strictCommandTemplate")
        row = {
            "target": target_id,
            "label": target["label"],
            "mode": "report-only",
            "command": command,
            "strictExportCommand": strict_template.format(source=source) if strict_template else None,
            "authoritativeCheck": target["authoritativeCheck"],
            "status": "report-ready",
            "readiness": "report-ready",
            "blockedBy": list(blocked_by_validation),
            "metadataOnlyExtensions": [],
            "metadataOnlySections": [],
            **BOUNDARY_FLAGS,
        }
        if target_id == "vercel-eve":
            row["eveCompatibilitySummary"] = eve_compatibility_summary(path)
        if target_id == "buzz-static-projection":
            import buzz_export
            summary = buzz_export.parity_summary(doc, errors)
            row.update(summary)
        if errors:
            row["status"] = "blocked"
            row["readiness"] = "blocked-by-validation"
        elif target_id in {"agent-spec", "a2a-agent-card", "agent-skills-skill-md"}:
            row["metadataOnlyExtensions"] = static_review["metadataOnlyExtensions"]
            row["metadataOnlySections"] = [
                *reddi_metadata_sections,
                *static_review["metadataOnlyExtensions"],
            ]
            if row["metadataOnlySections"] or static_review["unsupportedFeatures"]:
                row["status"] = "metadata-only"
                row["readiness"] = "metadata-only"
                row["blockedBy"] = static_review["unsupportedFeatures"]
        elif target_id == "starter-manifest":
            row["status"] = "blocked-before-generation"
            row["readiness"] = "blocked-before-generation"
            row["blockedBy"] = ["generator-implementation-review"]
        elif target_id == "rap-bridge" and not has_rap_metadata:
            row["status"] = "not-applicable"
            row["readiness"] = "not-applicable"
            row["blockedBy"] = ["no_payment_receipt_reputation_metadata"]
        elif target_id == "vercel-eve":
            row["metadataOnlyExtensions"] = static_review["metadataOnlyExtensions"]
            row["metadataOnlySections"] = [
                *reddi_metadata_sections,
                *static_review["metadataOnlyExtensions"],
            ]
            if row["metadataOnlySections"] or static_review["unsupportedFeatures"]:
                row["status"] = "metadata-only"
                row["readiness"] = "metadata-only"
                row["blockedBy"] = static_review["unsupportedFeatures"]
        rows.append(row)
    return rows


def eve_compatibility_summary(path: Path) -> dict:
    report = eve_compatibility.report_for(path)
    unsupported = report["unsupportedFeatures"]
    metadata_only = report["metadataOnlySections"]
    validation_errors = report["validationErrors"]
    blocked_warnings = [
        "no live eve runtime install or execution",
        "no provider/model API call",
        "no MCP server resolution or invocation",
        "no credential lookup/access",
        "no wallet, facilitator, payment rail, or settlement access",
        "no server start, deployment, package publishing, or production gateway mutation",
    ]
    if report["status"] == "blocked-by-validation":
        ui_state = "blocked"
        lossless_state = "blocked-by-validation"
    elif unsupported:
        ui_state = "unsupported-runtime-features"
        lossless_state = "not-lossless-unsupported"
    elif metadata_only:
        ui_state = "metadata-only"
        lossless_state = "not-lossless-metadata-only"
    else:
        ui_state = "lossless-static-compatible"
        lossless_state = "lossless-static-report"

    future_work = []
    if unsupported:
        future_work.append("runtime enforcement for unsupported eve features")
    if metadata_only:
        future_work.append("native eve enforcement for ReddiAgent metadata-only sections")
    if validation_errors:
        future_work.append("valid ADL input before eve export review")
    if not future_work:
        future_work.append("strict eve export review before any generated project files")

    return {
        "target": "vercel-eve",
        "label": "Vercel eve",
        "source": report["source"],
        "agent": report["agent"],
        "status": report["status"],
        "uiState": ui_state,
        "losslessState": lossless_state,
        "supported": report["supported"],
        "metadataOnlySections": metadata_only,
        "unsupportedFeatures": unsupported,
        "validationErrors": validation_errors,
        "projectRootPreview": report["projectManifest"]["projectRoot"],
        "plannedFileCount": len(report["projectManifest"]["files"]),
        "plannedConnectionCount": len(report["projectManifest"]["connections"]),
        "sourceReportCommand": f"python3 scripts/eve_compatibility.py --single {report['source']}",
        "authoritativeCheck": "tests/test_eve_compatibility.py",
        "blockedLiveActionWarnings": blocked_warnings,
        "futureWork": future_work,
        "deploymentAllowed": False,
        **BOUNDARY_FLAGS,
    }


def export_step(path: Path, doc: dict, errors: list[str]) -> dict:
    matrix = export_readiness_matrix(path, doc, errors)
    return {
        "id": "export",
        "label": "Export review artifacts",
        "status": "blocked" if errors else "ready",
        "targets": [
            {
                "target": row["target"],
                "command": row["command"],
                "mode": row["mode"],
            }
            for row in matrix
        ],
        "staticUiExportMatrix": matrix,
        "staticUiHandoffSummaries": rap_provider_handoff_summaries.build_fixture(
            rap_provider_handoff_summaries.DEFAULT_RAP_FIXTURE,
            rap_provider_handoff_summaries.DEFAULT_PROVIDER_EXAMPLES,
        )["summaries"],
    }


def unsafe_or_metadata_only(doc: dict) -> dict:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    unsupported = []
    metadata_only = []

    if harness.get("runtime", {}).get("target") != "local-python":
        unsupported.append("non_local_runtime_execution")
    if (extensions.get("x402") or {}).get("enabled"):
        unsupported.append("live_payment_execution")
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")
    for tool in harness.get("tools", []) or []:
        if tool.get("type") == "mcp":
            unsupported.append("mcp_runtime_invocation")
            break

    return {
        "unsupportedFeatures": unsupported,
        "metadataOnlyExtensions": metadata_only,
    }


def plan_for(path: Path) -> dict:
    doc = read_adl(path)
    errors = schema_errors(doc)
    static_review = unsafe_or_metadata_only(doc)
    preview = dry_run_preview(path, doc, errors)
    return {
        "format": "prosumer-builder-mvp-plan",
        "source": display_path(path),
        "agent": (doc.get("metadata") or {}).get("name"),
        "supported": not errors,
        **BOUNDARY_FLAGS,
        **static_review,
        "flow": [
            {
                "id": "choose_job",
                "label": "Choose job",
                "status": "ready",
                "selection": builder_job(doc),
            },
            {
                "id": "model_profile",
                "label": "Pick model profile",
                "status": "ready",
                "selection": model_profile(doc),
            },
            {
                "id": "tool",
                "label": "Add optional tool",
                "status": "ready",
                "selection": tool_profile(doc),
            },
            {
                "id": "policy_eval_gate",
                "label": "Add policy and eval gate",
                "status": "ready",
                "selection": policy_eval_profile(doc),
            },
            validation_step(path, errors),
            dry_run_step(preview),
            trace_step(errors, preview),
            export_step(path, doc, errors),
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--single", action="store_true", help="Emit one plan object instead of a list.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    if args.single and len(paths) != 1:
        print("--single requires exactly one ADL path", file=sys.stderr)
        return 2
    plans = [plan_for(path) for path in paths]
    payload: object = plans[0] if args.single else plans
    print(json.dumps(payload, indent=2))
    return 1 if any(not plan["supported"] for plan in plans) else 0


if __name__ == "__main__":
    sys.exit(main())
