#!/usr/bin/env python3
"""Emit a static provider adapter codegen plan without generating code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import provider_compatibility


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["openai", "anthropic", "gemini", "ollama", "langgraph"]
PLAN_BOUNDARY = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
    "writesFiles": False,
    "installsDependencies": False,
    "generatesRunnableCode": False,
}
TARGET_FILE_SHAPES = {
    "openai": [
        {
            "path": "adapters/openai/README.md",
            "purpose": "human review notes for the future OpenAI adapter contract",
            "format": "markdown",
        },
        {
            "path": "adapters/openai/adapter_plan.json",
            "purpose": "metadata-only OpenAI adapter shape plan",
            "format": "json",
        },
        {
            "path": "adapters/openai/tool_schema_review.json",
            "purpose": "function tool schema compatibility review",
            "format": "json",
        },
        {
            "path": "tests/provider_adapter_codegen/openai_plan_test.py",
            "purpose": "future static guard test for OpenAI plan fixtures",
            "format": "python-test",
        },
    ],
    "anthropic": [
        {
            "path": "adapters/anthropic/README.md",
            "purpose": "human review notes for the future Anthropic MCP adapter contract",
            "format": "markdown",
        },
        {
            "path": "adapters/anthropic/adapter_plan.json",
            "purpose": "metadata-only Anthropic MCP adapter shape plan",
            "format": "json",
        },
        {
            "path": "adapters/anthropic/mcp_declaration_review.json",
            "purpose": "MCP declaration compatibility review without server resolution",
            "format": "json",
        },
        {
            "path": "tests/provider_adapter_codegen/anthropic_plan_test.py",
            "purpose": "future static guard test for Anthropic plan fixtures",
            "format": "python-test",
        },
    ],
    "gemini": [
        {
            "path": "adapters/gemini/README.md",
            "purpose": "human review notes for the future Gemini adapter contract",
            "format": "markdown",
        },
        {
            "path": "adapters/gemini/adapter_plan.json",
            "purpose": "metadata-only Gemini adapter shape plan",
            "format": "json",
        },
        {
            "path": "adapters/gemini/function_declaration_review.json",
            "purpose": "Gemini function declaration compatibility review",
            "format": "json",
        },
        {
            "path": "tests/provider_adapter_codegen/gemini_plan_test.py",
            "purpose": "future static guard test for Gemini plan fixtures",
            "format": "python-test",
        },
    ],
    "ollama": [
        {
            "path": "adapters/ollama/README.md",
            "purpose": "human review notes for the future Ollama/local adapter contract",
            "format": "markdown",
        },
        {
            "path": "adapters/ollama/adapter_plan.json",
            "purpose": "metadata-only Ollama/local adapter shape plan",
            "format": "json",
        },
        {
            "path": "adapters/ollama/local_harness_review.json",
            "purpose": "local harness compatibility review without endpoint probing",
            "format": "json",
        },
        {
            "path": "tests/provider_adapter_codegen/ollama_plan_test.py",
            "purpose": "future static guard test for Ollama/local plan fixtures",
            "format": "python-test",
        },
    ],
    "langgraph": [
        {
            "path": "adapters/langgraph/README.md",
            "purpose": "human review notes for the future LangGraph adapter contract",
            "format": "markdown",
        },
        {
            "path": "adapters/langgraph/adapter_plan.json",
            "purpose": "metadata-only LangGraph adapter shape plan",
            "format": "json",
        },
        {
            "path": "adapters/langgraph/static_graph_review.json",
            "purpose": "static graph compatibility review without graph compilation",
            "format": "json",
        },
        {
            "path": "tests/provider_adapter_codegen/langgraph_plan_test.py",
            "purpose": "future static guard test for LangGraph plan fixtures",
            "format": "python-test",
        },
    ],
}
TARGET_BLOCKERS = {
    "openai": [
        "No reviewed OpenAI runtime adapter contract exists.",
        "Required API credential handling policy is not implemented in this repo.",
    ],
    "anthropic": [
        "No reviewed Anthropic runtime adapter contract exists.",
        "MCP declarations are metadata-only and cannot be resolved or invoked.",
    ],
    "gemini": [
        "No reviewed Gemini runtime adapter contract exists.",
        "Grounding and code-execution surfaces are compatibility diagnostics only.",
    ],
    "ollama": [
        "No reviewed local model harness contract exists.",
        "Local endpoints and model ids must not be probed by the planner.",
    ],
    "langgraph": [
        "No reviewed LangGraph runtime graph contract exists.",
        "Graph, state, checkpoint, and interrupt semantics are static-plan-only.",
    ],
}
VALIDATION_GATES = [
    "provider compatibility report remains deterministic",
    "planned file list is report-only and writesFiles=false",
    "target-specific unsupported semantics are listed before codegen",
    "payment, MCP, runtime, credential, and network boundaries remain disabled",
    "no provider SDK install/import/call occurs during validation",
]
MANIFEST_VALIDATION_GATES = [
    {
        "id": "manifest-fixture-deterministic",
        "description": "adapter manifest fixture is derived from deterministic compatibility reports",
    },
    {
        "id": "manifest-files-report-only",
        "description": "planned adapter files are metadata entries and are not written by this plan",
    },
    {
        "id": "manifest-target-support-metadata",
        "description": "required secrets, hosted services, unsupported semantics, and blockers are explicit",
    },
    {
        "id": "manifest-runtime-boundary-disabled",
        "description": "runtime, network, MCP, payment, credential, and runnable codegen paths remain disabled",
    },
]


def planned_targets(values: list[str]) -> list[str]:
    if not values or "all" in values:
        return TARGETS
    return values


def planned_examples(paths: list[str], agents: list[str]) -> list[Path]:
    return provider_compatibility.selected_examples(paths, agents)


def unsupported_semantics(report: dict) -> list[str]:
    semantics = list(report["unsupportedFeatures"])
    mapping = report.get("providerMapping", {}).get("adapterMapping", {})
    semantics.extend(f"metadata_only:{field}" for field in mapping.get("metadataOnly", []))
    semantics.extend(f"unsupported_execution:{tool}" for tool in mapping.get("unsupportedExecution", []))
    return sorted(dict.fromkeys(semantics))


def target_summary(target: str, reports: list[dict]) -> dict:
    target_reports = [item for item in reports if item["target"] == target]
    required_secrets = sorted(
        {secret for item in target_reports for secret in item["requiredSecrets"]}
    )
    hosted_services = sorted(
        {service for item in target_reports for service in item["requiredHostedServices"]}
    )
    unsupported = sorted(
        {semantic for item in target_reports for semantic in unsupported_semantics(item)}
    )
    warning_count = sum(len(item["warnings"]) for item in target_reports)

    return {
        "target": target,
        "compatibilityModes": sorted(
            {item["compatibilityMode"] for item in target_reports}
        ),
        "plannedFileShapes": TARGET_FILE_SHAPES[target],
        "targetBlockers": TARGET_BLOCKERS[target],
        "requiredSecrets": required_secrets,
        "requiredHostedServices": hosted_services,
        "unsupportedSemantics": unsupported,
        "warningCount": warning_count,
        "codegenStatus": "blocked-report-only",
        "generationAllowed": False,
    }


def target_manifest(summary: dict) -> dict:
    blocker_ids = [
        f"{summary['target']}-blocker-{index}"
        for index, _ in enumerate(summary["targetBlockers"], start=1)
    ]
    return {
        "target": summary["target"],
        "manifestId": f"{summary['target']}-provider-adapter-codegen-manifest",
        "manifestStatus": "blocked-report-only",
        "compatibilityModes": summary["compatibilityModes"],
        "plannedFiles": [
            {
                **file_shape,
                "plannedOnly": True,
                "generatedByThisPlan": False,
                "validationStatus": "not-generated",
            }
            for file_shape in summary["plannedFileShapes"]
        ],
        "targetSupportMetadata": {
            "requiredSecretRefs": summary["requiredSecrets"],
            "hostedServiceRefs": summary["requiredHostedServices"],
            "unsupportedSemantics": summary["unsupportedSemantics"],
            "warningCount": summary["warningCount"],
        },
        "validationGateIds": [gate["id"] for gate in MANIFEST_VALIDATION_GATES],
        "blockers": [
            {"id": blocker_id, "description": description}
            for blocker_id, description in zip(blocker_ids, summary["targetBlockers"])
        ],
        "generationAllowed": False,
    }


def build_plan(examples: list[Path], targets: list[str]) -> dict:
    reports = [
        provider_compatibility.report(example, target)
        for example in examples
        for target in targets
    ]
    target_plans = [target_summary(target, reports) for target in targets]
    return {
        "planId": "provider-adapter-codegen-compatibility-only",
        "planStatus": "blocked-before-runnable-codegen",
        "boundary": PLAN_BOUNDARY,
        "inputs": {
            "examples": [str(path.relative_to(ROOT)) for path in examples],
            "targets": targets,
            "compatibilityReportCount": len(reports),
        },
        "targetPlans": target_plans,
        "adapterManifestFixture": {
            "schemaVersion": "provider-adapter-codegen-manifest-fixture.v0.1",
            "fixtureId": "provider-adapter-codegen-manifest-fixtures",
            "fixtureStatus": "blocked-report-only",
            "boundary": PLAN_BOUNDARY,
            "manifestValidationGates": MANIFEST_VALIDATION_GATES,
            "targetManifests": [target_manifest(summary) for summary in target_plans],
        },
        "validationGates": VALIDATION_GATES,
        "nonGoals": [
            "generate runnable provider adapter code",
            "install provider SDKs or local model dependencies",
            "call provider APIs or local model endpoints",
            "resolve or invoke MCP servers",
            "read, write, or require credentials",
            "touch wallets, facilitators, payment rails, or settlement",
            "mutate production gateway or deployment configuration",
        ],
    }


def render_json(plan: dict) -> str:
    return json.dumps(plan, indent=2) + "\n"


def render_summary(plan: dict) -> str:
    lines = [
        "Provider adapter codegen plan (compatibility-only)",
        (
            "boundary: runtimeExecutionAllowed=false networkAccess=false "
            "paymentAccess=false mcpInvocation=false writesFiles=false "
            "installsDependencies=false generatesRunnableCode=false"
        ),
    ]
    for item in plan["targetPlans"]:
        unsupported = ",".join(item["unsupportedSemantics"]) or "none"
        lines.append(
            f"- {item['target']}: status={item['codegenStatus']} "
            f"files={len(item['plannedFileShapes'])} "
            f"requiredSecrets={','.join(item['requiredSecrets']) or 'none'} "
            f"unsupported={unsupported}"
        )
    return "\n".join(lines) + "\n"


def write_or_print(content: str, output: Path | None) -> None:
    if output is None:
        print(content, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", nargs="*", help="ADL example paths. Defaults to examples/*.yaml.")
    parser.add_argument(
        "--target",
        action="append",
        choices=["all", *TARGETS],
        default=[],
        help="Provider target to include. Repeat for multiple targets. Defaults to all.",
    )
    parser.add_argument(
        "--agent",
        action="append",
        default=[],
        help="Filter by metadata.name. Repeat for multiple agents.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="json",
        help="Output format. JSON remains the deterministic evidence format.",
    )
    parser.add_argument("--output", type=Path, help="Write the plan to a file instead of stdout.")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    examples = planned_examples(args.examples, args.agent)
    if not examples:
        print("No ADL examples matched the requested selection.", file=sys.stderr)
        return 1

    plan = build_plan(examples, planned_targets(args.target))
    content = render_json(plan) if args.format == "json" else render_summary(plan)
    write_or_print(content, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
