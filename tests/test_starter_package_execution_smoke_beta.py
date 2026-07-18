#!/usr/bin/env python3
"""Check local starter package execution smoke beta guardrails."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "starter-package-execution-smoke-beta.json"


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


def normalize_artifact(artifact: dict) -> dict:
    copy = json.loads(json.dumps(artifact))
    package_root = "<temp-output-dir>/simple-research-helper"
    copy["outputDir"] = "<temp-output-dir>"
    copy["generatedFileManifest"]["packageRoot"] = package_root
    copy["cleanupTranscript"][0]["command"] = f"rm -rf {package_root}"
    for command in copy["commandTranscript"]:
        command["cwd"] = package_root
        command["command"][0] = "<python>"
    return copy


def assert_no_escape(root: Path, artifact: dict) -> None:
    resolved_root = root.resolve()
    package_root = Path(artifact["generatedFileManifest"]["packageRoot"]).resolve()
    assert resolved_root == package_root or resolved_root in package_root.parents
    for item in artifact["generatedFileManifest"]["files"]:
        generated_path = (root / item["path"]).resolve()
        assert resolved_root == generated_path or resolved_root in generated_path.parents


def main() -> int:
    missing_output = run_command("--execution-smoke-beta", "examples/simple-agent.yaml")
    assert missing_output.returncode == 2
    assert "--output-dir is required" in missing_output.stderr

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
        temp_path = Path(temp)
        smoke = run_command(
            "--execution-smoke-beta",
            "--output-dir",
            str(temp_path),
            "examples/simple-agent.yaml",
        )
        assert smoke.returncode == 0, smoke.stderr
        artifact = load_stdout(smoke)
        assert artifact["format"] == "starter-package-execution-smoke-beta-artifact"
        assert artifact["issue"] == 244
        assert artifact["status"] == "passed"
        assert artifact["executionMode"] == "local-deterministic-smoke"
        assert artifact["localExecutionAllowed"] is True
        assert artifact["networkAccess"] is False
        assert artifact["paymentAccess"] is False
        assert artifact["mcpInvocation"] is False
        assert artifact["installsDependencies"] is False
        assert artifact["budgetEvidence"] == {
            "providerCalls": 0,
            "modelCalls": 0,
            "dependencyInstalls": 0,
            "networkRequests": 0,
            "mcpInvocations": 0,
            "paymentRailCalls": 0,
            "mainnetCalls": 0,
        }
        assert artifact["blockedLiveClaims"]["writeOutsideTempOutput"] is False
        assert [item["label"] for item in artifact["commandTranscript"]] == [
            "static-contract",
            "policy-eval-gates",
            "deterministic-harness",
        ]
        assert [item["status"] for item in artifact["commandTranscript"]] == ["pass", "pass", "pass"]
        harness_payload = json.loads(artifact["commandTranscript"][2]["stdout"])
        assert harness_payload["status"] == "local-deterministic-response"
        assert harness_payload["boundaryFlags"]["networkAccess"] is False
        assert artifact["evalEvidence"] == {
            "staticContract": "pass",
            "policyEvalGateInventory": "pass",
            "deterministicHarness": "pass",
        }
        assert_no_escape(temp_path, artifact)
        assert normalize_artifact(artifact) == json.loads(FIXTURE.read_text())

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
        deleted = run_command(
            "--execution-smoke-beta",
            "--delete-after",
            "--output-dir",
            temp,
            "examples/simple-agent.yaml",
        )
        assert deleted.returncode == 0, deleted.stderr
        deleted_artifact = load_stdout(deleted)
        assert deleted_artifact["cleanupTranscript"][1]["executed"] is True
        assert deleted_artifact["cleanupTranscript"][1]["exitCode"] == 0
        assert not Path(deleted_artifact["generatedFileManifest"]["packageRoot"]).exists()

    removed_skip = run_command(
        "--execution-smoke-beta",
        "--skip-generation",
        "--output-dir",
        tempfile.gettempdir(),
        "examples/simple-agent.yaml",
    )
    assert removed_skip.returncode == 2
    assert "unrecognized arguments: --skip-generation" in removed_skip.stderr

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
        package_root = Path(temp) / "simple-research-helper"
        (package_root / "tests").mkdir(parents=True)
        (package_root / "src").mkdir()
        (package_root / "tests" / "test_static_contract.py").write_text("raise SystemExit(0)\n")
        (package_root / "tests" / "test_policy_eval_gates.py").write_text("raise SystemExit(0)\n")
        (package_root / "src" / "agent_harness.py").write_text("raise SystemExit(0)\n")
        existing_package = run_command(
            "--execution-smoke-beta",
            "--output-dir",
            temp,
            "examples/simple-agent.yaml",
        )
        assert existing_package.returncode == 2
        assert "package directory already exists" in existing_package.stderr

    unsafe_dir = run_command(
        "--execution-smoke-beta",
        "--output-dir",
        str(ROOT),
        "examples/simple-agent.yaml",
    )
    assert unsafe_dir.returncode == 2
    assert "system temp root" in unsafe_dir.stderr

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
        traversal = run_command(
            "--execution-smoke-beta",
            "--output-dir",
            temp,
            "--package-dir",
            "../escape",
            "examples/simple-agent.yaml",
        )
        assert traversal.returncode == 2
        assert "path traversal" in traversal.stderr

        outside = run_command(
            "--execution-smoke-beta",
            "--output-dir",
            temp,
            "--package-dir",
            str(Path(temp).parent / "outside"),
            "examples/simple-agent.yaml",
        )
        assert outside.returncode == 2
        assert "safe relative path" in outside.stderr

    with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
        invalid = run_command(
            "--execution-smoke-beta",
            "--output-dir",
            temp,
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
        with tempfile.TemporaryDirectory(prefix="reddiagent-starter-smoke-") as temp:
            blocked = run_command(
                "--execution-smoke-beta",
                "--output-dir",
                temp,
                flag,
                "examples/simple-agent.yaml",
            )
            assert blocked.returncode == 3
            blocked_artifact = load_stdout(blocked)
            assert blocked_artifact["status"] == "blocked-unsafe-request"
            assert blocked_artifact["writesFiles"] is False
            assert blocked_artifact["blockedRequests"][0]["policyId"] == policy_id
            assert blocked_artifact["blockedRequests"][0]["allowed"] is False

    print("PASS starter package execution smoke beta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
