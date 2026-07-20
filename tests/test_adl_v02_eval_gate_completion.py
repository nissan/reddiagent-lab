#!/usr/bin/env python3
"""Validate ADL v0.2 eval-gate completion contract semantics."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
SPEC_PATH = ROOT / "specs" / "ADL-v0.2.md"
POSITIVE_EXAMPLE = ROOT / "examples" / "v0.2" / "simple-agent.yaml"
NEGATIVE_REQUIRED_NONBLOCKING = (
    ROOT / "examples" / "invalid" / "adl-v0.2-required-eval-gate-nonblocking.yaml"
)
NEGATIVE_WARNING_BLOCKING = (
    ROOT / "examples" / "invalid" / "adl-v0.2-warning-eval-gate-blocking.yaml"
)
RESULT_FIXTURE = ROOT / "tests" / "fixtures" / "adl-v02-eval-gate-completion-results.json"

REQUIRED_GATE_FIELDS = {
    "id",
    "type",
    "rule",
    "required",
    "severity",
    "appliesTo",
    "evidence",
    "retryable",
    "onFailure",
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


def warning_gate() -> dict:
    return {
        "id": "preferred-summary-style",
        "type": "output-check",
        "rule": "Output should include a concise summary.",
        "required": False,
        "severity": "warning",
        "appliesTo": {"scope": "output"},
        "evidence": {
            "ref": "trace:output.style_checked",
            "schema": {
                "type": "object",
                "required": ["status"],
                "properties": {"status": {"enum": ["pass", "warn", "fail"]}},
            },
        },
        "retryable": True,
        "onFailure": {"completion": "warn", "defaultStatus": "warn", "visibility": "trace"},
    }


def completion_for(gates: list[dict], results: dict[str, dict]) -> dict:
    blocking_failures = []
    warnings = []
    for gate in gates:
        gate_id = gate["id"]
        result = results.get(gate_id, {})
        default_status = gate["onFailure"]["defaultStatus"]
        status = result.get("status", default_status)
        if gate["required"]:
            if status != "pass":
                blocking_failures.append(gate_id)
        elif status != "pass":
            warnings.append(gate_id)

    required_gate_status = "fail" if blocking_failures else "pass"
    return {
        "transportStatus": "pass",
        "requiredGateStatus": required_gate_status,
        "status": required_gate_status,
        "blockingFailures": blocking_failures,
        "warnings": warnings,
    }


def test_schema_declares_eval_gate_completion_contract() -> None:
    eval_gate_schema = load_schema()["$defs"]["evalGate"]
    assert set(eval_gate_schema["required"]) == REQUIRED_GATE_FIELDS
    assert eval_gate_schema["properties"]["required"]["type"] == "boolean"
    assert eval_gate_schema["properties"]["severity"]["enum"] == ["info", "warning", "error", "critical"]
    assert eval_gate_schema["properties"]["appliesTo"]["required"] == ["scope"]
    assert eval_gate_schema["properties"]["evidence"]["required"] == ["ref", "schema"]
    assert eval_gate_schema["properties"]["retryable"]["type"] == "boolean"
    assert eval_gate_schema["properties"]["onFailure"]["required"] == ["completion", "defaultStatus"]


def test_positive_example_uses_required_fail_closed_gate_contract() -> None:
    assert_no_schema_errors(POSITIVE_EXAMPLE)
    gate = load_yaml(POSITIVE_EXAMPLE)["harness"]["evalGates"][0]
    assert REQUIRED_GATE_FIELDS <= set(gate)
    assert gate["required"] is True
    assert gate["severity"] == "error"
    assert gate["evidence"]["ref"] == "trace:output.has_answer"
    assert gate["onFailure"] == {
        "completion": "block",
        "defaultStatus": "fail",
        "visibility": "trace-and-receipt",
    }


def test_required_gates_must_be_blocking_fail_closed() -> None:
    messages = [error.message for error in schema_errors(NEGATIVE_REQUIRED_NONBLOCKING)]
    assert any("'warning' is not one of ['error', 'critical']" in message for message in messages)
    assert any("'block' was expected" in message for message in messages)
    assert any("'fail' was expected" in message for message in messages)


def test_warning_gates_must_be_nonblocking() -> None:
    errors = schema_errors(NEGATIVE_WARNING_BLOCKING)
    messages = [error.message for error in errors]
    assert any("'error' is not one of ['info', 'warning']" in message for message in messages)
    assert any("'warn' was expected" in message for message in messages)
    assert any(
        "'warn' was expected" in error.message and list(error.path)[-1:] == ["defaultStatus"]
        for error in errors
    )


def test_completion_reducer_distinguishes_required_and_warning_gates() -> None:
    document = load_yaml(POSITIVE_EXAMPLE)
    required_gates = document["harness"]["evalGates"]
    fixture = json.loads(RESULT_FIXTURE.read_text())

    for scenario in fixture["scenarios"]:
        gates = (
            required_gates + [warning_gate()]
            if scenario.get("includeWarningGate")
            or "preferred-summary-style" in scenario["results"]
            else required_gates
        )
        assert completion_for(gates, scenario["results"]) == scenario["expected"], scenario["id"]


def test_spec_documents_eval_gate_completion_contract() -> None:
    text = SPEC_PATH.read_text()
    for phrase in [
        "Eval Gate Completion Contract",
        "`required`: whether this gate must pass before task completion",
        "Missing evidence for a required gate uses the fail-closed default status",
        "Completion is computed from gate results, not from dry-run transport success",
        "Non-required gates remain visible in traces and receipts but cannot block completion",
        "`completion.transportStatus = pass` only means deterministic validation and reporting completed",
    ]:
        assert phrase in text


def main() -> int:
    test_schema_declares_eval_gate_completion_contract()
    test_positive_example_uses_required_fail_closed_gate_contract()
    test_required_gates_must_be_blocking_fail_closed()
    test_warning_gates_must_be_nonblocking()
    test_completion_reducer_distinguishes_required_and_warning_gates()
    test_spec_documents_eval_gate_completion_contract()
    print("PASS ADL v0.2 eval-gate completion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
