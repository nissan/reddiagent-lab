#!/usr/bin/env python3
"""Static starter-code review manifest for ADL examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml


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
    "paymentAccess": False,
    "mcpInvocation": False,
    "writesFiles": False,
    "installsDependencies": False,
}


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


def slugify(name: str | None) -> str:
    if not name:
        return "unnamed-agent"
    return "".join(char if char.isalnum() else "-" for char in name.lower()).strip("-")


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
        "toolIds": [tool.get("id") or tool.get("toolName") for tool in tools],
        "fixtureCount": len(fixtures),
        "fixtureToolIds": [fixture.get("toolId") for fixture in fixtures],
    }


def metadata_boundaries(doc: dict) -> dict:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    unsupported = []
    metadata_only = []

    if harness.get("runtime", {}).get("target") != "local-python":
        unsupported.append("non_local_runtime_execution")
    if any(tool.get("type") == "mcp" for tool in harness.get("tools", []) or []):
        unsupported.append("mcp_runtime_invocation")
    if (extensions.get("x402") or {}).get("enabled"):
        unsupported.append("live_payment_execution")
        metadata_only.append("extensions.x402")
    if extensions.get("receipts"):
        metadata_only.append("extensions.receipts")
    if extensions.get("reputation"):
        metadata_only.append("extensions.reputation")

    return {
        "unsupportedFeatures": unsupported,
        "metadataOnlyExtensions": metadata_only,
    }


def planned_files(agent_slug: str, doc: dict) -> list[dict]:
    harness = doc.get("harness") or {}
    files = [
        {
            "path": f"starter/{agent_slug}/README.md",
            "purpose": "Explain the generated starter review package and remaining human gates.",
            "status": "review-only",
        },
        {
            "path": f"starter/{agent_slug}/agent.adl.yaml",
            "purpose": "Copy the source ADL as the canonical input, not a generated runtime contract.",
            "status": "review-only",
        },
        {
            "path": f"starter/{agent_slug}/src/agent_harness.py",
            "purpose": "Skeleton entry point that a future approved generator could fill in.",
            "status": "placeholder-only",
        },
        {
            "path": f"starter/{agent_slug}/tests/test_static_contract.py",
            "purpose": "Pin expected boundary flags and static manifest shape before any runtime work.",
            "status": "placeholder-only",
        },
        {
            "path": f"starter/{agent_slug}/.env.example",
            "purpose": "List environment variable names only after a separate credential policy review.",
            "status": "withheld",
        },
    ]
    if harness.get("toolFixtures"):
        files.append(
            {
                "path": f"starter/{agent_slug}/fixtures/tools.json",
                "purpose": "Package deterministic local tool fixtures for tests without network access.",
                "status": "review-only",
            }
        )
    if harness.get("policies") or harness.get("evalGates"):
        files.append(
            {
                "path": f"starter/{agent_slug}/tests/test_policy_eval_gates.py",
                "purpose": "Describe policy/eval assertions that must pass before generated code can run.",
                "status": "placeholder-only",
            }
        )
    return files


def blocked_gates(doc: dict) -> list[dict]:
    harness = doc.get("harness") or {}
    extensions = doc.get("extensions") or {}
    gates = [
        {
            "id": "generator-implementation-review",
            "status": "required",
            "reason": "This artifact is a manifest only; runnable starter generation needs a separate reviewed issue.",
        },
        {
            "id": "dependency-install-review",
            "status": "required",
            "reason": "No package manager or framework dependencies are installed in report-only mode.",
        },
        {
            "id": "provider-runtime-review",
            "status": "required",
            "reason": "Provider calls and model execution remain blocked until an approved runtime adapter exists.",
        },
    ]
    if harness.get("runtime", {}).get("target") != "local-python":
        gates.append(
            {
                "id": "runtime-target-review",
                "status": "required",
                "reason": "Non-local runtime targets require a separate deployment/runtime approval.",
            }
        )
    if any(tool.get("type") == "mcp" for tool in harness.get("tools", []) or []):
        gates.append(
            {
                "id": "mcp-resolution-review",
                "status": "required",
                "reason": "MCP server resolution and invocation are intentionally out of scope.",
            }
        )
    if (extensions.get("x402") or {}).get("enabled"):
        gates.append(
            {
                "id": "payment-rail-review",
                "status": "required",
                "reason": "Wallet, facilitator, settlement, and paid execution paths remain blocked.",
            }
        )
    return gates


def dry_run_file_manifest(
    source: Path,
    agent_slug: str,
    planned: list[dict],
    gates: list[dict],
    validation_status: str,
) -> dict:
    status_counts: dict[str, int] = {}
    for item in planned:
        status = item["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "format": "starter-code-dry-run-file-manifest-fixture",
        "source": display_path(source),
        "outputRoot": f"starter/{agent_slug}",
        "manifestOnly": True,
        "writesFiles": False,
        "validationStatus": validation_status,
        "fileCount": len(planned),
        "paths": [item["path"] for item in planned],
        "statusCounts": status_counts,
        "blockedGateIds": [gate["id"] for gate in gates],
        "nonGoalIds": [
            "no-file-writes",
            "no-dependency-install",
            "no-provider-model-mcp-payment-calls",
            "no-sensitive-payloads",
        ],
    }


def plan_for(path: Path) -> dict:
    doc = read_adl(path)
    errors = schema_errors(doc)
    metadata = doc.get("metadata") or {}
    agent_name = metadata.get("name")
    agent_slug = slugify(agent_name)
    validation_status = "pass" if not errors else "fail"
    planned = [] if errors else planned_files(agent_slug, doc)
    gates = blocked_gates(doc)
    return {
        "format": "starter-code-review-manifest",
        "source": display_path(path),
        "agent": agent_name,
        "supported": not errors,
        **BOUNDARY_FLAGS,
        **metadata_boundaries(doc),
        "target": {
            "language": "python",
            "packageLayout": "single-agent-starter",
            "generationMode": "manifest-only",
            "outputRoot": f"starter/{agent_slug}",
        },
        "model": model_profile(doc),
        "tools": tool_profile(doc),
        "validation": {
            "status": validation_status,
            "command": f"python3 scripts/validate_examples.py --format json {display_path(path)}",
            "errors": errors,
        },
        "plannedFiles": planned,
        "dryRunFileManifest": dry_run_file_manifest(path, agent_slug, planned, gates, validation_status),
        "blockedGatesBeforeGeneration": gates,
        "nonGoals": [
            "Do not write starter project files from this command.",
            "Do not install dependencies or create virtual environments.",
            "Do not call providers, local models, MCP servers, wallets, facilitators, or payment rails.",
            "Do not embed credentials, raw prompts, private task bodies, or settlement payloads.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--single", action="store_true", help="Emit one manifest object instead of a list.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    if args.single and len(paths) != 1:
        print("--single requires exactly one ADL path", file=sys.stderr)
        return 2
    manifests = [plan_for(path) for path in paths]
    payload: object = manifests[0] if args.single else manifests
    print(json.dumps(payload, indent=2))
    return 1 if any(not manifest["supported"] for manifest in manifests) else 0


if __name__ == "__main__":
    sys.exit(main())
