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
    ROOT / "examples" / "mcp-readonly-agent.yaml",
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
EVE_BOUNDARY_FLAGS = {
    **BOUNDARY_FLAGS,
    "deploymentAllowed": False,
}
BASE_TEMPLATE_CONTRACTS = [
    {
        "templateId": "starter.readme",
        "pathSuffix": "README.md",
        "inputRefs": ["metadata.name", "model.capability", "harness.runtime"],
        "status": "review-only",
        "purpose": "Document the static starter review package, blocked gates, and human handoff notes.",
    },
    {
        "templateId": "starter.adl_copy",
        "pathSuffix": "agent.adl.yaml",
        "inputRefs": ["<source-adl>"],
        "status": "review-only",
        "purpose": "Preserve the source ADL as the canonical contract for later reviewed generation.",
    },
    {
        "templateId": "starter.python_harness",
        "pathSuffix": "src/agent_harness.py",
        "inputRefs": ["metadata.name", "model", "harness.runtime", "harness.tools"],
        "status": "placeholder-only",
        "purpose": "Describe the future local harness entry point without creating runnable code.",
    },
    {
        "templateId": "starter.static_contract_test",
        "pathSuffix": "tests/test_static_contract.py",
        "inputRefs": ["boundaryFlags", "validation.status", "blockedGatesBeforeGeneration"],
        "status": "placeholder-only",
        "purpose": "Pin static boundary assertions before any generator can write executable files.",
    },
    {
        "templateId": "starter.env_example",
        "pathSuffix": ".env.example",
        "inputRefs": [],
        "status": "withheld",
        "purpose": "Withhold environment variable templates until a separate credential policy review.",
    },
]
SAFETY_POLICY_RULES = [
    {
        "policyId": "no-dependency-install",
        "requestId": "install-runtime-dependencies",
        "request": "Install package manager dependencies for the generated starter.",
        "decision": "deny",
        "risk": "dependency-install",
        "reason": "Report-only starter planning cannot run package managers or create virtual environments.",
    },
    {
        "policyId": "no-external-network-tool-execution",
        "requestId": "enable-external-tool-network",
        "request": "Enable generated starter tools to call external network services.",
        "decision": "deny",
        "risk": "external-network-tool-execution",
        "reason": "Tool execution remains limited to deterministic local fixtures and no network access.",
    },
    {
        "policyId": "no-mcp-invocation",
        "requestId": "resolve-live-mcp-server",
        "request": "Resolve or invoke a live MCP server during starter generation.",
        "decision": "deny",
        "risk": "mcp-invocation",
        "reason": "MCP resolution and invocation require a separate reviewed runtime lane.",
    },
    {
        "policyId": "no-provider-model-local-execution",
        "requestId": "call-provider-or-local-model",
        "request": "Call a provider API, execute a model, or probe a local model endpoint from the starter.",
        "decision": "deny",
        "risk": "provider-model-local-execution",
        "reason": "Provider calls, model execution, and local model probes stay blocked until a reviewed runtime adapter exists.",
    },
    {
        "policyId": "no-credential-material",
        "requestId": "embed-secret-material",
        "request": "Write API keys, tokens, raw prompts, or private task bodies into starter files.",
        "decision": "deny",
        "risk": "credential-or-private-material",
        "reason": "Starter manifests may reference symbolic input names only; sensitive values are never stored.",
    },
    {
        "policyId": "no-wallet-payment-settlement-access",
        "requestId": "wire-payment-settlement",
        "request": "Configure wallets, facilitators, payment rails, reputation settlement, or receipt submission.",
        "decision": "deny",
        "risk": "wallet-payment-settlement",
        "reason": "Payment and reputation semantics remain metadata-only until a separate approved rail exists.",
    },
    {
        "policyId": "no-deployment",
        "requestId": "deploy-generated-starter",
        "request": "Deploy, publish, or register the generated starter as a live service.",
        "decision": "deny",
        "risk": "deployment",
        "reason": "Starter planning is static and cannot deploy or register live runtime endpoints.",
    },
    {
        "policyId": "no-production-config-mutation",
        "requestId": "mutate-production-config",
        "request": "Update production gateway, cron, environment, or service configuration for the starter.",
        "decision": "deny",
        "risk": "production-config-mutation",
        "reason": "Production config mutation is outside report-only fixture scope.",
    },
]
READY_SAFETY_REQUEST = {
    "requestId": "review-static-starter-manifest",
    "request": "Review the static starter manifest, planned paths, and withheld gates without writing files.",
    "decision": "allow",
    "risk": "static-review",
    "reason": "Manifest-only review preserves all boundary flags and performs no runtime action.",
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


def template_contracts(agent_slug: str, doc: dict, gates: list[dict]) -> list[dict]:
    contracts = [
        {
            "templateId": template["templateId"],
            "plannedPath": f"starter/{agent_slug}/{template['pathSuffix']}",
            "status": template["status"],
            "requiredInputs": template["inputRefs"],
            "blockedGateIds": [gate["id"] for gate in gates],
            "writesFiles": False,
            "installsDependencies": False,
            "runtimeExecutionAllowed": False,
            "purpose": template["purpose"],
        }
        for template in BASE_TEMPLATE_CONTRACTS
    ]
    harness = doc.get("harness") or {}
    if harness.get("toolFixtures"):
        contracts.append(
            {
                "templateId": "starter.local_tool_fixtures",
                "plannedPath": f"starter/{agent_slug}/fixtures/tools.json",
                "status": "review-only",
                "requiredInputs": ["harness.toolFixtures"],
                "blockedGateIds": [gate["id"] for gate in gates],
                "writesFiles": False,
                "installsDependencies": False,
                "runtimeExecutionAllowed": False,
                "purpose": "Package deterministic local tool fixtures as data only, with no network or MCP access.",
            }
        )
    if harness.get("policies") or harness.get("evalGates"):
        contracts.append(
            {
                "templateId": "starter.policy_eval_gate_tests",
                "plannedPath": f"starter/{agent_slug}/tests/test_policy_eval_gates.py",
                "status": "placeholder-only",
                "requiredInputs": ["harness.policies", "harness.evalGates"],
                "blockedGateIds": [gate["id"] for gate in gates],
                "writesFiles": False,
                "installsDependencies": False,
                "runtimeExecutionAllowed": False,
                "purpose": "Describe policy and eval assertions without running the starter harness.",
            }
        )
    return contracts


def template_contract_fixture(
    source: Path,
    agent_slug: str,
    contracts: list[dict],
    validation_status: str,
) -> dict:
    status_counts: dict[str, int] = {}
    for contract in contracts:
        status = contract["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "format": "starter-code-template-contract-fixture",
        "source": display_path(source),
        "outputRoot": f"starter/{agent_slug}",
        "manifestOnly": True,
        "writesFiles": False,
        "validationStatus": validation_status,
        "templateCount": len(contracts),
        "templateIds": [contract["templateId"] for contract in contracts],
        "plannedPaths": [contract["plannedPath"] for contract in contracts],
        "statusCounts": status_counts,
        "requiredInputRefs": sorted({ref for contract in contracts for ref in contract["requiredInputs"]}),
        "contractNonGoalIds": [
            "no-template-rendering",
            "no-file-writes",
            "no-dependency-install",
            "no-runtime-execution",
            "no-provider-model-mcp-payment-calls",
            "no-sensitive-payloads",
        ],
    }


def starter_safety_policy_fixture(
    source: Path,
    agent_slug: str,
    gates: list[dict],
    validation_status: str,
) -> dict:
    return {
        "format": "starter-code-safety-policy-fixture",
        "source": display_path(source),
        "outputRoot": f"starter/{agent_slug}",
        "manifestOnly": True,
        "validationStatus": validation_status,
        **BOUNDARY_FLAGS,
        "readyRequest": READY_SAFETY_REQUEST,
        "unsafeRequests": [
            {
                **rule,
                "blockedGateIds": [gate["id"] for gate in gates],
                "allowed": False,
            }
            for rule in SAFETY_POLICY_RULES
        ],
        "policyNonGoalIds": [
            "no-file-writes",
            "no-dependency-install",
            "no-external-network-tool-execution",
            "no-mcp-invocation",
            "no-provider-model-local-execution",
            "no-credential-material",
            "no-wallet-payment-settlement-access",
            "no-deployment",
            "no-production-config-mutation",
        ],
    }


def preview_bundle_fixture(
    source: Path,
    agent_slug: str,
    planned: list[dict],
    contracts: list[dict],
    safety_policy: dict,
    gates: list[dict],
    validation_status: str,
    errors: list[str],
) -> dict:
    contract_by_path = {contract["plannedPath"]: contract for contract in contracts}
    unsafe_requests = safety_policy["unsafeRequests"]
    return {
        "format": "starter-code-preview-bundle-fixture",
        "source": display_path(source),
        "outputRoot": f"starter/{agent_slug}",
        "bundleStatus": "ready-for-static-review" if validation_status == "pass" else "blocked-invalid-adl",
        "manifestOnly": True,
        **BOUNDARY_FLAGS,
        "validationStatus": validation_status,
        "validationErrorCount": len(errors),
        "plannedFilePreviews": [
            {
                "path": item["path"],
                "status": item["status"],
                "templateId": contract_by_path.get(item["path"], {}).get("templateId"),
                "writesFile": False,
                "installsDependencies": False,
                "purpose": item["purpose"],
            }
            for item in planned
        ],
        "templateContractIds": [contract["templateId"] for contract in contracts],
        "templateContractCount": len(contracts),
        "blockedGateIds": [gate["id"] for gate in gates],
        "blockedGates": gates,
        "safetyPolicyState": {
            "readyRequestId": safety_policy["readyRequest"]["requestId"],
            "readyDecision": safety_policy["readyRequest"]["decision"],
            "unsafeCount": len(unsafe_requests),
            "unsafeAllowed": any(request["allowed"] for request in unsafe_requests),
            "unsafePolicyIds": [request["policyId"] for request in unsafe_requests],
            "unsafeRisks": [request["risk"] for request in unsafe_requests],
        },
        "failClosed": {
            "invalidAdlBlocksPlannedFiles": validation_status == "fail" and not planned,
            "unsafeRequestsDenied": all(
                request["decision"] == "deny" and request["allowed"] is False
                for request in unsafe_requests
            ),
            "liveClaimsAllowed": False,
            "writesFilesAllowed": False,
            "installsDependenciesAllowed": False,
        },
        "previewNonGoalIds": [
            "no-file-writes",
            "no-template-rendering",
            "no-dependency-install",
            "no-runtime-execution",
            "no-provider-model-mcp-payment-calls",
            "no-sensitive-payloads",
        ],
    }


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


def eve_snake(value: str | None) -> str:
    if not value:
        return "item"
    slug = "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")
    return slug or "item"


