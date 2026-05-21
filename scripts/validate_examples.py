#!/usr/bin/env python3
"""Validate ReddiAgent example YAML files against ADL v0.1 JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "tool-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
]


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    failed = False

    paths = [Path(arg) for arg in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT_EXAMPLES
    for path in paths:
        if not path.is_absolute():
            path = ROOT / path
        data = yaml.safe_load(path.read_text())
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            failed = True
            print(f"FAIL {path.relative_to(ROOT)}")
            for error in errors:
                loc = ".".join(str(p) for p in error.path) or "<root>"
                print(f"  - {loc}: {error.message}")
        else:
            print(f"PASS {path.relative_to(ROOT)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
