#!/usr/bin/env python3
"""Materialize local-only provider adapter stubs for sandbox review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import yaml

from run_local_agent import display_path, validate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FIXTURE = ROOT / "tests" / "fixtures" / "provider-adapter-codegen-manifest.json"
POLICY_FIXTURE = ROOT / "tests" / "fixtures" / "provider-adapter-sandbox-policy.json"

BOUNDARIES = {
    "writesFiles": True,
    "hostedProviderModelApiCalls": False,
    "networkAccess": False,
    "credentialAccess": False,
    "installsDependencies": False,
    "runtimeExecutionAllowed": False,
    "mcpInvocation": False,
    "paymentAccess": False,
    "devnetAccess": False,
    "mainnetAccess": False,
    "deploymentAllowed": False,
    "packagePublishingAllowed": False,
    "externalSpendUsd": 0,
}

BLOCKED_REQUESTS = {
    "request_credential": {
        "policyId": "no-credential-access",
        "reason": "adapter sandbox stubs may reference credential names only and cannot read or require secrets",
    },
    "request_provider_call": {
        "policyId": "no-hosted-provider-model-call",
        "reason": "adapter sandbox beta proves file materialization only and cannot call hosted providers or local models",
    },
    "request_network": {
        "policyId": "no-network-or-provider-call",
        "reason": "network and provider call requests are blocked before any files are written",
    },
    "request_dependency_install": {
        "policyId": "no-dependency-install",
        "reason": "provider SDK and package manager installs are outside the local-only sandbox",
    },
    "request_mainnet": {
        "policyId": "no-mainnet",
        "reason": "mainnet deployment or execution remains blocked",
    },
}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def load_adl(path: Path) -> dict[str, Any]:
    resolved = path if path.is_absolute() else ROOT / path
    return yaml.safe_load(resolved.read_text())


def slugify(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")


def deny(status: str, reason: str, *, blocked_requests: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "format": "provider-adapter-generated-code-sandbox-beta-artifact",
        "issue": 243,
        "status": status,
        "reason": reason,
        "writesFiles": False,
        "boundaries": {**BOUNDARIES, "writesFiles": False},
        "blockedRequests": blocked_requests or [],
    }


def request_denials(args: argparse.Namespace) -> list[dict[str, Any]]:
    denials = []
    for attr, template in BLOCKED_REQUESTS.items():
        if getattr(args, attr):
            denials.append(
                {
                    "requestId": attr.replace("_", "-"),
                    "policyId": template["policyId"],
                    "allowed": False,
                    "reason": template["reason"],
                }
            )
    return denials


def resolve_output_dir(path: Path | None) -> tuple[Path | None, dict[str, Any] | None]:
    if path is None:
        return None, deny("blocked-missing-output-dir", "--output-dir is required")
    resolved = path.expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        return None, deny(
            "blocked-unsafe-output-path",
            "output directory must be an explicit temp/review directory outside the repository",
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved, None


def resolve_package_root(output_dir: Path, package_dir: str) -> tuple[Path | None, dict[str, Any] | None]:
    if not package_dir or Path(package_dir).is_absolute():
        return None, deny("blocked-unsafe-output-path", "package directory must be a relative path")
    package_root = (output_dir / package_dir).resolve()
    if output_dir != package_root and output_dir not in package_root.parents:
        return None, deny("blocked-unsafe-output-path", "package directory attempted path traversal")
    if package_root.exists() and any(package_root.iterdir()):
        return None, deny(
            "blocked-unsafe-output-path",
            "package directory already exists and is not empty",
        )
    return package_root, None


def provider_manifest(manifest: dict[str, Any], target: str) -> dict[str, Any] | None:
    for item in manifest.get("targetManifests", []):
        if item.get("target") == target:
            return item
    return None


def validate_policy(policy: dict[str, Any], target: str) -> dict[str, Any] | None:
    if policy.get("schemaVersion") != "provider-adapter-sandbox-policy.v0.1":
        return deny("blocked-missing-provider-policy", "provider sandbox policy fixture has an unsupported schema")
    if target not in policy.get("approvedTargets", []):
        return deny("blocked-missing-provider-policy", f"provider target {target!r} is not approved by policy")
    required_flags = {
        "allowHostedProviderCalls": False,
        "allowCredentialAccess": False,
        "allowNetworkAccess": False,
        "allowDependencyInstall": False,
        "allowMainnet": False,
    }
    for key, expected in required_flags.items():
        if policy.get("controls", {}).get(key) is not expected:
            return deny("blocked-missing-provider-policy", f"provider sandbox policy must set {key}={expected}")
    return None


def adapter_plan(doc: dict[str, Any], target: str, manifest: dict[str, Any]) -> dict[str, Any]:
    model = doc.get("model") or {}
    providers = model.get("providers") or {}
    harness = doc.get("harness") or {}
    return {
        "target": target,
        "manifestId": manifest["manifestId"],
        "manifestStatusAtGeneration": manifest["manifestStatus"],
        "agentName": doc["metadata"]["name"],
        "modelMetadataPlaceholders": {
            "preferredProvider": providers.get("preferred"),
            "fallbackProviders": providers.get("fallbacks", []),
            "modelId": f"{target}/<reviewed-model-id>",
            "providerSdkVersion": "<not-installed>",
            "credentialRef": "<withheld>",
        },
        "promptMetadataPlaceholders": {
            "systemPromptHash": stable_hash(harness.get("instructions", {}).get("inline", "")),
            "rawPromptStored": False,
            "taskBodyStored": False,
        },
        "budgetGates": [
            {"id": "max-prompt-tokens", "status": "placeholder", "limit": "<review-required>"},
            {"id": "max-completion-tokens", "status": "placeholder", "limit": "<review-required>"},
            {"id": "max-usd", "status": "placeholder", "limit": 0},
        ],
        "evalGates": [
            {"id": gate["id"], "type": gate["type"], "status": "placeholder"}
            for gate in harness.get("evalGates", [])
        ],
        "providerPolicy": {
            "hostedProviderCallsAllowed": False,
            "credentialAccessAllowed": False,
            "networkAccessAllowed": False,
            "dependencyInstallAllowed": False,
            "mainnetAllowed": False,
        },
    }


def file_index(package_root: Path, output_dir: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(item for item in package_root.rglob("*") if item.is_file()):
        rel_output = path.relative_to(output_dir).as_posix()
        files.append(
            {
                "path": rel_output,
                "bytes": path.stat().st_size,
                "sha256": stable_hash(path.read_text()),
            }
        )
    return files


def write_stubs(
    package_root: Path,
    output_dir: Path,
    doc: dict[str, Any],
    target: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    package_root.mkdir(parents=True, exist_ok=False)
    adapter_dir = package_root / "adapters" / target
    test_dir = package_root / "tests"
    adapter_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)

    plan = adapter_plan(doc, target, manifest)
    (package_root / "README.md").write_text(
        "\n".join(
            [
                f"# {doc['metadata']['name']} Provider Adapter Sandbox",
                "",
                "Local-only generated stub package for review.",
                "",
                "- Hosted provider/model API calls: blocked",
                "- Credential access: blocked",
                "- Dependency installs: blocked",
                "- Runtime execution: blocked",
                "- Mainnet: blocked",
                "",
            ]
        )
    )
    (adapter_dir / "adapter_manifest.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (adapter_dir / "adapter_stub.py").write_text(
        "\n".join(
            [
                '"""Local-only provider adapter stub generated for review."""',
                "",
                "BOUNDARIES = {",
                '    "hostedProviderModelApiCalls": False,',
                '    "credentialAccess": False,',
                '    "networkAccess": False,',
                '    "installsDependencies": False,',
                '    "mainnetAccess": False,',
                "}",
                "",
                "",
                "def describe_adapter():",
                f'    return {{"target": {target!r}, "status": "stub-only", "boundaries": BOUNDARIES}}',
                "",
            ]
        )
    )
    (test_dir / "test_static_provider_adapter_contract.py").write_text(
        "\n".join(
            [
                "import sys",
                "from pathlib import Path",
                "",
                "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
                "",
                "from adapters.%s.adapter_stub import describe_adapter" % target,
                "",
                "",
                "def test_provider_adapter_stub_boundaries():",
                "    doc = describe_adapter()",
                "    assert doc['status'] == 'stub-only'",
                "    assert doc['boundaries']['hostedProviderModelApiCalls'] is False",
                "    assert doc['boundaries']['credentialAccess'] is False",
                "    assert doc['boundaries']['networkAccess'] is False",
                "    assert doc['boundaries']['installsDependencies'] is False",
                "    assert doc['boundaries']['mainnetAccess'] is False",
                "",
            ]
        )
    )
    return {
        "packageRoot": str(package_root),
        "fileCount": len(file_index(package_root, output_dir)),
        "files": file_index(package_root, output_dir),
    }


def cleanup(package_root: Path, delete_after: bool) -> list[dict[str, Any]]:
    transcript = [
        {
            "step": "prepare-delete",
            "command": f"rm -rf {package_root}",
            "executed": False,
            "reason": "cleanup command recorded before optional deletion",
        }
    ]
    if delete_after:
        shutil.rmtree(package_root)
        transcript.append(
            {
                "step": "delete-generated-package",
                "command": f"rm -rf {package_root}",
                "executed": True,
                "exitCode": 0,
            }
        )
    return transcript


def build_artifact(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    denials = request_denials(args)
    if denials:
        return 3, deny("blocked-unsafe-request", "unsafe request denied before generation", blocked_requests=denials)

    output_dir, output_error = resolve_output_dir(args.output_dir)
    if output_error:
        return 2, output_error
    assert output_dir is not None

    adl_path = Path(args.adl)
    doc = load_adl(adl_path)
    errors = validate(doc)
    if errors:
        return 1, {
            **deny("blocked-invalid-adl", "ADL validation failed before generation"),
            "adl": display_path((ROOT / adl_path).resolve()),
            "validation": {"status": "fail", "errors": errors},
        }

    policy = load_json(args.provider_policy)
    policy_error = validate_policy(policy, args.target)
    if policy_error:
        return 2, policy_error

    manifest_fixture = load_json(args.manifest_fixture)
    manifest = provider_manifest(manifest_fixture, args.target)
    if manifest is None:
        return 2, deny("blocked-missing-provider-policy", f"no adapter manifest fixture for {args.target!r}")

    package_dir = args.package_dir or f"{slugify(doc['metadata']['name'])}-{args.target}-adapter-sandbox"
    package_root, package_error = resolve_package_root(output_dir, package_dir)
    if package_error:
        return 2, package_error
    assert package_root is not None

    generated = write_stubs(package_root, output_dir, doc, args.target, manifest)
    cleanup_transcript = cleanup(package_root, args.delete_after)
    return 0, {
        "format": "provider-adapter-generated-code-sandbox-beta-artifact",
        "issue": 243,
        "status": "generated-local-sandbox-beta",
        "adl": display_path((ROOT / adl_path).resolve()),
        "target": args.target,
        "outputDir": str(output_dir),
        "packageDir": package_root.name,
        "writesFiles": True,
        "boundaries": BOUNDARIES,
        "adapterManifest": {
            "source": display_path((ROOT / args.manifest_fixture).resolve()),
            "manifestId": manifest["manifestId"],
            "manifestStatus": manifest["manifestStatus"],
            "plannedFileCount": len(manifest["plannedFiles"]),
            "generationAllowedInSourceManifest": manifest["generationAllowed"],
        },
        "providerPolicy": {
            "source": display_path((ROOT / args.provider_policy).resolve()),
            "approvedTargets": policy["approvedTargets"],
            "controls": policy["controls"],
        },
        "promptAndModelMetadataPlaceholders": adapter_plan(doc, args.target, manifest),
        "budgetAndEvalGates": {
            "budget": adapter_plan(doc, args.target, manifest)["budgetGates"],
            "evals": adapter_plan(doc, args.target, manifest)["evalGates"],
        },
        "generatedFileIndex": generated,
        "cleanupTranscript": cleanup_transcript,
        "costEvidence": {
            "hostedProviderCalls": 0,
            "hostedProviderModelApiCalls": False,
            "externalSpendUsd": 0,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adl", help="Approved ADL fixture to materialize adapter stubs from.")
    parser.add_argument("--target", choices=["openai", "anthropic", "gemini", "ollama", "langgraph"], default="openai")
    parser.add_argument("--manifest-fixture", type=Path, default=MANIFEST_FIXTURE)
    parser.add_argument("--provider-policy", type=Path, default=POLICY_FIXTURE)
    parser.add_argument("--output-dir", type=Path, required=False)
    parser.add_argument("--package-dir")
    parser.add_argument("--delete-after", action="store_true")
    parser.add_argument("--request-credential", action="store_true")
    parser.add_argument("--request-provider-call", action="store_true")
    parser.add_argument("--request-network", action="store_true")
    parser.add_argument("--request-dependency-install", action="store_true")
    parser.add_argument("--request-mainnet", action="store_true")
    return parser.parse_args(argv)


def main() -> int:
    code, artifact = build_artifact(parse_args(sys.argv[1:]))
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
