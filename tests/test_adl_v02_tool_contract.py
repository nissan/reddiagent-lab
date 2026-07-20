#!/usr/bin/env python3
"""Validate ADL v0.2 tool contract metadata and policy linkage."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
POSITIVE_TOOL_CONTRACT = ROOT / "examples" / "v0.2" / "tool-contract-agent.yaml"
NEGATIVE_UNSAFE_MISSING_POLICY = (
    ROOT / "examples" / "invalid" / "adl-v0.2-unsafe-tool-missing-policy-ref.yaml"
)
NEGATIVE_DUPLICATE_TOOL_ID = ROOT / "examples" / "invalid" / "adl-v0.2-duplicate-tool-id.yaml"
NEGATIVE_BAD_METADATA = ROOT / "examples" / "invalid" / "adl-v0.2-bad-tool-contract-metadata.yaml"

TOOL_METADATA_FIELDS = {"permissions", "sideEffects", "timeout", "retryPolicy", "auditLevel"}
RISKY_PERMISSIONS = {"network", "payment", "shell", "filesystem", "messaging", "mcp", "mutation"}
RISKY_SIDE_EFFECTS = {"write", "network", "payment", "messaging", "shell", "filesystem", "mcp", "multiple"}
REQUIRED_RISKY_COVERAGE = {"network", "payment", "shell", "filesystem", "messaging", "mcp", "mutation"}


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


def tools(document: dict) -> list[dict]:
    return document["harness"].get("tools", []) + document["harness"].get("functions", [])


def policy_by_id(document: dict) -> dict[str, dict]:
    return {policy["id"]: policy for policy in document["harness"].get("policies", [])}


def is_risky_tool(tool: dict) -> bool:
    permissions = set(tool.get("permissions", []))
    side_effect_mode = tool.get("sideEffects", {}).get("mode")
    return (
        tool.get("type") == "mcp"
        or bool(permissions & RISKY_PERMISSIONS)
        or side_effect_mode in RISKY_SIDE_EFFECTS
    )


def assert_tool_ids_unique(document: dict) -> None:
    ids = [tool["id"] for tool in tools(document)]
    duplicates = sorted({tool_id for tool_id in ids if ids.count(tool_id) > 1})
    assert duplicates == [], f"duplicate tool ids: {duplicates}"


def policy_matches_tool(policy: dict, tool: dict) -> bool:
    expected_capability = tool.get("capability", "tool")
    expected_resource = tool.get("resource", f"tool:{tool['id']}")
    expected_action = tool.get("action", "invoke")
    enforcement = policy.get("enforcement", {})
    return (
        policy.get("effect") == "allow"
        and policy.get("capability") == expected_capability
        and policy.get("resource") == expected_resource
        and policy.get("action") == expected_action
        and enforcement.get("targetRef") == f"tool:{tool['id']}"
    )


def assert_risky_tools_have_matching_policy_refs(document: dict) -> None:
    known = policy_by_id(document)
    for tool in tools(document):
        refs = tool.get("policyRefs", [])
        if not is_risky_tool(tool):
            assert refs == [], f"safe fixture tool {tool['id']} should not need policyRefs"
            continue
        assert refs, f"risky tool {tool['id']} must declare policyRefs"
        for ref in refs:
            assert ref in known, f"{tool['id']} references unknown policy {ref}"
        assert any(policy_matches_tool(known[ref], tool) for ref in refs), (
            f"{tool['id']} must reference a matching policy"
        )


def test_schema_declares_tool_contract_metadata_fields() -> None:
    tool_schema = load_schema()["$defs"]["tool"]
    assert set(tool_schema["properties"]) >= TOOL_METADATA_FIELDS
    assert tool_schema["properties"]["permissions"]["items"]["enum"] == [
        "tool",
        "network",
        "payment",
        "shell",
        "filesystem",
        "messaging",
        "mcp",
        "mutation",
    ]
    assert tool_schema["properties"]["sideEffects"]["required"] == ["mode"]
    assert tool_schema["properties"]["timeout"]["required"] == ["seconds"]
    assert tool_schema["properties"]["retryPolicy"]["required"] == ["maxAttempts"]


def test_positive_tool_contract_example_validates_and_links_policies() -> None:
    assert_no_schema_errors(POSITIVE_TOOL_CONTRACT)
    document = load_yaml(POSITIVE_TOOL_CONTRACT)

    assert_tool_ids_unique(document)
    assert_risky_tools_have_matching_policy_refs(document)

    covered_permissions = set()
    for tool in tools(document):
        covered_permissions.update(tool.get("permissions", []))
        assert TOOL_METADATA_FIELDS <= set(tool), tool["id"]
    assert covered_permissions >= REQUIRED_RISKY_COVERAGE


def test_schema_requires_policy_refs_for_unsafe_tool_metadata() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_UNSAFE_MISSING_POLICY)]
    assert any("'policyRefs' is a required property" in message for message in messages)


def test_schema_rejects_bad_tool_contract_metadata() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_BAD_METADATA)]
    expected_fragments = [
        "'teleport' is not one of",
        "'invisible' is not one of",
        "0 is less than the minimum of 1",
        "'ignore' is not one of",
        "11 is greater than the maximum of 10",
        "'random' is not one of",
        "'everything' is not one of",
    ]
    for fragment in expected_fragments:
        assert any(fragment in message for message in messages), fragment


def test_tool_ids_must_be_unique_within_harness() -> None:
    assert_no_schema_errors(NEGATIVE_DUPLICATE_TOOL_ID)
    try:
        assert_tool_ids_unique(load_yaml(NEGATIVE_DUPLICATE_TOOL_ID))
    except AssertionError as error:
        assert "duplicate_tool" in str(error)
    else:
        raise AssertionError("duplicate harness tool ids must fail compatibility")


def test_spec_documents_tool_contract_policy_linkage() -> None:
    text = SPEC_PATH.read_text()
    for phrase in [
        "permissions",
        "sideEffects",
        "timeout",
        "retryPolicy",
        "auditLevel",
        "Safe fixture tools",
        "Mutating, network, payment, shell, filesystem, messaging",
        "Tool IDs must be unique",
    ]:
        assert phrase in text


def main() -> int:
    test_schema_declares_tool_contract_metadata_fields()
    test_positive_tool_contract_example_validates_and_links_policies()
    test_schema_requires_policy_refs_for_unsafe_tool_metadata()
    test_schema_rejects_bad_tool_contract_metadata()
    test_tool_ids_must_be_unique_within_harness()
    test_spec_documents_tool_contract_policy_linkage()
    print("PASS ADL v0.2 tool contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
