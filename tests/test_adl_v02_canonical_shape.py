#!/usr/bin/env python3
"""Validate the ADL v0.2 canonical document shape."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
POSITIVE_EXAMPLES = [
    ROOT / "examples" / "v0.2" / "simple-agent.yaml",
    ROOT / "examples" / "v0.2" / "path-agent.yaml",
    ROOT / "examples" / "v0.2" / "permission-policy-agent.yaml",
    ROOT / "examples" / "v0.2" / "tool-contract-agent.yaml",
    ROOT / "examples" / "v0.2" / "source-boundary-agent.yaml",
    ROOT / "examples" / "v0.2" / "provider-capability-agent.yaml",
    ROOT / "examples" / "v0.2" / "runtime-local-python-agent.yaml",
    ROOT / "examples" / "v0.2" / "runtime-hosted-container-agent.yaml",
    ROOT / "examples" / "v0.2" / "runtime-serverless-platform-agent.yaml",
    ROOT / "examples" / "v0.2" / "runtime-platform-native-agent.yaml",
]
NEGATIVE_STRING_INSTRUCTIONS = ROOT / "examples" / "invalid" / "adl-v0.2-string-instructions.yaml"
NEGATIVE_UNKNOWN_PROVIDER = ROOT / "examples" / "invalid" / "adl-v0.2-unknown-provider-id.yaml"
NEGATIVE_UNKNOWN_REQUIREMENT = ROOT / "examples" / "invalid" / "adl-v0.2-unknown-model-requirement.yaml"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load_schema())


def field_contract() -> dict:
    text = SPEC_PATH.read_text()
    match = re.search(r"```json\n(?P<payload>\{.*?\})\n```", text, re.DOTALL)
    assert match, "ADL v0.2 spec must include a JSON field contract"
    return json.loads(match.group("payload"))


def sorted_properties(schema_section: dict) -> list[str]:
    return sorted(schema_section["properties"].keys())


def optional_fields(schema_section: dict) -> list[str]:
    required = set(schema_section.get("required", []))
    return sorted(field for field in schema_section["properties"] if field not in required)


def assert_no_errors(path: Path) -> None:
    errors = sorted(validator().iter_errors(load_yaml(path)), key=lambda error: list(error.path))
    assert errors == [], [error.message for error in errors]


def test_positive_examples_validate_against_v02_schema() -> None:
    for path in POSITIVE_EXAMPLES:
        assert_no_errors(path)


def test_checked_examples_use_canonical_instruction_shape() -> None:
    for path in POSITIVE_EXAMPLES:
        instructions = load_yaml(path)["harness"]["instructions"]
        assert isinstance(instructions, dict), path
        assert sorted(instructions.keys()) in (["inline"], ["path"]), path


def test_shape_divergence_negative_fixture_fails_clearly() -> None:
    errors = sorted(
        validator().iter_errors(load_yaml(NEGATIVE_STRING_INSTRUCTIONS)),
        key=lambda error: list(error.path),
    )
    assert errors, "legacy bare-string instructions fixture must fail"
    first = errors[0]
    assert list(first.path) == ["harness", "instructions"]
    assert "is not of type 'object'" in first.message


def test_provider_and_requirement_vocabulary_fail_closed() -> None:
    provider_errors = sorted(
        validator().iter_errors(load_yaml(NEGATIVE_UNKNOWN_PROVIDER)),
        key=lambda error: list(error.path),
    )
    assert provider_errors, "unknown provider id fixture must fail"
    assert any(list(error.path) == ["model", "providers", "preferred"] for error in provider_errors)
    assert any("openai:gpt-4.1-mini" in error.message and "is not one of" in error.message for error in provider_errors)

    requirement_errors = sorted(
        validator().iter_errors(load_yaml(NEGATIVE_UNKNOWN_REQUIREMENT)),
        key=lambda error: list(error.path),
    )
    assert requirement_errors, "unknown model requirement fixture must fail"
    assert any(list(error.path) == ["model", "requirements"] for error in requirement_errors)
    assert any("providerNativeMagic" in error.message for error in requirement_errors)


def test_spec_field_contract_matches_schema() -> None:
    schema = load_schema()
    contract = field_contract()

    assert schema["required"] == contract["topLevel"]["required"]
    assert optional_fields(schema) == contract["topLevel"]["optional"]
    assert sorted_properties(schema) == sorted(contract["topLevel"]["required"] + contract["topLevel"]["optional"])

    model_schema = schema["properties"]["model"]
    assert model_schema["required"] == contract["model"]["required"]
    assert optional_fields(model_schema) == contract["model"]["optional"]

    harness_schema = schema["properties"]["harness"]
    assert harness_schema["required"] == contract["harness"]["required"]
    assert optional_fields(harness_schema) == sorted(contract["harness"]["optional"])


def main() -> int:
    test_positive_examples_validate_against_v02_schema()
    test_checked_examples_use_canonical_instruction_shape()
    test_shape_divergence_negative_fixture_fails_clearly()
    test_provider_and_requirement_vocabulary_fail_closed()
    test_spec_field_contract_matches_schema()
    print("PASS ADL v0.2 canonical shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
