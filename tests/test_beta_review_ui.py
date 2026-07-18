#!/usr/bin/env python3
"""Check local beta review UI artifact generation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-review-ui.json"
PACKAGE = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package.json"


def run_review_ui(package: dict | None = None, expect_status: int = 0) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        package_path = PACKAGE
        if package is not None:
            package_path = tmp_path / "package.json"
            package_path.write_text(json.dumps(package))
        html_path = tmp_path / "review.html"
        proc = subprocess.run(
            [
                PYTHON,
                "scripts/beta_review_ui.py",
                str(package_path),
                "--html-output",
                str(html_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == expect_status, proc.stdout
        doc = json.loads(proc.stdout)
        html = html_path.read_text()
    doc["_html"] = html
    return doc


def assert_mutation_fails(mutator, expected_path: str) -> None:
    package = json.loads(PACKAGE.read_text())
    mutator(package)
    doc = run_review_ui(package, expect_status=3)
    assert doc["status"] == "fail"
    assert expected_path in {finding["path"] for finding in doc["findings"]}


def main() -> int:
    doc = run_review_ui()
    html = doc.pop("_html")
    assert doc == json.loads(FIXTURE.read_text())
    assert doc["mode"] == "beta-runtime-package-review-ui"
    assert doc["issue"] == 246
    assert doc["parentEpic"] == 220
    assert doc["status"] == "pass"
    assert doc["selectedAdlPath"] == "examples/tool-agent.yaml"
    assert doc["rcGateStatus"] == "pass"
    assert doc["currentEvidenceMatchesPinned"] is True
    assert doc["runtimeMode"] == "local-only"
    assert doc["environment"] == "local"
    assert doc["htmlPath"] == "docs/beta-review-ui.html"
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False

    panels = {panel["id"]: panel for panel in doc["reviewPanels"]}
    assert set(panels) == {
        "package-summary",
        "operator-transcript",
        "rollback-transcript",
        "evidence-index",
        "fail-closed-cues",
    }
    assert len(panels["evidence-index"]["rows"]) == 6
    assert all(row["exists"] and row["sha256"] for row in panels["evidence-index"]["rows"])
    assert any(row["id"] == "non-local-runtime-request-denied" for row in panels["fail-closed-cues"]["rows"])
    assert any(row["id"] == "mainnet-request-denied" for row in panels["fail-closed-cues"]["rows"])

    assert "<title>ReddiAgent Beta Review UI</title>" in html
    assert "examples/tool-agent.yaml" in html
    assert "operator-transcript" in html
    assert "rollback.completed" in html
    assert "tests/fixtures/beta-local-runtime-rc-gate.json" in html
    assert "No export blockers." in html
    assert "https://" not in html
    assert "<script" not in html.lower()

    assert_mutation_fails(
        lambda package: package.update({"releaseId": "stale-release"}),
        "package.currentEvidence",
    )
    assert_mutation_fails(
        lambda package: package["results"][0]["evidenceIndex"][0].update({"exists": False, "sha256": None}),
        "positive.evidenceIndex[0]",
    )
    assert_mutation_fails(
        lambda package: package["results"][0].update({"liveRuntimeRequested": 1}),
        "positive.liveRuntimeRequested",
    )
    assert_mutation_fails(
        lambda package: package["results"][0].update({"mainnetRequested": 1}),
        "positive.mainnetRequested",
    )
    assert_mutation_fails(
        lambda package: package["results"][0].update({"rawSecret": "sk-local-test-secret"}),
        "package.results[0].rawSecret",
    )
    assert_mutation_fails(
        lambda package: package["results"][0]["rcGateEvidence"].update({"currentEvidenceMatchesPinned": False}),
        "positive.rcGateEvidence.currentEvidenceMatchesPinned",
    )
    print("PASS beta review UI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
