#!/usr/bin/env python3
"""Validate the ADL v0.2 source-boundary contract."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.2.schema.json"
POSITIVE_SOURCE_BOUNDARY = ROOT / "examples" / "v0.2" / "source-boundary-agent.yaml"
NEGATIVE_ALIAS = ROOT / "examples" / "invalid" / "adl-v0.2-data-source-alias.yaml"
NEGATIVE_UNTRUSTED = ROOT / "examples" / "invalid" / "adl-v0.2-untrusted-source-no-check.yaml"
NEGATIVE_UNTRUSTED_APPROVED = (
    ROOT / "examples" / "invalid" / "adl-v0.2-untrusted-source-approved-expectation.yaml"
)

CANONICAL_TYPES = ["file", "url", "api", "database", "vector-index", "mcp"]


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load_schema())


def validation_errors(path: Path) -> list[jsonschema.ValidationError]:
    return sorted(validator().iter_errors(load_yaml(path)), key=lambda error: list(error.path))


def test_source_boundary_positive_fixture_covers_canonical_vocabulary() -> None:
    doc = load_yaml(POSITIVE_SOURCE_BOUNDARY)
    sources = doc["harness"]["dataSources"]

    assert [source["type"] for source in sources] == CANONICAL_TYPES
    assert validation_errors(POSITIVE_SOURCE_BOUNDARY) == []

    for source in sources:
        assert source["sourceRef"].startswith(f"{source['type']}:")
        assert source["trust"] == "approved"
        assert source["citationRequired"] is True
        assert source["sourceCheck"]["required"] is True
        assert source["sourceCheck"]["expectation"] == "approved-source"


def test_source_type_shape_fields_are_mutually_exclusive() -> None:
    sources = {source["type"]: source for source in load_yaml(POSITIVE_SOURCE_BOUNDARY)["harness"]["dataSources"]}

    assert set(sources["file"]) >= {"sourceRef", "path"}
    assert "url" not in sources["file"]
    assert set(sources["url"]) >= {"sourceRef", "url"}
    assert "path" not in sources["url"]
    assert set(sources["api"]["api"]) == {"endpoint", "method"}
    assert set(sources["database"]["database"]) == {"engine", "connectionRef", "schemaRef"}
    assert set(sources["vector-index"]["vectorIndex"]) == {"indexRef", "embeddingModel"}
    assert set(sources["mcp"]["mcp"]) == {"serverRef", "toolName", "outputShape"}


def test_legacy_data_source_aliases_fail_validation() -> None:
    errors = validation_errors(NEGATIVE_ALIAS)
    assert errors, "legacy data-source aliases must fail in ADL v0.2"
    assert any("is not one of" in error.message and "document" in error.message for error in errors)


def test_untrusted_sources_must_keep_citation_and_source_check_required() -> None:
    errors = validation_errors(NEGATIVE_UNTRUSTED)
    assert errors, "untrusted sources without source checks must fail closed"
    messages = [error.message for error in errors]
    assert "True was expected" in messages


def test_untrusted_sources_cannot_claim_approved_source_expectation() -> None:
    errors = validation_errors(NEGATIVE_UNTRUSTED_APPROVED)
    assert errors, "untrusted sources must not claim approved-source expectation"
    assert any("'approved-source' is not one of ['manual-review', 'not-citable']" in error.message for error in errors)


def test_approved_sources_must_keep_citation_and_source_check_required() -> None:
    doc = load_yaml(POSITIVE_SOURCE_BOUNDARY)
    source = deepcopy(doc["harness"]["dataSources"][0])
    source["citationRequired"] = False
    source["sourceCheck"]["required"] = False
    doc["harness"]["dataSources"] = [source]

    errors = sorted(validator().iter_errors(doc), key=lambda error: list(error.path))
    messages = [error.message for error in errors]
    assert "True was expected" in messages


def test_schema_source_vocabulary_matches_spec_contract() -> None:
    schema_types = load_schema()["$defs"]["dataSource"]["properties"]["type"]["enum"]
    spec = (ROOT / "specs" / "ADL-v0.2.md").read_text()

    assert schema_types == CANONICAL_TYPES
    for alias in ["document", "web", "knowledge-base"]:
        assert f"`{alias}`" in spec
        assert alias not in schema_types


def main() -> int:
    test_source_boundary_positive_fixture_covers_canonical_vocabulary()
    test_source_type_shape_fields_are_mutually_exclusive()
    test_legacy_data_source_aliases_fail_validation()
    test_untrusted_sources_must_keep_citation_and_source_check_required()
    test_untrusted_sources_cannot_claim_approved_source_expectation()
    test_approved_sources_must_keep_citation_and_source_check_required()
    test_schema_source_vocabulary_matches_spec_contract()
    print("PASS ADL v0.2 source boundary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
