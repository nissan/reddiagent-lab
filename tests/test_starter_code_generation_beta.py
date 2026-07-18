#!/usr/bin/env python3
"""Check local starter-code generation beta guardrails."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "starter-code-generation-beta.json"


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/starter_code_plan.py", *args],
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


def normalized_fixture(artifact: dict) -> dict:
    copy = json.loads(json.dumps(artifact))
    copy["outputDir"] = "<temp-output-dir>"
    copy["generatedFileManifest"]["packageRoot"] = "<temp-output-dir>/simple-research-helper"
    copy["rollbackDeleteTranscript"][0]["command"] = "rm -rf <temp-output-dir>/simple-research-helper"
    return copy


def main() -> int:
    missing_output = run_command("--generate-beta", "examples/simple-agent.yaml")
    assert missing_output.returncode == 2
    assert "--output-dir is required" in missing_output.stderr

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-beta-") as temp:
        temp_path = Path(temp)
        generated = run_command(
            "--generate-beta",
            "--output-dir",
            str(temp_path),
            "examples/simple-agent.yaml",
        )
        assert generated.returncode == 0, generated.stderr
        artifact = load_stdout(generated)
        assert artifact["format"] == "starter-code-generation-beta-artifact"
        assert artifact["issue"] == 242
        assert artifact["status"] == "generated-local-beta"
        assert artifact["writesFiles"] is True
        assert artifact["networkAccess"] is False
        assert artifact["paymentAccess"] is False
        assert artifact["mcpInvocation"] is False
        assert artifact["installsDependencies"] is False
        assert artifact["packageDir"] == "simple-research-helper"
        assert artifact["blockedLiveClaims"] == {
            "dependencyInstall": False,
            "providerModelCall": False,
            "liveMcpInvocation": False,
            "walletPaymentSettlement": False,
            "mainnet": False,
            "deployment": False,
        }
        manifest = artifact["generatedFileManifest"]
        assert manifest["fileCount"] == 6
        assert_no_escape(temp_path, manifest["files"])
        paths = {item["path"]: item for item in manifest["files"]}
        assert set(paths) == {
            "simple-research-helper/.env.example",
            "simple-research-helper/README.md",
            "simple-research-helper/agent.adl.yaml",
            "simple-research-helper/src/agent_harness.py",
            "simple-research-helper/tests/test_policy_eval_gates.py",
            "simple-research-helper/tests/test_static_contract.py",
        }
        assert paths["simple-research-helper/src/agent_harness.py"]["templateId"] == "starter.python_harness"
        assert "starter.python_harness" in artifact["templateIds"]
        assert "starter.policy_eval_gate_tests" in artifact["templateIds"]
        assert "provider-runtime-review" in artifact["safetyPolicyGates"]["blockedGateIds"]
        assert artifact["rollbackDeleteTranscript"][0]["step"] == "prepare-delete"
        assert artifact["rollbackDeleteTranscript"][0]["executed"] is False
        assert normalized_fixture(artifact) == json.loads(FIXTURE.read_text())
        package_root = temp_path / "simple-research-helper"
        assert (package_root / "README.md").exists()
        assert (package_root / "agent.adl.yaml").exists()
        assert (package_root / "src/agent_harness.py").exists()
        static_contract = subprocess.run(
            [PYTHON, "tests/test_static_contract.py"],
            cwd=package_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert static_contract.returncode == 0, static_contract.stderr
        harness = subprocess.run(
            [PYTHON, "src/agent_harness.py"],
            cwd=package_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert harness.returncode == 0, harness.stderr
        harness_payload = json.loads(harness.stdout)
        assert harness_payload["status"] == "local-deterministic-response"
        assert harness_payload["boundaryFlags"]["networkAccess"] is False

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-beta-") as temp:
        deleted = run_command(
            "--generate-beta",
            "--delete-after",
            "--output-dir",
            temp,
            "examples/simple-agent.yaml",
        )
        assert deleted.returncode == 0, deleted.stderr
        deleted_artifact = load_stdout(deleted)
        assert deleted_artifact["rollbackDeleteTranscript"][1]["executed"] is True
        assert deleted_artifact["rollbackDeleteTranscript"][1]["exitCode"] == 0
        assert not Path(deleted_artifact["generatedFileManifest"]["packageRoot"]).exists()

    traversal = run_command(
        "--generate-beta",
        "--output-dir",
        tempfile.gettempdir(),
        "--package-dir",
        "../escape",
        "examples/simple-agent.yaml",
    )
    assert traversal.returncode == 2
    assert "path traversal" in traversal.stderr

    invalid = run_command(
        "--generate-beta",
        "--output-dir",
        tempfile.gettempdir(),
        "examples/invalid/missing-instructions.yaml",
    )
    assert invalid.returncode == 1
    invalid_artifact = load_stdout(invalid)
    assert invalid_artifact["status"] == "blocked-invalid-adl"
    assert invalid_artifact["writesFiles"] is False
    assert invalid_artifact["validation"]["status"] == "fail"

    blocked_flags = [
        ("--request-dependency-install", "no-dependency-install"),
        ("--request-provider-call", "no-provider-model-local-execution"),
        ("--request-live-mcp", "no-mcp-invocation"),
        ("--request-live-payment", "no-wallet-payment-settlement-access"),
        ("--request-mainnet", "no-mainnet"),
    ]
    for flag, policy_id in blocked_flags:
        blocked = run_command(
            "--generate-beta",
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

    print("PASS starter code generation beta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
