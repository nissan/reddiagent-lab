#!/usr/bin/env python3
"""Focused deterministic Buzz static exporter checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SOURCE = ROOT / "tests" / "fixtures" / "buzz-valid-static-agent.yaml"
ATTRIBUTION = ROOT / "tests" / "fixtures" / "buzz-attribution-distribution-request.json"
SCHEMA = ROOT / "specs" / "ADL-v0.2.schema.json"
PIN = "a" * 40


def binding(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"canonicalAgentId": "reddiagent:buzz-static-review-agent",
            "adlDigest": digest, "buzzAgentKey": "buzz:review-key",
            "ownerKey": "owner:review-key", "bindingDigest": "b" * 64,
            "status": "active", "verified": True}


def command(source: Path, binding_path: Path, *extra: str) -> list[str]:
    return [PYTHON, "scripts/buzz_export.py", "--single", str(source),
            "--canonical-uri", "repo:tests/fixtures/buzz-valid-static-agent.yaml",
            "--schema", str(SCHEMA), "--source-commit", PIN,
            "--upstream-commit", PIN, "--fork-commit", PIN,
            "--adapter-commit", PIN, "--identity-binding", str(binding_path), *extra]


def assert_boundaries(item: dict) -> None:
    for key in ("runtimeExecutionAllowed", "networkAccess", "relayAccess",
                "providerAccess", "credentialAccess", "toolExecutionAllowed",
                "mcpInvocation", "walletAccess", "paymentAccess",
                "deploymentAllowed", "bidirectionalImportAllowed",
                "publicDistributionAllowed", "publicBrandingAllowed"):
        assert item[key] is False, key


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        binding_path = temp / "binding.json"
        binding_path.write_text(json.dumps(binding(SOURCE)))
        first = subprocess.run(command(SOURCE, binding_path), cwd=ROOT, capture_output=True, check=True)
        second = subprocess.run(command(SOURCE, binding_path), cwd=ROOT, capture_output=True, check=True)
        assert first.stdout == second.stdout
        report = json.loads(first.stdout)
        assert report["packageEligible"] is True
        assert report["canonicalAdl"]["digest"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        assert report["canonical"] is False and report["oneWayProjection"] is True
        assert report["paymentMode"] == "none"
        assert_boundaries(report)

        one = temp / "package-one"
        two = temp / "package-two"
        for dest in (one, two):
            proc = subprocess.run(command(SOURCE, binding_path, "--export-package", str(dest)), cwd=ROOT,
                                  capture_output=True, check=True)
            assert proc.stdout == first.stdout
            assert sorted(p.name for p in dest.iterdir()) == ["compatibility-report.json", "manifest.json", "persona.json"]
            assert_boundaries(json.loads((dest / "manifest.json").read_text()))
            assert_boundaries(json.loads((dest / "persona.json").read_text()))
        assert {p.name: p.read_bytes() for p in one.iterdir()} == {p.name: p.read_bytes() for p in two.iterdir()}

        refused = temp / "distribution-refused"
        attribution_request = json.loads(ATTRIBUTION.read_text())
        assert attribution_request["requestDistribution"] is True
        assert attribution_request["publicDistributionAllowed"] is False
        assert attribution_request["publicBrandingAllowed"] is False
        proc = subprocess.run(command(SOURCE, binding_path, "--request-distribution", "--export-package", str(refused)),
                              cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        refusal = json.loads(proc.stdout)
        assert "BUZZ_ATTRIBUTION_REVIEW_REQUIRED" in [d["code"] for d in refusal["diagnostics"]]
        assert not refused.exists()
        assert not list(temp.glob(".*.buzz-export-tmp"))

        tampered_binding = binding(SOURCE)
        tampered_binding["adlDigest"] = "0" * 64
        binding_path.write_text(json.dumps(tampered_binding))
        proc = subprocess.run(command(SOURCE, binding_path), cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_IDENTITY_BINDING_INVALID" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        sensitive = temp / "sensitive.yaml"
        sensitive.write_bytes(SOURCE.read_bytes().replace(b"reviewed public input", b"api_key=sk-secretsecretsecret"))
        binding_path.write_text(json.dumps(binding(sensitive)))
        proc = subprocess.run(command(sensitive, binding_path), cwd=ROOT, text=True, capture_output=True)
        assert proc.returncode == 3
        assert "BUZZ_PUBLIC_SENSITIVE_CONTENT" in [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]

        help_text = subprocess.run([PYTHON, "scripts/buzz_export.py", "--help"], cwd=ROOT,
                                   text=True, capture_output=True, check=True).stdout.lower()
        assert "--import" not in help_text and "round-trip" not in help_text and "reverse" not in help_text

    print("PASS deterministic Buzz static exporter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
