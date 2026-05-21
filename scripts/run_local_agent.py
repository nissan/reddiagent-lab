#!/usr/bin/env python3
"""Dry-run a ReddiAgent ADL file on the local-python target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validate(doc: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    return [f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def dry_run(path: Path) -> int:
    doc = load_yaml(path)
    errors = validate(doc)
    if errors:
        print("validation: failed")
        for error in errors:
            print(f"- {error}")
        return 1

    metadata = doc["metadata"]
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}

    summary = {
        "agent": metadata["name"],
        "description": metadata["description"],
        "runtime": harness["runtime"]["target"],
        "modelCapability": model["capability"],
        "preferredProvider": model["providers"]["preferred"],
        "fallbackProviders": model["providers"].get("fallbacks", []),
        "toolCount": len(harness.get("tools", [])),
        "policyCount": len(harness.get("policies", [])),
        "evalGateCount": len(harness.get("evalGates", [])),
        "paymentEnabled": bool((extensions.get("x402") or {}).get("enabled")),
        "mode": "dry-run"
    }

    print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("adl", type=Path)
    args = parser.parse_args()
    return dry_run(args.adl)


if __name__ == "__main__":
    sys.exit(main())

