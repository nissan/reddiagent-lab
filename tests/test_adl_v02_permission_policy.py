#!/usr/bin/env python3
"""Validate ADL v0.2 structured permission and capability policies."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
POSITIVE_POLICY_EXAMPLE = ROOT / "examples" / "v0.2" / "permission-policy-agent.yaml"
NEGATIVE_UNKNOWN_CAPABILITY = ROOT / "examples" / "invalid" / "adl-v0.2-unknown-policy-capability.yaml"
NEGATIVE_UNENFORCEABLE = ROOT / "examples" / "invalid" / "adl-v0.2-unenforceable-policy.yaml"
NEGATIVE_TOOL_POLICY_REF = ROOT / "examples" / "invalid" / "adl-v0.2-tool-missing-policy-ref.yaml"
NEGATIVE_PAYMENT_POLICY_REF = ROOT / "examples" / "invalid" / "adl-v0.2-payment-missing-policy-ref.yaml"
NEGATIVE_HUMAN_APPROVAL = ROOT / "examples" / "invalid" / "adl-v0.2-human-approval-not-required.yaml"

REQUIRED_POLICY_FIELDS = {
    "id",
    "capability",
    "subject",
    "resource",
    "action",
    "effect",
    "scope",
    "limits",
    "approval",
    "enforcement",
}
REQUIRED_CAPABILITY_COVERAGE = {
    "tool",
    "network",
    "filesystem",
    "payment",
    "messaging",
    "human-approval",
}


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


def policies(document: dict) -> list[dict]:
    return document["harness"].get("policies", [])


def policy_by_id(document: dict) -> dict[str, dict]:
    return {policy["id"]: policy for policy in policies(document)}


def policy_matches_tool(policy: dict, tool_id: str) -> bool:
    target_ref = f"tool:{tool_id}"
    enforcement = policy.get("enforcement", {})
    if policy.get("effect") != "allow":
        return False
    if enforcement.get("target") != "runtime-adapter":
        return False
    if enforcement.get("phase") != "before-execution":
        return False
    if enforcement.get("targetRef") != target_ref:
        return False
    if policy["capability"] == "tool":
        return policy["resource"] == target_ref and policy["action"] == "invoke"
    if policy["capability"] == "messaging":
        return policy["action"] == "send"
    return False


def policy_matches_payment_intent(policy: dict, intent: dict) -> bool:
    limits = policy.get("limits", {})
    if policy.get("capability") != "payment":
        return False
    if policy.get("effect") != "allow":
        return False
    if policy.get("resource") != f"x402:intent:{intent['id']}":
        return False
    if policy.get("action") != intent["direction"]:
        return False
    if policy.get("enforcement", {}).get("target") != "policy-engine":
        return False
    if policy.get("enforcement", {}).get("phase") != "before-execution":
        return False
    if Decimal(intent["maxAmount"]) > Decimal(limits.get("maxUsd", "0")):
        return False
    if intent.get("requireReceipt") and limits.get("requireReceipt") is not True:
        return False
    return True


def assert_policy_refs_match(document: dict) -> None:
    known = policy_by_id(document)

    for tool in document["harness"].get("tools", []) + document["harness"].get("functions", []):
        refs = tool.get("policyRefs", [])
        assert refs, f"{tool['id']} must declare policyRefs"
        for ref in refs:
            assert ref in known, f"{tool['id']} references unknown policy {ref}"
        assert any(policy_matches_tool(known[ref], tool["id"]) for ref in refs), (
            f"{tool['id']} must reference a policy matching tool id, action, "
            "resource, and enforcement target"
        )

    x402 = document.get("extensions", {}).get("x402", {})
    for intent in x402.get("intents", []):
        refs = intent.get("policyRefs", [])
        assert refs, f"{intent['id']} must declare policyRefs"
        for ref in refs:
            assert ref in known, f"{intent['id']} references unknown policy {ref}"
        assert any(policy_matches_payment_intent(known[ref], intent) for ref in refs), (
            f"{intent['id']} must reference a payment policy matching intent id, "
            "action, limits, and enforcement target"
        )


def expect_policy_ref_mismatch(document: dict, expected: str) -> None:
    try:
        assert_policy_refs_match(document)
    except AssertionError as error:
        assert expected in str(error)
    else:
        raise AssertionError(f"{expected} mismatch must fail compatibility")


def test_positive_policy_example_validates_and_covers_required_capabilities() -> None:
    assert_no_schema_errors(POSITIVE_POLICY_EXAMPLE)
    document = load_yaml(POSITIVE_POLICY_EXAMPLE)

    for policy in policies(document):
        assert REQUIRED_POLICY_FIELDS <= set(policy), policy["id"]

    assert {policy["capability"] for policy in policies(document)} >= REQUIRED_CAPABILITY_COVERAGE
    assert_policy_refs_match(document)


def test_policy_schema_names_required_structured_fields() -> None:
    policy_schema = load_schema()["$defs"]["policy"]
    assert policy_schema["required"] == [
        "id",
        "capability",
        "subject",
        "resource",
        "action",
        "effect",
        "scope",
        "enforcement",
    ]
    assert set(policy_schema["properties"]) >= REQUIRED_POLICY_FIELDS


def test_spec_documents_fail_closed_policy_model() -> None:
    text = SPEC_PATH.read_text()
    for phrase in [
        "typed capability",
        "subject",
        "resource",
        "action",
        "effect",
        "scope",
        "limits",
        "approval",
        "enforcement",
        "Unknown, mismatched, or unenforceable",
    ]:
        assert phrase in text


def test_unknown_policy_capability_fails_schema_before_execution() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_UNKNOWN_CAPABILITY)]
    assert any("'browser' is not one of" in message for message in messages)


def test_unenforceable_policy_target_fails_schema_before_execution() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_UNENFORCEABLE)]
    assert any("'best-effort-note' is not one of" in message for message in messages)


def test_human_approval_policy_must_require_human_review() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_HUMAN_APPROVAL)]
    assert any("True was expected" in message for message in messages)


def test_risky_tool_capability_requires_matching_policy_ref() -> None:
    document = load_yaml(NEGATIVE_TOOL_POLICY_REF)
    assert_no_schema_errors(NEGATIVE_TOOL_POLICY_REF)
    expect_policy_ref_mismatch(document, "references unknown policy missing-policy")


def test_existing_tool_policy_refs_must_match_declared_capability() -> None:
    document = load_yaml(POSITIVE_POLICY_EXAMPLE)

    only_messaging = deepcopy(document)
    only_messaging["harness"]["tools"][0]["policyRefs"] = ["allow-approved-messaging"]
    expect_policy_ref_mismatch(only_messaging, "search_docs must reference a policy matching")

    only_human_approval = deepcopy(document)
    only_human_approval["harness"]["tools"][0]["policyRefs"] = ["require-human-approval"]
    expect_policy_ref_mismatch(only_human_approval, "search_docs must reference a policy matching")

    wrong_tool = deepcopy(document)
    wrong_tool["harness"]["tools"][1]["policyRefs"] = ["allow-reviewed-tool"]
    expect_policy_ref_mismatch(wrong_tool, "send_summary must reference a policy matching")

    wrong_enforcement_target = deepcopy(document)
    wrong_enforcement_target["harness"]["policies"][0]["enforcement"]["target"] = "static-validator"
    expect_policy_ref_mismatch(wrong_enforcement_target, "search_docs must reference a policy matching")


def test_payment_intent_requires_matching_payment_policy_ref() -> None:
    document = load_yaml(NEGATIVE_PAYMENT_POLICY_REF)
    assert_no_schema_errors(NEGATIVE_PAYMENT_POLICY_REF)
    expect_policy_ref_mismatch(document, "references unknown policy missing-payment-policy")


def test_payment_policy_ref_must_match_intent_resource_and_limits() -> None:
    document = load_yaml(POSITIVE_POLICY_EXAMPLE)

    wrong_intent_id = deepcopy(document)
    wrong_intent_id["extensions"]["x402"]["intents"][0]["id"] = "different-fee"
    expect_policy_ref_mismatch(wrong_intent_id, "different-fee must reference a payment policy matching")

    excessive_amount = deepcopy(document)
    excessive_amount["extensions"]["x402"]["intents"][0]["maxAmount"] = "999.00"
    expect_policy_ref_mismatch(excessive_amount, "review-fee must reference a payment policy matching")


def main() -> int:
    test_positive_policy_example_validates_and_covers_required_capabilities()
    test_policy_schema_names_required_structured_fields()
    test_spec_documents_fail_closed_policy_model()
    test_unknown_policy_capability_fails_schema_before_execution()
    test_unenforceable_policy_target_fails_schema_before_execution()
    test_human_approval_policy_must_require_human_review()
    test_risky_tool_capability_requires_matching_policy_ref()
    test_existing_tool_policy_refs_must_match_declared_capability()
    test_payment_intent_requires_matching_payment_policy_ref()
    test_payment_policy_ref_must_match_intent_resource_and_limits()
    print("PASS ADL v0.2 permission policy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
