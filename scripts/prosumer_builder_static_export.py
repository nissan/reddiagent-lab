#!/usr/bin/env python3
"""Generate a local/static Prosumer Builder export report HTML fixture."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import sys

from prosumer_builder_plan import BOUNDARY_FLAGS, DEFAULT_EXAMPLES, ROOT, plan_for


DEFAULT_INVALID_EXAMPLE = ROOT / "examples" / "invalid" / "missing-instructions.yaml"
DEFAULT_OUTPUT = ROOT / "docs" / "prosumer-builder-static-export.html"


def build_manifest(paths: list[Path], invalid_path: Path) -> dict:
    plans = [plan_for(path) for path in paths]
    invalid_plan = plan_for(invalid_path)
    return {
        "format": "prosumer-builder-static-html-export-report",
        "generatedFrom": "scripts/prosumer_builder_static_export.py",
        "authoritativePlanCommand": "python3 scripts/prosumer_builder_plan.py examples/simple-agent.yaml examples/tool-agent.yaml examples/payment-agent.yaml",
        "authoritativeCheck": "tests/test_prosumer_builder_static_export.py",
        "coveredSources": [plan["source"] for plan in plans],
        "blockedFixtureSource": invalid_plan["source"],
        "guardrails": {
            "localStaticFixtureOnly": True,
            "devServerStarted": False,
            "browserAutomationRequired": False,
            **BOUNDARY_FLAGS,
        },
        "plans": plans,
        "blockedExportFixture": invalid_plan,
        "summary": summarize(plans, invalid_plan),
    }


def summarize(plans: list[dict], invalid_plan: dict) -> dict:
    rows = []
    for plan in plans:
        export_step = next(step for step in plan["flow"] if step["id"] == "export")
        rows.append(
            {
                "agent": plan["agent"],
                "source": plan["source"],
                "supported": plan["supported"],
                "targetCount": len(export_step["staticUiExportMatrix"]),
                "readinessStates": sorted(
                    {row["readiness"] for row in export_step["staticUiExportMatrix"]}
                ),
                "paymentAccess": plan["paymentAccess"],
                "runtimeExecutionAllowed": plan["runtimeExecutionAllowed"],
                "mcpInvocation": plan["mcpInvocation"],
            }
        )
    return {
        "coveredAgentCount": len(plans),
        "blockedFixtureStatus": invalid_plan["supported"],
        "blockedFixtureExportStatus": next(
            step for step in invalid_plan["flow"] if step["id"] == "export"
        )["status"],
        "rows": rows,
    }


def render_html(manifest: dict) -> str:
    manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
    rows = "\n".join(render_agent_section(plan) for plan in manifest["plans"])
    blocked = render_blocked_section(manifest["blockedExportFixture"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prosumer Builder Static Export Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #20242b;
      --muted: #5b6472;
      --line: #d8dde5;
      --accent: #2864d8;
      --warn: #8a5a00;
      --bad: #9f243b;
      --good: #1f7a52;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; line-height: 1.15; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    h3 {{ margin: 0 0 8px; font-size: 16px; }}
    p {{ margin: 0 0 12px; color: var(--muted); }}
    .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .stack {{ display: grid; gap: 16px; }}
    .flags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
    .flag {{ border: 1px solid var(--line); border-radius: 999px; padding: 3px 8px; background: #f9fafb; font-size: 12px; }}
    .ok {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border-top: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    code {{ overflow-wrap: anywhere; color: var(--accent); }}
    details {{ margin-top: 12px; }}
    pre {{ max-height: 420px; overflow: auto; background: #111827; color: #eef2ff; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <main class="stack">
    <header>
      <h1>Prosumer Builder Static Export Report</h1>
      <p>Local HTML fixture generated from existing Prosumer Builder plan data. It starts no server, calls no provider, invokes no MCP server, and touches no payment rails.</p>
      <div class="flags">
        {render_guardrail_flags(manifest["guardrails"])}
      </div>
    </header>
    <section class="grid">
      <div class="panel">
        <h2>Coverage</h2>
        <p>{manifest["summary"]["coveredAgentCount"]} supported ADL examples and 1 blocked invalid ADL fixture.</p>
        <p><code>{html.escape(manifest["authoritativePlanCommand"])}</code></p>
      </div>
      <div class="panel">
        <h2>Authoritative Check</h2>
        <p><code>{html.escape(manifest["authoritativeCheck"])}</code></p>
        <p>Embedded JSON below is the deterministic fixture source for this report.</p>
      </div>
    </section>
    {rows}
    {blocked}
    <section class="panel">
      <h2>Embedded Fixture Manifest</h2>
      <details>
        <summary>Show JSON</summary>
        <pre>{html.escape(manifest_json)}</pre>
      </details>
    </section>
  </main>
  <script id="prosumer-static-export-manifest" type="application/json">{html.escape(manifest_json)}</script>
</body>
</html>
"""


def render_guardrail_flags(guardrails: dict) -> str:
    return "\n        ".join(
        f'<span class="flag">{html.escape(key)}={str(value).lower()}</span>'
        for key, value in guardrails.items()
    )


def render_agent_section(plan: dict) -> str:
    export_step = next(step for step in plan["flow"] if step["id"] == "export")
    rows = "\n".join(render_matrix_row(row) for row in export_step["staticUiExportMatrix"])
    return f"""<section class="panel">
      <h2>{html.escape(plan["agent"])}</h2>
      <p><code>{html.escape(plan["source"])}</code></p>
      <table>
        <thead>
          <tr><th>Target</th><th>Readiness</th><th>Command</th><th>Blocked By</th></tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>"""


def render_matrix_row(row: dict) -> str:
    blocked = ", ".join(row["blockedBy"]) if row["blockedBy"] else "none"
    readiness_class = "ok" if row["readiness"] == "report-ready" else "warn"
    if row["readiness"] == "blocked-by-validation":
        readiness_class = "bad"
    return f"""          <tr>
            <td>{html.escape(row["label"])}</td>
            <td class="{readiness_class}">{html.escape(row["readiness"])}</td>
            <td><code>{html.escape(row["command"])}</code></td>
            <td>{html.escape(blocked)}</td>
          </tr>"""


def render_blocked_section(plan: dict) -> str:
    validate_step = next(step for step in plan["flow"] if step["id"] == "validate")
    return f"""<section class="panel">
      <h2>Blocked Export Fixture</h2>
      <p><code>{html.escape(plan["source"])}</code></p>
      <p class="bad">Validation status: {html.escape(validate_step["status"])}</p>
      <p>{html.escape("; ".join(validate_step["errors"]))}</p>
    </section>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--invalid", type=Path, default=DEFAULT_INVALID_EXAMPLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths if args.paths else DEFAULT_EXAMPLES
    manifest = build_manifest(paths, args.invalid)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
