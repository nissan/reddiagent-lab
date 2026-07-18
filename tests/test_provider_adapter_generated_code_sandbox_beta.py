#!/usr/bin/env python3
"""Check provider adapter generated-code sandbox beta guardrails."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "provider-adapter-generated-code-sandbox-beta.json"


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/provider_adapter_generated_code_sandbox_beta.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_stdout(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def assert_no_escape(root: Path, files: list[dict]) -> None:
    resolved_root = root.resolve()
    for item in files:
        path = (root / item["path"]).resolve()
        assert resolved_root == path or resolved_root in path.parents, item["path"]


def normalize(artifact: dict) -> dict:
    copy = json.loads(json.dumps(artifact))
    copy["outputDir"] = "<temp-output-dir>"
    copy["generatedFileIndex"]["packageRoot"] = "<temp-output-dir>/simple-research-helper-openai-adapter-sandbox"
    for item in copy["cleanupTranscript"]:
        item["command"] = item["command"].replace(
            artifact["outputDir"], "<temp-output-dir>"
        )
    return copy


def main() -> int:
    missing_output = run_command("examples/simple-agent.yaml")
    assert missing_output.returncode == 2
    assert load_stdout(missing_output)["status"] == "blocked-missing-output-dir"

    with tempfile.TemporaryDirectory(prefix="reddiagent-provider-adapter-beta-") as temp:
        temp_path = Path(temp)
        generated = run_command(
            "--output-dir",
            str(temp_path),
            "--delete-after",
            "examples/simple-agent.yaml",
        )
        assert generated.returncode == 0, generated.stderr
        artifact = load_stdout(generated)
        assert artifact["format"] == "provider-adapter-generated-code-sandbox-beta-artifact"
        assert artifact["issue"] == 243
        assert artifact["status"] == "generated-local-sandbox-beta"
        assert artifact["target"] == "openai"
        assert artifact["writesFiles"] is True
        assert artifact["boundaries"]["hostedProviderModelApiCalls"] is False
        assert artifact["boundaries"]["credentialAccess"] is False
        assert artifact["boundaries"]["networkAccess"] is False
        assert artifact["boundaries"]["installsDependencies"] is False
        assert artifact["boundaries"]["mainnetAccess"] is False
        assert artifact["adapterManifest"]["manifestId"] == "openai-provider-adapter-codegen-manifest"
        assert artifact["adapterManifest"]["generationAllowedInSourceManifest"] is False
        assert artifact["providerPolicy"]["controls"]["allowHostedProviderCalls"] is False
        assert artifact["providerPolicy"]["controls"]["allowCredentialAccess"] is False
        assert artifact["promptAndModelMetadataPlaceholders"]["modelMetadataPlaceholders"]["credentialRef"] == "<withheld>"
        assert artifact["promptAndModelMetadataPlaceholders"]["promptMetadataPlaceholders"]["rawPromptStored"] is False
        assert artifact["budgetAndEvalGates"]["budget"][0]["status"] == "placeholder"
        assert artifact["budgetAndEvalGates"]["evals"][0]["id"] == "has-answer"
        assert artifact["costEvidence"] == {
            "externalSpendUsd": 0,
            "hostedProviderCalls": 0,
            "hostedProviderModelApiCalls": False,
        }
        manifest = artifact["generatedFileIndex"]
        assert manifest["fileCount"] == 4
        assert_no_escape(temp_path, manifest["files"])
        paths = {item["path"] for item in manifest["files"]}
        assert paths == {
            "simple-research-helper-openai-adapter-sandbox/README.md",
            "simple-research-helper-openai-adapter-sandbox/adapters/openai/adapter_manifest.json",
            "simple-research-helper-openai-adapter-sandbox/adapters/openai/adapter_stub.py",
            "simple-research-helper-openai-adapter-sandbox/tests/test_static_provider_adapter_contract.py",
        }
        assert artifact["cleanupTranscript"][0]["executed"] is False
        assert artifact["cleanupTranscript"][1]["executed"] is True
        assert not Path(artifact["generatedFileIndex"]["packageRoot"]).exists()
        assert normalize(artifact) == json.loads(FIXTURE.read_text())

    with tempfile.TemporaryDirectory(prefix="reddiagent-provider-adapter-beta-") as temp:
        retained = run_command(
            "--output-dir",
            temp,
            "examples/simple-agent.yaml",
        )
        assert retained.returncode == 0, retained.stderr
        retained_artifact = load_stdout(retained)
        package_root = Path(retained_artifact["generatedFileIndex"]["packageRoot"])
        assert package_root.exists()
        static_contract = subprocess.run(
            [PYTHON, "tests/test_static_provider_adapter_contract.py"],
            cwd=package_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert static_contract.returncode == 0, static_contract.stderr

    missing_policy = run_command(
        "--output-dir",
        tempfile.gettempdir(),
        "--provider-policy",
        "tests/fixtures/provider-adapter-codegen-manifest.json",
        "examples/simple-agent.yaml",
    )
    assert missing_policy.returncode == 2
    assert load_stdout(missing_policy)["status"] == "blocked-missing-provider-policy"

    with tempfile.TemporaryDirectory(prefix="reddiagent-provider-adapter-unapproved-") as temp:
        unapproved_adl = Path(temp) / "simple-agent-copy.yaml"
        unapproved_adl.write_text((ROOT / "examples/simple-agent.yaml").read_text())
        unapproved = run_command(
            "--output-dir",
            tempfile.gettempdir(),
            str(unapproved_adl),
        )
        assert unapproved.returncode == 2
        unapproved_artifact = load_stdout(unapproved)
        assert unapproved_artifact["status"] == "blocked-unapproved-input"
        assert unapproved_artifact["writesFiles"] is False

    unapproved_manifest = run_command(
        "--output-dir",
        tempfile.gettempdir(),
        "--manifest-fixture",
        "tests/fixtures/provider-adapter-sandbox-policy.json",
        "examples/simple-agent.yaml",
    )
    assert unapproved_manifest.returncode == 2
    assert load_stdout(unapproved_manifest)["status"] == "blocked-unapproved-input"

    traversal = run_command(
        "--output-dir",
        tempfile.gettempdir(),
        "--package-dir",
        "../escape",
        "examples/simple-agent.yaml",
    )
    assert traversal.returncode == 2
    assert load_stdout(traversal)["status"] == "blocked-unsafe-output-path"

    repo_output = run_command(
        "--output-dir",
        str(ROOT / "tmp-provider-adapter-output"),
        "examples/simple-agent.yaml",
    )
    assert repo_output.returncode == 2
    assert load_stdout(repo_output)["status"] == "blocked-unsafe-output-path"

    blocked_flags = [
        ("--request-credential", "no-credential-access"),
        ("--request-provider-call", "no-hosted-provider-model-call"),
        ("--request-network", "no-network-or-provider-call"),
        ("--request-dependency-install", "no-dependency-install"),
        ("--request-mainnet", "no-mainnet"),
    ]
    for flag, policy_id in blocked_flags:
        blocked = run_command(
            "--output-dir",
            tempfile.gettempdir(),
            flag,
            "examples/simple-agent.yaml",
        )
        assert blocked.returncode == 3
        blocked_artifact = load_stdout(blocked)
        assert blocked_artifact["status"] == "blocked-unsafe-request"
        assert blocked_artifact["writesFiles"] is False
        assert blocked_artifact["blockedRequests"][0]["policyId"] == policy_id
        assert blocked_artifact["blockedRequests"][0]["allowed"] is False

    print("PASS provider adapter generated-code sandbox beta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
