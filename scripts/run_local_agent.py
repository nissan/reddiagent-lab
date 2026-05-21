#!/usr/bin/env python3
"""Dry-run a ReddiAgent ADL file on the local-python target."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import jsonschema
import yaml

from validation_guidance import format_errors, render_text


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validate(doc: dict) -> list[jsonschema.ValidationError]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    return sorted(validator.iter_errors(doc), key=lambda e: list(e.path))


def stable_id(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def build_trace(doc: dict, path: Path) -> list[dict]:
    metadata = doc["metadata"]
    harness = doc["harness"]
    model = doc["model"]
    agent = metadata["name"]
    trace_id = stable_id(agent, path.name, "dry-run")
    events = [
        {
            "event": "session.started",
            "traceId": trace_id,
            "agent": agent,
            "runtime": harness["runtime"]["target"],
        },
        {
            "event": "model.resolved",
            "traceId": trace_id,
            "provider": model["providers"]["preferred"],
            "capability": model["capability"],
        },
        {
            "event": "tools.registered",
            "traceId": trace_id,
            "count": len(harness.get("tools", [])),
        },
        {
            "event": "policies.loaded",
            "traceId": trace_id,
            "count": len(harness.get("policies", [])),
        },
        {
            "event": "evals.loaded",
            "traceId": trace_id,
            "count": len(harness.get("evalGates", [])),
        },
        {
            "event": "task.dry_run_completed",
            "traceId": trace_id,
            "status": "pass",
        },
    ]
    return events


def dry_run(path: Path) -> int:
    doc = load_yaml(path)
    errors = validate(doc)
    if errors:
        print(render_text(str(path.relative_to(ROOT)), format_errors(errors)))
        return 1

    metadata = doc["metadata"]
    model = doc["model"]
    harness = doc["harness"]
    extensions = doc.get("extensions") or {}

    trace = build_trace(doc, path)
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
        "mode": "dry-run",
        "level": 1,
        "trace": trace,
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
