#!/usr/bin/env python3
"""Static starter-code review manifest for ADL examples."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
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
GENERATION_BOUNDARY_FLAGS = {
    **BOUNDARY_FLAGS,
    "writesFiles": True,
}
BLOCKED_BETA_REQUESTS = {
    "request_dependency_install": "no-dependency-install",
    "request_provider_call": "no-provider-model-local-execution",
    "request_live_mcp": "no-mcp-invocation",
    "request_live_payment": "no-wallet-payment-settlement-access",
    "request_mainnet": "no-mainnet",
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


def stable_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


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


def safe_relative_package_dir(value: str, agent_slug: str) -> Path:
    raw = value or agent_slug
    path = Path(raw)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise ValueError("--package-dir must be a safe relative path with no path traversal")
    if str(path).strip() in {"", "."}:
        raise ValueError("--package-dir must name a package directory")
    return path


def require_output_dir(path: Path | None) -> Path:
    if path is None:
        raise ValueError("--output-dir is required for --generate-beta")
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError("--output-dir must be an existing explicit temporary directory")
    return resolved


def blocked_request_findings(args: argparse.Namespace) -> list[dict]:
    findings = []
    for attr, policy_id in BLOCKED_BETA_REQUESTS.items():
        if getattr(args, attr):
            findings.append(
                {
                    "requestFlag": attr.replace("_", "-"),
                    "policyId": policy_id,
                    "status": "blocked",
                    "allowed": False,
                }
            )
    return findings


def file_template_id(path: str) -> str:
    mapping = {
        "README.md": "starter.readme",
        "agent.adl.yaml": "starter.adl_copy",
        "src/agent_harness.py": "starter.python_harness",
        "tests/test_static_contract.py": "starter.static_contract_test",
        ".env.example": "starter.env_example",
        "fixtures/tools.json": "starter.local_tool_fixtures",
        "tests/test_policy_eval_gates.py": "starter.policy_eval_gate_tests",
    }
    for suffix, template_id in mapping.items():
        if path.endswith(suffix):
            return template_id
    raise ValueError(f"no template id for generated path: {path}")


def render_readme(plan: dict) -> str:
    return f"""# {plan["agent"]} starter

This local beta package was generated from `{plan["source"]}`.

It is runnable only as a deterministic local scaffold. It does not install
dependencies, call model providers, resolve MCP servers, use payment rails,
touch credentials, deploy, or use devnet/mainnet.

Run the local contract check:

