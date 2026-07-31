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
BLOCKED_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "prosumer-builder-blocked-export-ui.json"


def generated_files(html_path: Path, fixture_path: Path) -> tuple[str, dict]:
    subprocess.run(
        [
            PYTHON,
            "scripts/prosumer_builder_static_export.py",
            "--output",
            str(html_path),
            "--blocked-fixture-output",
            str(fixture_path),
        ],
        cwd=ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    return html_path.read_text(), json.loads(fixture_path.read_text())


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
        tmp_path = Path(tmp)
        expected, expected_blocked_fixture = generated_files(
            tmp_path / "prosumer-builder-static-export.html",
            tmp_path / "prosumer-builder-blocked-export-ui.json",
        )

    committed = HTML_PATH.read_text()
    assert committed == expected, "docs/prosumer-builder-static-export.html is not regenerated"
    blocked_fixture = json.loads(BLOCKED_FIXTURE_PATH.read_text())
    assert blocked_fixture == expected_blocked_fixture, (
        "tests/fixtures/prosumer-builder-blocked-export-ui.json is not regenerated"
    )
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
    assert manifest["blockedFixtureCheck"] == (
        "tests/fixtures/prosumer-builder-blocked-export-ui.json"
    )
    assert manifest["coveredSources"] == [
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
        "examples/payment-agent.yaml",
    ]
    assert manifest["blockedFixtureSource"] == "examples/invalid/missing-instructions.yaml"
    assert len(manifest["plans"]) == 3
    assert manifest["eveCompatibilitySummaries"]["format"] == (
        "prosumer-builder-eve-compatibility-ui-summaries"
    )
    assert manifest["eveCompatibilitySummaries"]["guardrails"]["deploymentAllowed"] is False
    assert manifest["eveCompatibilitySummaries"]["guardrails"]["runtimeExecutionAllowed"] is False
    assert manifest["eveCompatibilitySummaries"]["uiStateCounts"] == {
        "blocked": 1,
        "metadata-only": 2,
        "unsupported-runtime-features": 1,
    }
    assert manifest["eveCompatibilitySummaries"]["losslessStateCounts"] == {
        "blocked-by-validation": 1,
        "not-lossless-metadata-only": 2,
        "not-lossless-unsupported": 1,
    }

    by_agent = {plan["agent"]: plan for plan in manifest["plans"]}
    simple_matrix = export_step(by_agent["simple-research-helper"])["staticUiExportMatrix"]
    assert [row["target"] for row in simple_matrix] == [
        "agent-spec",
        "a2a-agent-card",
        "agent-skills-skill-md",
        "starter-manifest",
        "provider-compatibility",
        "rap-bridge",
        "vercel-eve",
        "buzz-static-projection",
    ]
    assert simple_matrix[0]["readiness"] == "metadata-only"
    eve_simple = next(row for row in simple_matrix if row["target"] == "vercel-eve")
    assert eve_simple["readiness"] == "metadata-only"
    assert eve_simple["blockedBy"] == []
    assert eve_simple["eveCompatibilitySummary"]["uiState"] == "metadata-only"
    assert eve_simple["eveCompatibilitySummary"]["sourceReportCommand"] == (
        "python3 scripts/eve_compatibility.py --single examples/simple-agent.yaml"
    )
    assert eve_simple["eveCompatibilitySummary"]["deploymentAllowed"] is False
    payment_matrix = export_step(by_agent["paid-specialist-researcher"])["staticUiExportMatrix"]
    assert next(row for row in payment_matrix if row["target"] == "rap-bridge")["readiness"] == "report-ready"
    blocked = manifest["blockedExportFixture"]
    assert blocked["supported"] is False
    assert export_step(blocked)["status"] == "blocked"
    assert manifest["blockedExportUiFixture"] == blocked_fixture
    assert blocked_fixture["format"] == "prosumer-builder-blocked-export-ui-fixture"
    assert blocked_fixture["guardrails"]["localStaticFixtureOnly"] is True
    assert blocked_fixture["guardrails"]["runtimeExecutionAllowed"] is False
    assert blocked_fixture["guardrails"]["networkAccess"] is False
    assert blocked_fixture["guardrails"]["paymentAccess"] is False
    assert blocked_fixture["guardrails"]["mcpInvocation"] is False
    assert blocked_fixture["readinessCounts"] == {
        "blocked-before-generation": 3,
        "blocked-by-validation": 8,
        "metadata-only": 12,
        "refused": 1,
    }
    assert blocked_fixture["sources"] == [
        "examples/invalid/missing-instructions.yaml",
        "examples/payment-agent.yaml",
        "examples/simple-agent.yaml",
        "examples/tool-agent.yaml",
    ]
    invalid_rows = [
        row
        for row in blocked_fixture["rows"]
        if row["source"] == "examples/invalid/missing-instructions.yaml"
    ]
    assert len(invalid_rows) == 8
    assert {row["readiness"] for row in invalid_rows} == {"blocked-by-validation"}
    assert all(
        row["blockedBy"] == (["BUZZ_ADL_INVALID"] if row["target"] == "buzz-static-projection" else ["validation_failed"])
        for row in invalid_rows
    )
    assert all(row["validationStatus"] == "fail" for row in invalid_rows)
    assert any(
        "harness: 'instructions' is a required property" in error
        for row in invalid_rows
        for error in row["validationErrors"]
    )
    starter_rows = [
        row
        for row in blocked_fixture["rows"]
        if row["target"] == "starter-manifest"
        and row["readiness"] == "blocked-before-generation"
    ]
    assert len(starter_rows) == 3
    assert all(row["readiness"] == "blocked-before-generation" for row in starter_rows)
    assert all(row["blockedBy"] == ["generator-implementation-review"] for row in starter_rows)
    eve_rows = [row for row in blocked_fixture["rows"] if row["target"] == "vercel-eve"]
    assert len(eve_rows) == 4
    assert [row["readiness"] for row in eve_rows].count("metadata-only") == 3
    assert [row["readiness"] for row in eve_rows].count("blocked-by-validation") == 1
    assert next(
        row for row in eve_rows if row["source"] == "examples/payment-agent.yaml"
    )["blockedBy"] == ["non_local_runtime_execution", "live_payment_execution"]
    assert next(
        row for row in eve_rows if row["source"] == "examples/payment-agent.yaml"
    )["eveCompatibilitySummary"]["uiState"] == "unsupported-runtime-features"
    assert next(
        row
        for row in eve_rows
        if row["source"] == "examples/invalid/missing-instructions.yaml"
    )["eveCompatibilitySummary"]["uiState"] == "blocked"
    payment_metadata_rows = [
        row
        for row in blocked_fixture["rows"]
        if row["source"] == "examples/payment-agent.yaml"
        and row["readiness"] == "metadata-only"
    ]
    assert len(payment_metadata_rows) == 4
    assert all(
        row["blockedBy"] == ["non_local_runtime_execution", "live_payment_execution"]
        for row in payment_metadata_rows
    )
    assert all(
        row["metadataOnlyExtensions"] == [
            "extensions.x402",
            "extensions.receipts",
            "extensions.reputation",
        ]
        for row in payment_metadata_rows
    )
    assert all(row["runtimeExecutionAllowed"] is False for row in blocked_fixture["rows"])
    assert all(row["paymentAccess"] is False for row in blocked_fixture["rows"])
    assert all(plan["runtimeExecutionAllowed"] is False for plan in manifest["plans"])

    print("PASS Prosumer Builder static export")
    return 0


if __name__ == "__main__":
    sys.exit(main())
