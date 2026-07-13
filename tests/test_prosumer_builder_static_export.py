#!/usr/bin/env python3
"""Check the local/static Prosumer Builder HTML export fixture."""

from __future__ import annotations

import json
from html import unescape
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
HTML_PATH = ROOT / "docs" / "prosumer-builder-static-export.html"


def generated_html(path: Path) -> str:
    subprocess.run(
        [PYTHON, "scripts/prosumer_builder_static_export.py", "--output", str(path)],
        cwd=ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    return path.read_text()


def manifest_from_html(rendered: str) -> dict:
    marker = '<script id="prosumer-static-export-manifest" type="application/json">'
    start = rendered.index(marker) + len(marker)
    end = rendered.index("</script>", start)
    return json.loads(unescape(rendered[start:end]))


def export_step(plan: dict) -> dict:
    matches = [step for step in plan["flow"] if step["id"] == "export"]
    assert len(matches) == 1
    return matches[0]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        expected = generated_html(Path(tmp) / "prosumer-builder-static-export.html")

    committed = HTML_PATH.read_text()
    assert committed == expected, "docs/prosumer-builder-static-export.html is not regenerated"
    assert "https://" not in committed
    assert "http://" not in committed
    assert "<script src=" not in committed
    assert "fetch(" not in committed
    assert "XMLHttpRequest" not in committed
    assert "runtimeExecutionAllowed=false" in committed
    assert "paymentAccess=false" in committed
    assert "mcpInvocation=false" in committed

    manifest = manifest_from_html(committed)
    assert manifest["format"] == "prosumer-builder-static-html-export-report"
    assert manifest["guardrails"]["localStaticFixtureOnly"] is True
    assert manifest["guardrails"]["devServerStarted"] is False
    assert manifest["guardrails"]["browserAutomationRequired"] is False
    assert manifest["guardrails"]["runtimeExecutionAllowed"] is False
    assert manifest["guardrails"]["networkAccess"] is False
    assert manifest["guardrails"]["paymentAccess"] is False
    assert manifest["guardrails"]["mcpInvocation"] is False
    assert manifest["coveredSources"] == [
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
    ]
    assert manifest["blockedFixtureSource"] == "examples/invalid/missing-instructions.yaml"
    assert len(manifest["plans"]) == 3

    by_agent = {plan["agent"]: plan for plan in manifest["plans"]}
    simple_matrix = export_step(by_agent["simple-research-helper"])["staticUiExportMatrix"]
    assert [row["target"] for row in simple_matrix] == [
        "agent-spec",
        "a2a-agent-card",
        "agent-skills-skill-md",
        "starter-manifest",
        "provider-compatibility",
        "rap-bridge",
    ]
    assert simple_matrix[0]["readiness"] == "metadata-only"
    payment_matrix = export_step(by_agent["paid-specialist-researcher"])["staticUiExportMatrix"]
    assert next(row for row in payment_matrix if row["target"] == "rap-bridge")["readiness"] == "report-ready"
    blocked = manifest["blockedExportFixture"]
    assert blocked["supported"] is False
    assert export_step(blocked)["status"] == "blocked"
    assert all(plan["runtimeExecutionAllowed"] is False for plan in manifest["plans"])

    print("PASS Prosumer Builder static export")
    return 0


if __name__ == "__main__":
    sys.exit(main())