```bash
python3 tests/test_static_contract.py
```
"""


def render_harness(plan: dict, doc: dict) -> str:
    instructions = ((doc.get("harness") or {}).get("instructions") or {}).get("inline", "")
    return f'''#!/usr/bin/env python3
"""Deterministic local starter harness for {plan["agent"]}."""

from __future__ import annotations

import json


AGENT_NAME = {plan["agent"]!r}
INSTRUCTIONS = {instructions!r}
BOUNDARY_FLAGS = {{
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
    "installsDependencies": False,
}}


def run_response(prompt: str) -> dict:
    return {{
        "agent": AGENT_NAME,
        "status": "local-deterministic-response",
        "prompt": prompt,
        "instructions": INSTRUCTIONS,
        "boundaryFlags": BOUNDARY_FLAGS,
    }}


if __name__ == "__main__":
    print(json.dumps(run_response("local beta smoke"), indent=2, sort_keys=True))
'''


def render_static_contract(plan: dict) -> str:
    return f'''#!/usr/bin/env python3
"""Static checks for the generated {plan["agent"]} starter package."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        "README.md",
        "agent.adl.yaml",
        "src/agent_harness.py",
        "tests/test_static_contract.py",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative
    assert not (ROOT / "package-lock.json").exists()
    assert not (ROOT / "node_modules").exists()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def render_policy_eval_tests(plan: dict, doc: dict) -> str:
    policies = (doc.get("harness") or {}).get("policies") or []
    gates = (doc.get("harness") or {}).get("evalGates") or []
    return f'''#!/usr/bin/env python3
"""Policy/eval gate inventory for {plan["agent"]}."""

POLICY_IDS = {json.dumps([policy.get("id") for policy in policies], sort_keys=True)}
EVAL_GATE_IDS = {json.dumps([gate.get("id") for gate in gates], sort_keys=True)}


def main() -> int:
    assert POLICY_IDS or EVAL_GATE_IDS
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def starter_file_contents(plan: dict, source_path: Path, doc: dict) -> dict[str, str]:
    contents = {
        "README.md": render_readme(plan),
        "agent.adl.yaml": source_path.read_text(),
        "src/agent_harness.py": render_harness(plan, doc),
        "tests/test_static_contract.py": render_static_contract(plan),
        ".env.example": "# No credentials are required for this local beta starter.\n",
    }
    harness = doc.get("harness") or {}
    if harness.get("toolFixtures"):
        contents["fixtures/tools.json"] = stable_json(harness["toolFixtures"])
    if harness.get("policies") or harness.get("evalGates"):
        contents["tests/test_policy_eval_gates.py"] = render_policy_eval_tests(plan, doc)
    return contents


def write_starter_package(plan: dict, source_path: Path, doc: dict, output_dir: Path, package_dir: Path) -> dict:
    package_root = (output_dir / package_dir).resolve()
    output_root = output_dir.resolve()
    if output_root != package_root and output_root not in package_root.parents:
        raise ValueError("resolved package directory escaped --output-dir")
    if package_root.exists():
        raise ValueError("package directory already exists; remove it or choose a fresh temp output")

    contents = starter_file_contents(plan, source_path, doc)
    generated_files = []
    for relative, content in sorted(contents.items()):
        target = package_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        stat = target.stat()
        generated_files.append(
            {
                "path": str((package_dir / relative).as_posix()),
                "templateId": file_template_id(str(package_dir / relative)),
                "bytes": stat.st_size,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )

    return {
        "packageRoot": str(package_root),
        "fileCount": len(generated_files),
        "files": generated_files,
    }


def generation_artifact(
    plan: dict,
    source_path: Path,
    output_dir: Path,
    package_dir: Path,
    generated_manifest: dict,
    delete_after: bool,
) -> dict:
    delete_command = f"rm -rf {generated_manifest['packageRoot']}"
    transcript = [
        {
            "step": "prepare-delete",
            "command": delete_command,
            "executed": False,
            "reason": "Generated package is left in temp output for local inspection by default.",
        }
    ]
    if delete_after:
        shutil.rmtree(generated_manifest["packageRoot"])
        transcript.append(
            {
                "step": "delete-temp-output",
                "command": delete_command,
                "executed": True,
                "exitCode": 0,
            }
        )
    return {
        "format": "starter-code-generation-beta-artifact",
        "issue": 242,
        "source": display_path(source_path),
        "agent": plan["agent"],
        "status": "generated-local-beta",
        **GENERATION_BOUNDARY_FLAGS,
        "outputDir": str(output_dir),
        "packageDir": str(package_dir.as_posix()),
        "generatedFileManifest": generated_manifest,
        "templateIds": sorted({item["templateId"] for item in generated_manifest["files"]}),
        "safetyPolicyGates": {
            "readyRequest": plan["starterSafetyPolicy"]["readyRequest"],
            "unsafeRequests": plan["starterSafetyPolicy"]["unsafeRequests"],
            "blockedGateIds": [gate["id"] for gate in plan["blockedGatesBeforeGeneration"]],
        },
        "blockedLiveClaims": {
            "dependencyInstall": False,
            "providerModelCall": False,
            "liveMcpInvocation": False,
            "walletPaymentSettlement": False,
            "mainnet": False,
            "deployment": False,
        },
        "rollbackDeleteTranscript": transcript,
    }


def generate_beta(args: argparse.Namespace) -> tuple[int, dict]:
    output_dir = require_output_dir(args.output_dir)
    blocked = blocked_request_findings(args)
    if blocked:
        return 3, {
            "format": "starter-code-generation-beta-artifact",
            "issue": 242,
            "status": "blocked-unsafe-request",
            **BOUNDARY_FLAGS,
            "blockedRequests": blocked,
        }
    if len(args.paths) != 1:
        raise ValueError("--generate-beta requires exactly one ADL path")
    source_path = args.paths[0]
    plan = plan_for(source_path)
    if not plan["supported"]:
        return 1, {
            "format": "starter-code-generation-beta-artifact",
            "issue": 242,
            "source": display_path(source_path),
            "status": "blocked-invalid-adl",
            **BOUNDARY_FLAGS,
            "validation": plan["validation"],
        }
    doc = read_adl(source_path)
    package_dir = safe_relative_package_dir(args.package_dir, slugify(plan["agent"]))
    generated_manifest = write_starter_package(plan, source_path, doc, output_dir, package_dir)
    return 0, generation_artifact(
        plan,
        source_path,
        output_dir,
        package_dir,
        generated_manifest,
        args.delete_after,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--single", action="store_true", help="Emit one manifest object instead of a list.")
    parser.add_argument("--generate-beta", action="store_true", help="Write a local beta starter package.")
    parser.add_argument("--output-dir", type=Path, help="Existing explicit temp output directory for beta generation.")
    parser.add_argument("--package-dir", default="", help="Safe relative package directory under --output-dir.")
    parser.add_argument("--delete-after", action="store_true", help="Delete generated temp package after artifact capture.")
    parser.add_argument("--request-dependency-install", action="store_true")
    parser.add_argument("--request-provider-call", action="store_true")
    parser.add_argument("--request-live-mcp", action="store_true")
    parser.add_argument("--request-live-payment", action="store_true")
    parser.add_argument("--request-mainnet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.generate_beta:
        try:
            code, payload = generate_beta(args)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(payload, indent=2, sort_keys=True))
        return code
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
