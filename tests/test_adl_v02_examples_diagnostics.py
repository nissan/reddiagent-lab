#!/usr/bin/env python3
"""Check ADL v0.2 example coverage and stable validation diagnostics."""

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

RICH_POSITIVE_EXAMPLES = [
    ROOT / "examples" / "v0.2" / "memory-observability-agent.yaml",
    ROOT / "examples" / "v0.2" / "runtime-hosted-container-agent.yaml",
    ROOT / "examples" / "v0.2" / "adapter-loss-export-agent.yaml",
]

INVALID_EXAMPLE_BUCKETS = {
    "shape": ROOT / "examples" / "invalid" / "adl-v0.2-string-instructions.yaml",
    "policy": ROOT / "examples" / "invalid" / "adl-v0.2-unknown-policy-capability.yaml",
    "gate": ROOT / "examples" / "invalid" / "adl-v0.2-required-eval-gate-nonblocking.yaml",
    "payment": ROOT / "examples" / "invalid" / "adl-v0.2-x402-missing-authority.yaml",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def schema_errors(path: Path) -> list[jsonschema.ValidationError]:
    validator = jsonschema.Draft202012Validator(load_schema())
    return sorted(validator.iter_errors(load_yaml(path)), key=lambda error: list(error.path))


def run_json(args: list[str], check: bool = True) -> list[dict]:
    proc = subprocess.run(
        [PYTHON, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )
    return json.loads(proc.stdout)


def test_rich_v02_examples_validate_and_cover_requested_concepts() -> None:
    for path in RICH_POSITIVE_EXAMPLES:
        assert schema_errors(path) == [], path

    memory = load_yaml(ROOT / "examples" / "v0.2" / "memory-observability-agent.yaml")
    assert memory["harness"]["memory"]["mode"] == "external"
    assert memory["harness"]["memory"]["retention"] == "30d"
    assert memory["harness"]["dataSources"][0]["type"] == "vector-index"
    assert {policy["capability"] for policy in memory["harness"]["policies"]} == {"memory"}

    hosted = load_yaml(ROOT / "examples" / "v0.2" / "runtime-hosted-container-agent.yaml")
    assert hosted["harness"]["runtime"]["target"] == "hosted-container"
    assert hosted["harness"]["observability"]["exports"]["eventRefs"] == [
        "adapter.loss.reported",
        "deployment.health.checked",
    ]

    adapter_loss = load_yaml(ROOT / "examples" / "v0.2" / "adapter-loss-export-agent.yaml")
    assert adapter_loss["harness"]["observability"]["exports"]["requiredEvidenceRefs"] == [
        "export:adapter-loss"
    ]
    assert adapter_loss["harness"]["observability"]["destinations"][0]["mode"] == "local-only"


def test_invalid_v02_examples_cover_shape_policy_gate_and_payment_cases() -> None:
    for category, path in INVALID_EXAMPLE_BUCKETS.items():
        errors = schema_errors(path)
        assert errors, category


def test_v02_schema_diagnostics_have_stable_machine_fields_and_location() -> None:
    reports = run_json(
        [
            "scripts/adl_v02_conformance.py",
            str(INVALID_EXAMPLE_BUCKETS["payment"].relative_to(ROOT)),
        ],
        check=False,
    )
    diagnostics = reports[0]["schemaDiagnostics"]
    assert diagnostics
    first = diagnostics[0]
    assert first["code"].startswith("adl_v0_2_schema."), first
    assert first["severity"] == "error", first
    assert first["category"] == "payment", first
    assert first["path"] == "extensions.x402.intents.0.authority", first
    assert isinstance(first["line"], int), first
    assert isinstance(first["column"], int), first
    assert first["message"], first


def test_provider_refusal_reuses_stable_validation_diagnostics() -> None:
    reports = run_json(
        [
            "scripts/provider_compatibility.py",
            str(INVALID_EXAMPLE_BUCKETS["policy"].relative_to(ROOT)),
            "--target",
            "openai",
        ]
    )
    diagnostics = reports[0]["validationDiagnostics"]
    assert diagnostics
    assert diagnostics[0]["severity"] == "error"
    assert diagnostics[0]["category"] == "policy"
    assert diagnostics[0]["path"].startswith("harness.policies")
    assert diagnostics[0]["line"] is not None
    assert diagnostics[0]["column"] is not None


def test_adl_v02_spec_includes_supporting_spec_ownership_index() -> None:
    text = SPEC_PATH.read_text()
    assert "## Supporting Spec Index" in text
    for section, owner in [
        ("`harness.memory`", "`specs/MEMORY-CONTRACT-v0.1.md`"),
        ("`harness.observability`", "`specs/OBSERVABILITY-v0.1.md`"),
        ("`harness.evalGates`", "`specs/EVAL-GATES-v0.1.md`"),
        ("`extensions.x402`, `extensions.receipts`, `extensions.reputation`", "`specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md`"),
        ("`conformance`", "`specs/CONFORMANCE-v0.1.md`"),
    ]:
        assert section in text
        assert owner in text


def main() -> int:
    test_rich_v02_examples_validate_and_cover_requested_concepts()
    test_invalid_v02_examples_cover_shape_policy_gate_and_payment_cases()
    test_v02_schema_diagnostics_have_stable_machine_fields_and_location()
    test_provider_refusal_reuses_stable_validation_diagnostics()
    test_adl_v02_spec_includes_supporting_spec_ownership_index()
    print("PASS ADL v0.2 examples diagnostics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