def eve_project_skeleton_files(agent_slug: str, doc: dict) -> list[dict]:
    harness = doc.get("harness") or {}
    files = [
        {
            "path": f"eve/{agent_slug}/agent/instructions.md",
            "eveSlot": "agent/instructions.md",
            "source": "harness.instructions.inline"
            if (harness.get("instructions") or {}).get("inline")
            else "harness.instructions.path",
            "status": "static-content-plan",
        },
        {
            "path": f"eve/{agent_slug}/agent/agent.ts",
            "eveSlot": "agent/agent.ts",
            "source": "model + static boundary metadata",
            "status": "typescript-generation-blocked",
        },
        {
            "path": f"eve/{agent_slug}/agent/reddiagent.metadata.json",
            "eveSlot": "agent/reddiagent.metadata.json",
            "source": "ReddiAgent metadata-only sections",
            "status": "metadata-only",
        },
    ]
    for tool in harness.get("tools", []) or []:
        tool_id = tool.get("id") or tool.get("toolName") or "tool"
        if tool.get("type") == "mcp":
            files.append(
                {
                    "path": f"eve/{agent_slug}/agent/connections/{eve_snake(tool_id)}.ts",
                    "eveSlot": "agent/connections/",
                    "source": f"harness.tools.{tool_id}",
                    "status": "metadata-only",
                    "unsupportedFeature": "mcp_runtime_invocation",
                }
            )
        else:
            files.append(
                {
                    "path": f"eve/{agent_slug}/agent/tools/{eve_snake(tool_id)}.ts",
                    "eveSlot": "agent/tools/",
                    "source": f"harness.tools.{tool_id}",
                    "status": "static-stub-plan",
                }
            )
    for gate in harness.get("evalGates", []) or []:
        gate_id = gate.get("id") or "eval"
        files.append(
            {
                "path": f"eve/{agent_slug}/evals/{eve_snake(gate_id)}.eval.ts",
                "eveSlot": "evals/",
                "source": f"harness.evalGates.{gate_id}",
                "status": "static-eval-plan",
            }
        )
    return files


