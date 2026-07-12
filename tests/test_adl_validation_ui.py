#!/usr/bin/env python3
"""Check the local/static ADL validation UI prototype."""

from __future__ import annotations

import json
from html import unescape
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
HTML_PATH = ROOT / "docs" / "adl-validation-ui.html"


def generated_html(path: Path) -> str:
    subprocess.run(
        [PYTHON, "scripts/adl_validation_ui.py", "--output", str(path)],
        cwd=ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    return path.read_text()


def manifest_from_html(html: str) -> dict:
    marker = '<script id="adl-ui-manifest" type="application/json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    return json.loads(unescape(html[start:end]))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        expected = generated_html(Path(tmp) / "adl-validation-ui.html")

    committed = HTML_PATH.read_text()
    assert committed == expected, "docs/adl-validation-ui.html is not regenerated"
    assert "https://" not in committed
    assert "http://" not in committed
    assert "<script src=" not in committed
    assert "fetch(" not in committed
    assert "XMLHttpRequest" not in committed
    assert "runtimeExecutionAllowed" in committed
    assert "paymentAccess" in committed
    assert "mcpInvocation" in committed
    assert "validatePastedAdl" in committed

    manifest = manifest_from_html(committed)
    assert manifest["guardrails"]["localPrototypeOnly"] is True
    assert manifest["guardrails"]["runtimeExecutionAllowed"] is False
    assert manifest["guardrails"]["networkAccess"] is False
    assert manifest["guardrails"]["paymentAccess"] is False
    assert len(manifest["examples"]) == 4

    by_key = {item["key"]: item for item in manifest["examples"]}
    assert by_key["simple"]["validation"]["status"] == "pass"
    assert by_key["tool"]["validation"]["status"] == "pass"
    assert by_key["payment"]["validation"]["status"] == "pass"
    invalid = by_key["invalid-missing-instructions"]["validation"]
    assert invalid["status"] == "fail"
    assert invalid["errors"][0]["location"] == "harness.instructions"
    print("PASS adl validation UI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
