#!/usr/bin/env python3
"""Validate ReddiAgent example YAML files against ADL v0.1 JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml

from validation_guidance import format_errors, render_text


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"
DEFAULT_EXAMPLES = [
    ROOT / "examples" / "simple-agent.yaml",
    ROOT / "examples" / "tool-agent.yaml",
    ROOT / "examples" / "payment-agent.yaml",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--format",
        choices=["builder", "raw", "json"],
        default="builder",
        help="Output format for validation failures.",
    )
    return parser.parse_args()


def raw_error(error: jsonschema.ValidationError) -> str:
    loc = ".".join(str(p) for p in error.path) or "<root>"
    return f"{loc}: {error.message}"


def main() -> int:
    args = parse_args()
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    failed = False

    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    for path in paths:
        if not path.is_absolute():
            path = ROOT / path
        data = yaml.safe_load(path.read_text())
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            failed = True
            if args.format == "raw":
                print(f"FAIL {path.relative_to(ROOT)}")
                for error in errors:
                    print(f"  - {raw_error(error)}")
            elif args.format == "json":
                guidance = [item.to_dict() for item in format_errors(errors, path)]
                print(json.dumps({"path": str(path.relative_to(ROOT)), "errors": guidance}, indent=2))
            else:
                guidance = format_errors(errors, path)
                print(render_text(str(path.relative_to(ROOT)), guidance))
        else:
            print(f"PASS {path.relative_to(ROOT)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