def eve_project_skeleton_dry_run_manifest(
    source: Path,
    agent_slug: str,
    doc: dict,
    validation_status: str,
    errors: list[str],
) -> dict:
    harness = doc.get("harness") or {}
    files = [] if errors else eve_project_skeleton_files(agent_slug, doc)
    status_counts: dict[str, int] = {}
    for item in files:
        status = item["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    has_function_tools = any((tool.get("type") != "mcp") for tool in harness.get("tools", []) or [])
    has_mcp_tools = any((tool.get("type") == "mcp") for tool in harness.get("tools", []) or [])
    return {
        "format": "eve-project-skeleton-dry-run-manifest-fixture",
        "issue": 203,
        "source": display_path(source),
        "outputRoot": f"eve/{agent_slug}",
        "manifestOnly": True,
        "validationStatus": validation_status,
        **EVE_BOUNDARY_FLAGS,
        "fileCount": len(files),
        "paths": [item["path"] for item in files],
        "statusCounts": status_counts,
        "slotSummary": [
            {
                "slot": "agent/instructions.md",
                "planned": validation_status == "pass",
                "source": "harness.instructions",
            },
            {
                "slot": "agent/tools/",
                "planned": validation_status == "pass" and has_function_tools,
                "source": "harness.tools[type=function]",
            },
            {
                "slot": "agent/skills/",
                "planned": False,
                "source": None,
                "reason": "ADL v0.1 has no native eve skills package source.",
            },
            {
                "slot": "agent/connections/",
                "planned": validation_status == "pass" and has_mcp_tools,
                "source": "harness.tools[type=mcp]",
            },
            {
                "slot": "agent/schedules/",
                "planned": False,
                "source": None,
                "reason": "ADL v0.1 has no schedule declaration source.",
            },
            {
                "slot": "evals/",
                "planned": validation_status == "pass" and bool(harness.get("evalGates")),
                "source": "harness.evalGates",
            },
        ],
        "blockedGateIds": [
            "eve-typescript-generation-review",
            "eve-dependency-install-review",
            "eve-deployment-review",
        ],
        "blockedGatesBeforeGeneration": [
            {
                "id": "eve-typescript-generation-review",
                "status": "required",
                "reason": "Runnable eve TypeScript generation requires a separate reviewed implementation lane.",
            },
            {
                "id": "eve-dependency-install-review",
                "status": "required",
                "reason": "No eve package manager dependencies are installed in dry-run manifest mode.",
            },
            {
                "id": "eve-deployment-review",
                "status": "required",
                "reason": "No eve dev server, deployment, or public publishing is allowed from this fixture.",
            },
        ],
        "nonGoalIds": [
            "no-eve-project-file-writes",
            "no-eve-typescript-generation",
            "no-eve-dependency-install",
            "no-eve-dev-server-or-deployment",
            "no-provider-model-mcp-payment-calls",
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
    contracts = [] if errors else template_contracts(agent_slug, doc, gates)
    safety_policy = starter_safety_policy_fixture(path, agent_slug, gates, validation_status)
    preview_bundle = preview_bundle_fixture(
        path,
        agent_slug,
        planned,
        contracts,
        safety_policy,
        gates,
        validation_status,
        errors,
    )
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
        "eveProjectSkeletonDryRunManifest": eve_project_skeleton_dry_run_manifest(
            path,
            agent_slug,
            doc,
            validation_status,
            errors,
        ),
        "templateContracts": contracts,
        "templateContractFixture": template_contract_fixture(path, agent_slug, contracts, validation_status),
        "starterSafetyPolicy": safety_policy,
        "previewBundle": preview_bundle,
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
