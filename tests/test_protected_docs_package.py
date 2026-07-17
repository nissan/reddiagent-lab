#!/usr/bin/env python3
"""Check protected publishable documentation package manifest."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "protected-docs-package.json"


def run_package() -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/protected_docs_package.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def assert_static_boundaries(payload: dict) -> None:
    assert payload["runtimeExecutionAllowed"] is False
    assert payload["networkAccess"] is False
    assert payload["paymentAccess"] is False
    assert payload["mcpInvocation"] is False
    assert payload["providerModelApiCalls"] is False
    assert payload["credentialLookupOrStorage"] is False
    assert payload["deploymentAllowed"] is False
    assert payload["publishingAllowed"] is False
    assert payload["universalPasswordSelected"] is False
    assert payload["writesRuntimeCode"] is False


def section(payload: dict, section_id: str) -> dict:
    matches = [item for item in payload["contentSections"] if item["id"] == section_id]
    assert len(matches) == 1
    return matches[0]


def paths(item: dict) -> list[str]:
    return [record["path"] for record in item["files"]]


def main() -> int:
    payload = run_package()
    expected = json.loads(FIXTURE.read_text())
    assert payload == expected

    assert payload["format"] == "protected-docs-package-manifest"
    assert payload["issue"] == 210
    assert payload["parentEpic"] == 206
    assert payload["status"] == "ready-for-static-package-review"
    assert payload["missingRequiredFiles"] == []
    assert payload["approvalGate"]["deploymentRequiresNissanApproval"] is True
    assert payload["approvalGate"]["passwordSelectionRequiresNissanApproval"] is True
    assert payload["approvalGate"]["mainnetAllowed"] is False
    assert "selected outside this repo" in payload["accessModel"]["recommendedProtection"]
    assert "do not commit or generate" in payload["accessModel"]["passwordStorage"]
    assert payload["crawlerControls"]["robotsTxt"] == "User-agent: *\nDisallow: /\n"
    assert payload["crawlerControls"]["htmlMetaRobots"] == "noindex, nofollow, noarchive"
    assert payload["crawlerControls"]["httpHeader"] == (
        "X-Robots-Tag: noindex, nofollow, noarchive"
    )
    assert payload["crawlerControls"]["sitemap"] == "omit sitemap.xml for protected package"
    assert_static_boundaries(payload)

    assert paths(section(payload, "entrypoints")) == [
        "README.md",
        "docs/INDEX.md",
        "docs/REDDIAGENT-VISION-ROADMAP.md",
        "docs/PROTECTED-DOCS-PACKAGE.md",
    ]
    assert "docs/REDDIAGENT-ARCHITECTURE.md" in paths(section(payload, "architecture"))
    assert "docs/adr/0000-adr-index.md" in paths(section(payload, "decisions"))
    assert "specs/ADL-v0.1.md" in paths(section(payload, "specs"))
    assert "mappings/AGENT-SPEC.md" in paths(section(payload, "mappings"))
    assert "research/RESEARCH-TAXONOMY.md" in paths(section(payload, "research"))
    assert "tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md" in paths(
        section(payload, "evidence")
    )
    assert "tests/PROTECTED-DOCS-PACKAGE-REPORT.md" in paths(section(payload, "evidence"))
    assert all(item["status"] == "ready" for item in payload["contentSections"])
    assert all(
        artifact["status"] in {"planned-static-artifact", "generated-by-this-script"}
        for artifact in payload["staticPackageArtifacts"]
    )

    print("PASS protected docs package manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
