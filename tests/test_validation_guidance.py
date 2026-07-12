#!/usr/bin/env python3
"""Check builder-facing validation guidance for common ADL mistakes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/Users/loki/.pyenv/versions/3.14.3/bin/python3"


def validate(path: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/validate_examples.py", "--format", "json", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 1, proc.stdout
    lines = proc.stdout.splitlines()
    payload = "\n".join(line for line in lines if not line.startswith("PASS "))
    return json.loads(payload)


def assert_guidance(path: str, location: str, reference: str, needle: str) -> None:
    payload = validate(path)
    errors = payload["errors"]
    assert errors, payload
    first = errors[0]
    assert first["location"] == location, first
    assert first["reference"] == reference, first
    combined = " ".join(str(value) for value in first.values())
    assert needle in combined, first


def main() -> int:
    assert_guidance(
        "examples/invalid/missing-instructions.yaml",
        "harness.instructions",
        "tutorials/simple-local-agent.md",
        "operating contract",
    )
    assert_guidance(
        "examples/invalid/bad-model-capability.yaml",
        "model.capability",
        "specs/PROVIDER-MAPPING-v0.1.md",
        "supported capability",
    )
    assert_guidance(
        "examples/invalid/bad-runtime-target.yaml",
        "harness.runtime.target",
        "specs/RUNTIME-DEPLOYMENT-v0.1.md",
        "runtime target",
    )
    assert_guidance(
        "examples/invalid/bad-tool-id.yaml",
        "harness.tools.0.id",
        "specs/TOOL-REGISTRY-v0.1.md",
        "required format",
    )
    assert_guidance(
        "examples/invalid/bad-data-source.yaml",
        "harness.dataSources.0.type",
        "specs/ADL-v0.1.md",
        "reviewed knowledge boundary",
    )
    assert_guidance(
        "examples/invalid/bad-memory.yaml",
        "harness.memory.privacyPolicy",
        "specs/MEMORY-CONTRACT-v0.1.md",
        "persistent or external memory",
    )
    assert_guidance(
        "examples/invalid/duplicate-fallbacks.yaml",
        "model.providers.fallbacks",
        "specs/PROVIDER-MAPPING-v0.1.md",
        "duplicate",
    )
    assert_guidance(
        "examples/invalid/bad-payment-intent.yaml",
        "extensions.x402.intents.0.rails",
        "specs/PAYMENT-REPUTATION-EXTENSION-v0.1.md",
        "at least 1 item",
    )
    print("PASS validation guidance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
