#!/usr/bin/env python3
"""Validate ADL v0.2 conformance profile field sets without execution."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"

LIVE_GATED_BEFORE_LEVEL_3 = "payment/reputation extension requires Level 3 or higher"
LIVE_GATED_BEFORE_LEVEL_4 = "production deployment descriptor requires Level 4"
PRODUCTION_RUNTIME_TARGETS = {"hosted-container", "serverless", "platform-native", "openclaw"}
OBSERVABILITY_EVENTS_BY_LEVEL = {
    1: ["trace.started", "trace.completed", "task.completed", "task.failed"],
    2: ["model.called", "policy.checked", "eval.checked"],
    3: ["payment.intent.created", "receipt.emitted", "reputation.signal.emitted"],
    4: ["deployment.health.checked", "adapter.loss.reported"],
}


PROFILE_MATRIX = {
    0: {
        "name": "schema-valid",
        "requiredFields": ["apiVersion", "kind", "metadata.name", "metadata.description", "model", "harness"],
        "optionalFields": ["extensions", "conformance"],
        "evidenceOutputs": ["json-schema-validation"],
        "forbiddenCapabilities": [],
    },
    1: {
        "name": "local-python runnable",
        "requiredFields": [
            "harness.instructions",
            "harness.runtime.target",
            "harness.evalGates",
        ],
        "optionalFields": ["harness.memory", "harness.tools", "harness.dataSources"],
        "evidenceOutputs": [
            "level-1-trace",
            "completion.requiredGateStatus",
            "observability.events:trace.started",
            "observability.events:trace.completed",
            "observability.events:task.completed",
            "observability.events:task.failed",
        ],
        "forbiddenCapabilities": [LIVE_GATED_BEFORE_LEVEL_3, LIVE_GATED_BEFORE_LEVEL_4],
    },
    2: {
        "name": "provider-adapter compatible",
        "requiredFields": [
            "model.capability",
            "model.providers.preferred",
            "model.requirements",
            "harness.policies",
            "harness.evalGates",
        ],
        "optionalFields": ["harness.tools", "harness.dataSources", "harness.memory"],
        "evidenceOutputs": [
            "provider-compatibility-report",
            "unsupported-execution-boundary",
            "observability.events:model.called",
            "observability.events:policy.checked",
            "observability.events:eval.checked",
        ],
        "forbiddenCapabilities": [LIVE_GATED_BEFORE_LEVEL_3, LIVE_GATED_BEFORE_LEVEL_4],
    },
    3: {
        "name": "payment/reputation extension compatible",
        "requiredFields": [
            "extensions.x402.enabled=true",
            "extensions.x402.intents",
            "extensions.x402.intents[*].policyRefs",
            "extensions.receipts.required=true",
            "extensions.reputation.emitSignals",
        ],
        "optionalFields": ["extensions.identity"],
        "evidenceOutputs": [
            "receipt-evidence",
            "reputation-signal-evidence",
            "payment-policy-evidence",
            "observability.events:payment.intent.created",
            "observability.events:receipt.emitted",
            "observability.events:reputation.signal.emitted",
        ],
        "forbiddenCapabilities": [LIVE_GATED_BEFORE_LEVEL_4],
    },
    4: {
        "name": "production deployment compatible",
        "requiredFields": [
            "harness.runtime.target in hosted-container|serverless|platform-native|openclaw",
            "harness.deployment.environment",
            "harness.deployment.rollback",
            "harness.observability.events",
            "harness.recovery.disable",
        ],
        "optionalFields": ["harness.deployment.healthCheck", "harness.observability.destinations"],
        "evidenceOutputs": [
            "deployment-readiness-report",
            "observability-trace-config",
            "rollback-disable-evidence",
            "observability.events:deployment.health.checked",
            "observability.events:adapter.loss.reported",
        ],
        "forbiddenCapabilities": [],
    },
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_adl(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def object_or_empty(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def validation_error_path(error: jsonschema.ValidationError) -> str:
    if error.path:
        return ".".join(str(part) for part in error.path)
    return "<root>"


def schema_diagnostics(doc: dict) -> list[dict]:
    if doc.get("apiVersion") != "reddiagent.dev/v0.2":
        return []
    validator = jsonschema.Draft202012Validator(load_schema())
    return [
        {"path": validation_error_path(error), "message": error.message}
        for error in sorted(validator.iter_errors(doc), key=lambda item: list(item.path))
    ]


def has_path(doc: dict, dotted_path: str) -> bool:
    value: Any = doc
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and not value:
        return False
    return True


def payment_extension_enabled(doc: dict) -> bool:
    extensions = object_or_empty(doc.get("extensions"))
    return bool(object_or_empty(extensions.get("x402")).get("enabled"))


def payment_policies_by_id(doc: dict) -> dict[str, dict]:
    policies = object_or_empty(doc.get("harness")).get("policies", [])
    if not isinstance(policies, list):
        return {}
    return {
        policy["id"]: policy
        for policy in policies
        if isinstance(policy, dict) and isinstance(policy.get("id"), str)
    }


def receipt_requirements_by_intent(doc: dict) -> dict[str, dict]:
    extensions = object_or_empty(doc.get("extensions"))
    receipts = object_or_empty(extensions.get("receipts"))
    refs = receipts.get("refs", [])
    if not isinstance(refs, list):
        return {}
    return {
        requirement["intentRef"]: requirement
        for requirement in refs
        if isinstance(requirement, dict) and isinstance(requirement.get("intentRef"), str)
    }


def decimal_string_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    try:
        return Decimal(left) == Decimal(right)
    except InvalidOperation:
        return False


def payment_authority_matches_intent(intent: dict) -> bool:
    authority = object_or_empty(intent.get("authority"))
    if not authority:
        return False
    for key in ("currency", "rails", "purpose", "scope"):
        if authority.get(key) != intent.get(key):
            return False
    return decimal_string_equal(authority.get("maxAmount"), intent.get("maxAmount"))


def payment_policy_matches_intent(policy: dict, intent: dict) -> bool:
    limits = object_or_empty(policy.get("limits"))
    enforcement = object_or_empty(policy.get("enforcement"))
    if policy.get("capability") != "payment":
        return False
    if policy.get("resource") != f"x402:intent:{intent['id']}":
        return False
    if policy.get("action") != intent.get("direction"):
        return False
    if policy.get("effect") != "allow":
        return False
    if enforcement.get("target") != "policy-engine":
        return False
    if enforcement.get("phase") != "before-execution":
        return False
    if limits.get("requireReceipt") is not True:
        return False
    if intent.get("currency") == "USD":
        return decimal_string_equal(limits.get("maxUsd"), intent.get("maxAmount"))
    return limits.get("currency") == intent.get("currency") and decimal_string_equal(
        limits.get("maxAmount"),
        intent.get("maxAmount"),
    )


def payment_authority_missing_fields(doc: dict) -> list[str]:
    extensions = object_or_empty(doc.get("extensions"))
    x402 = object_or_empty(extensions.get("x402"))
    intents = x402.get("intents", [])
    if not isinstance(intents, list):
        return []

    policies = payment_policies_by_id(doc)
    receipts = receipt_requirements_by_intent(doc)
    missing: list[str] = []
    for intent in intents:
        if not isinstance(intent, dict):
            continue
        intent_id = intent.get("id")
        if not isinstance(intent_id, str):
            continue
        if intent.get("direction") not in {"spend", "refund"}:
            continue

        if not payment_authority_matches_intent(intent):
            missing.append(f"extensions.x402.intents[{intent_id}].authority")

        receipt = receipts.get(intent_id)
        if not receipt:
            missing.append(f"extensions.receipts.refs[intentRef={intent_id}]")

        matching_policy = False
        for policy_ref in intent.get("policyRefs", []):
            policy = policies.get(policy_ref)
            if not policy:
                continue
            if payment_policy_matches_intent(policy, intent):
                matching_policy = True
                break
        if not matching_policy:
            missing.append(f"harness.policies[payment:x402:intent:{intent_id}]")
    return missing


def has_production_runtime(doc: dict) -> bool:
    harness = object_or_empty(doc.get("harness"))
    target = object_or_empty(harness.get("runtime")).get("target")
    return target in PRODUCTION_RUNTIME_TARGETS


def has_deployment_descriptor(doc: dict) -> bool:
    deployment = object_or_empty(doc.get("harness")).get("deployment")
    if not isinstance(deployment, dict) or not deployment:
        return False
    if deployment.get("target") in {"container", "serverless", "platform-native", "openclaw"}:
        return True
    if deployment.get("environment") in {"preview", "staging", "production"}:
        return True
    rollback = object_or_empty(deployment.get("rollback"))
    if rollback and rollback.get("mode") != "none":
        return True
    return any(
        field in deployment
        for field in (
            "region",
            "resources",
            "secretRefs",
            "networkPolicy",
            "storage",
            "scheduler",
            "observability",
            "healthCheck",
            "constraints",
        )
    )


def observability_event_names(doc: dict) -> set[str]:
    observability = object_or_empty(object_or_empty(doc.get("harness")).get("observability"))
    names = set()
    for event in observability.get("events", []):
        if isinstance(event, dict) and isinstance(event.get("name"), str):
            names.add(event["name"])
    return names


def missing_observability_events(doc: dict, level: int) -> list[str]:
    declared = observability_event_names(doc)
    required = OBSERVABILITY_EVENTS_BY_LEVEL.get(level, [])
    return [f"harness.observability.events.{event}" for event in required if event not in declared]


def level_missing_fields(doc: dict, level: int) -> list[str]:
    if level == 0:
        return []
    if level == 1:
        missing = []
        if not has_path(doc, "harness.instructions"):
            missing.append("harness.instructions")
        if not has_path(doc, "harness.runtime.target"):
            missing.append("harness.runtime.target")
        if not has_path(doc, "harness.evalGates"):
            missing.append("harness.evalGates")
        missing.extend(missing_observability_events(doc, 1))
        return missing
    if level == 2:
        missing = [
            field
            for field in [
                "model.capability",
                "model.providers.preferred",
                "model.requirements",
                "harness.policies",
                "harness.evalGates",
            ]
            if not has_path(doc, field)
        ]
        missing.extend(missing_observability_events(doc, 2))
        return missing
    if level == 3:
        missing = []
        extensions = object_or_empty(doc.get("extensions"))
        x402 = object_or_empty(extensions.get("x402"))
        if x402.get("enabled") is not True:
            missing.append("extensions.x402.enabled=true")
        intents = x402.get("intents")
        if not isinstance(intents, list) or not intents:
            missing.append("extensions.x402.intents")
        elif any(not intent.get("policyRefs") for intent in intents if isinstance(intent, dict)):
            missing.append("extensions.x402.intents[*].policyRefs")
        receipts = object_or_empty(extensions.get("receipts"))
        if receipts.get("required") is not True:
            missing.append("extensions.receipts.required=true")
        reputation = object_or_empty(extensions.get("reputation"))
        if not reputation.get("emitSignals"):
            missing.append("extensions.reputation.emitSignals")
        missing.extend(payment_authority_missing_fields(doc))
        missing.extend(missing_observability_events(doc, 3))
        return missing
    if level == 4:
        missing = []
        if not has_production_runtime(doc):
            missing.append("harness.runtime.target in hosted-container|serverless|platform-native|openclaw")
        for field in [
            "harness.deployment.environment",
            "harness.deployment.rollback",
            "harness.observability.events",
            "harness.recovery.disable",
        ]:
            if not has_path(doc, field):
                missing.append(field)
        missing.extend(missing_observability_events(doc, 4))
        return missing
    raise ValueError(f"Unknown ADL v0.2 conformance level: {level}")


def level_forbidden_capabilities(doc: dict, level: int) -> list[str]:
    forbidden = []
    if level < 3 and payment_extension_enabled(doc):
        forbidden.append(LIVE_GATED_BEFORE_LEVEL_3)
    if level < 4 and (has_production_runtime(doc) or has_deployment_descriptor(doc)):
        forbidden.append(LIVE_GATED_BEFORE_LEVEL_4)
    return forbidden


def achieved_level(doc: dict, schema_errors: list[dict]) -> int:
    if schema_errors:
        return -1
    achieved = 0
    for level in range(1, 5):
        if level_missing_fields(doc, level):
            break
        achieved = level
    return achieved


def requested_level(doc: dict, override: int | None) -> int:
    if override is not None:
        return override
    declared = object_or_empty(doc.get("conformance")).get("requestedLevel")
    if declared is None:
        return 0
    return int(declared)


def conformance_report(path: Path, requested: int | None = None) -> dict:
    doc = load_adl(path)
    schema_errors = schema_diagnostics(doc)
    requested_value = requested_level(doc, requested)
    missing_by_level = {
        str(level): level_missing_fields(doc, level)
        for level in range(0, requested_value + 1)
        if schema_errors == []
    }
    forbidden_by_level = {
        str(level): level_forbidden_capabilities(doc, level)
        for level in range(0, requested_value + 1)
        if schema_errors == []
    }
    achieved = achieved_level(doc, schema_errors)
    requested_missing = [
        field
        for level in range(0, requested_value + 1)
        for field in missing_by_level.get(str(level), [])
    ]
    requested_forbidden = forbidden_by_level.get(str(requested_value), [])
    status = (
        "pass"
        if not schema_errors and not requested_missing and not requested_forbidden and achieved >= requested_value
        else "fail"
    )
    return {
        "agent": object_or_empty(doc.get("metadata")).get("name", path.stem),
        "schema": "specs/ADL-v0.2.schema.json",
        "requestedLevel": requested_value,
        "achievedLevel": achieved,
        "status": status,
        "missingFieldsByLevel": missing_by_level,
        "forbiddenCapabilitiesByLevel": forbidden_by_level,
        "schemaDiagnostics": schema_errors,
        "profile": PROFILE_MATRIX.get(requested_value),
        "profileMatrix": PROFILE_MATRIX,
        "boundary": {
            "runtimeExecutionAllowed": False,
            "networkAccess": False,
            "paymentAccess": False,
            "mcpInvocation": False,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", nargs="+", type=Path)
    parser.add_argument("--requested-level", type=int, choices=range(0, 5))
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    reports = [
        conformance_report(path if path.is_absolute() else ROOT / path, args.requested_level)
        for path in args.examples
    ]
    payload = json.dumps(reports, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload, end="")
    return 0 if all(report["status"] == "pass" for report in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
