#!/usr/bin/env python3
"""Validate ADL v0.2 runtime/deployment descriptor contracts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
LOCAL_EXAMPLE = ROOT / "examples" / "v0.2" / "runtime-local-python-agent.yaml"
HOSTED_CONTAINER_EXAMPLE = ROOT / "examples" / "v0.2" / "runtime-hosted-container-agent.yaml"
SERVERLESS_PLATFORM_EXAMPLE = ROOT / "examples" / "v0.2" / "runtime-serverless-platform-agent.yaml"
INVALID_EMBEDDED_SECRET = ROOT / "examples" / "invalid" / "adl-v0.2-runtime-embedded-secret.yaml"
INVALID_LIVE_APPROVAL = (
    ROOT / "examples" / "invalid" / "adl-v0.2-runtime-approved-live-without-evidence.yaml"
)


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load_schema())


def schema_errors(path: Path) -> list[jsonschema.ValidationError]:
    return sorted(validator().iter_errors(load_yaml(path)), key=lambda error: list(error.path))


def assert_no_schema_errors(path: Path) -> None:
    errors = schema_errors(path)
    assert errors == [], [error.message for error in errors]


def run_provider(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/provider_compatibility.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def test_schema_declares_typed_runtime_deployment_sections() -> None:
    schema = load_schema()
    harness = schema["properties"]["harness"]

    assert harness["properties"]["runtime"]["additionalProperties"] is False
    assert harness["properties"]["runtime"]["properties"]["network"] == {"$ref": "#/$defs/runtimeNetwork"}
    assert harness["properties"]["deployment"] == {"$ref": "#/$defs/deployment"}
    assert harness["properties"]["observability"] == {"$ref": "#/$defs/observability"}
    assert harness["properties"]["recovery"] == {"$ref": "#/$defs/recovery"}
    assert schema["$defs"]["secretRef"]["additionalProperties"] is False
    assert "value" not in schema["$defs"]["secretRef"]["properties"]
    assert schema["$defs"]["runtimeActivation"]["allOf"], "approved-bounded activation must require evidence refs"


def test_runtime_descriptor_examples_validate() -> None:
    for path in (LOCAL_EXAMPLE, HOSTED_CONTAINER_EXAMPLE, SERVERLESS_PLATFORM_EXAMPLE):
        assert_no_schema_errors(path)


def test_invalid_secret_bearing_and_live_activation_declarations_fail_schema() -> None:
    secret_messages = [error.message for error in schema_errors(INVALID_EMBEDDED_SECRET)]
    live_messages = [error.message for error in schema_errors(INVALID_LIVE_APPROVAL)]

    assert any("Additional properties are not allowed ('value' was unexpected)" in message for message in secret_messages)
    assert any("'approvalRef' is a required property" in message for message in live_messages)
    assert any("'expiresAt' is a required property" in message for message in live_messages)


def test_local_runtime_descriptor_reports_supported_without_execution() -> None:
    proc = run_provider([str(LOCAL_EXAMPLE.relative_to(ROOT)), "--target", "local-python"])
    report = json.loads(proc.stdout)[0]

    assert report["supported"] is True
    assert report["target"] == "local-python"
    assert report["runtimeDeployment"] == {
        "target": "local-python",
        "networkAccess": "none",
        "secretRefs": [],
        "storageMode": "ephemeral",
        "schedulerTrigger": "manual",
        "activationMode": "blocked",
        "constraints": {
            "runtimeVersion": "python3.14",
            "maxDurationSeconds": 60,
        },
        "deploymentTarget": "local",
        "deploymentEnvironment": "local",
        "rollbackMode": "none",
        "observabilityEvents": ["trace.started", "trace.completed"],
        "recoveryDisableMode": "manual",
        "unsupportedFeatures": [],
    }
    assert report["boundary"]["runtimeExecutionAllowed"] is False


def test_hosted_container_descriptor_fails_unsupported_features_before_execution() -> None:
    proc = run_provider([str(HOSTED_CONTAINER_EXAMPLE.relative_to(ROOT)), "--target", "hosted-container"])
    report = json.loads(proc.stdout)[0]

    assert report["supported"] is False
    assert report["level"] == 4
    assert report["runtimeDeployment"]["target"] == "hosted-container"
    assert report["runtimeDeployment"]["secretRefs"] == ["EXAMPLE_API_KEY"]
    assert report["runtimeDeployment"]["networkAccess"] == "egress"
    assert report["runtimeDeployment"]["storageMode"] == "persistent"
    assert report["runtimeDeployment"]["rollbackMode"] == "previous-version"
    assert {
        item["feature"]
        for item in report["runtimeDeployment"]["unsupportedFeatures"]
    } == {"network-access", "stateful-storage"}
    assert "runtime_deployment:network-access" in report["unsupportedFeatures"]
    assert "runtime_deployment:stateful-storage" in report["unsupportedFeatures"]
    assert report["boundary"]["runtimeExecutionAllowed"] is False


def test_serverless_platform_descriptor_fails_event_scheduler_before_execution() -> None:
    proc = run_provider([str(SERVERLESS_PLATFORM_EXAMPLE.relative_to(ROOT)), "--target", "serverless"])
    report = json.loads(proc.stdout)[0]

    assert report["supported"] is False
    assert report["runtimeDeployment"]["target"] == "serverless"
    assert report["runtimeDeployment"]["secretRefs"] == ["PLATFORM_TOKEN"]
    assert report["runtimeDeployment"]["schedulerTrigger"] == "event"
    assert {
        item["feature"]
        for item in report["runtimeDeployment"]["unsupportedFeatures"]
    } == {"network-access", "non-manual-scheduler"}
    assert "runtime_deployment:non-manual-scheduler" in report["unsupportedFeatures"]
    assert report["boundary"]["runtimeExecutionAllowed"] is False


def test_invalid_descriptor_refusal_keeps_runtime_blocked() -> None:
    proc = run_provider([str(INVALID_EMBEDDED_SECRET.relative_to(ROOT)), "--target", "hosted-container"])
    report = json.loads(proc.stdout)[0]

    assert report["supported"] is False
    assert report["compatibilityMode"] == "provider-compatibility-report-refused"
    assert report["unsupportedFeatures"] == ["adl_v0_2_schema_validation"]
    assert report["runtimeDeployment"]["target"] == "hosted-container"
    assert report["runtimeDeployment"]["secretRefs"] == ["EXAMPLE_API_KEY"]
    assert report["validationDiagnostics"]
    assert report["boundary"]["runtimeExecutionAllowed"] is False


def test_spec_documents_runtime_deployment_descriptor_contract() -> None:
    text = SPEC_PATH.read_text()
    for phrase in [
        "Runtime And Deployment Descriptor",
        "secret-reference-only",
        "Unsupported declarations",
        "hosted-container",
        "serverless/platform-native",
        "runtimeExecutionAllowed=false",
    ]:
        assert phrase in text


def main() -> int:
    test_schema_declares_typed_runtime_deployment_sections()
    test_runtime_descriptor_examples_validate()
    test_invalid_secret_bearing_and_live_activation_declarations_fail_schema()
    test_local_runtime_descriptor_reports_supported_without_execution()
    test_hosted_container_descriptor_fails_unsupported_features_before_execution()
    test_serverless_platform_descriptor_fails_event_scheduler_before_execution()
    test_invalid_descriptor_refusal_keeps_runtime_blocked()
    test_spec_documents_runtime_deployment_descriptor_contract()
    print("PASS ADL v0.2 runtime deployment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
