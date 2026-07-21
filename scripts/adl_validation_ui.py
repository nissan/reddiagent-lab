#!/usr/bin/env python3
"""Generate a local/static ADL validation UI prototype."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import sys

import jsonschema
import yaml

from validation_guidance import format_errors


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "ADL-v0.1.schema.json"
DEFAULT_OUTPUT = ROOT / "docs" / "adl-validation-ui.html"
EXAMPLES = [
    ("simple", ROOT / "examples" / "simple-agent.yaml", "Simple local agent"),
    ("tool", ROOT / "examples" / "tool-agent.yaml", "Tool fixture agent"),
    ("payment", ROOT / "examples" / "payment-agent.yaml", "Payment metadata agent"),
    (
        "invalid-missing-instructions",
        ROOT / "examples" / "invalid" / "missing-instructions.yaml",
        "Invalid: missing instructions",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def validate_payload(path: Path, validator: jsonschema.Draft202012Validator) -> dict:
    data = yaml.safe_load(path.read_text())
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    guidance = [item.to_dict() for item in format_errors(errors, path)]
    return {
        "status": "fail" if guidance else "pass",
        "errorCount": len(guidance),
        "errors": guidance,
    }


def build_manifest() -> dict:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    examples = []
    for key, path, label in EXAMPLES:
        examples.append(
            {
                "key": key,
                "label": label,
                "path": str(path.relative_to(ROOT)),
                "source": path.read_text(),
                "validation": validate_payload(path, validator),
            }
        )
    return {
        "generatedBy": "scripts/adl_validation_ui.py",
        "schema": "specs/ADL-v0.1.schema.json",
        "authoritativeCommand": "python3 scripts/validate_examples.py --format json <adl-path>",
        "guardrails": {
            "localPrototypeOnly": True,
            "runtimeExecutionAllowed": False,
            "networkAccess": False,
            "providerCalls": False,
            "mcpInvocation": False,
            "paymentAccess": False,
            "credentialAccess": False,
            "deploymentAllowed": False,
        },
        "examples": examples,
    }


def render_html(manifest: dict) -> str:
    manifest_json = json.dumps(manifest, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReddiAgent ADL Validation Prototype</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18202a;
      --muted: #5d6876;
      --line: #d6dde6;
      --panel: #f7f9fb;
      --ok: #0f7b55;
      --warn: #a54700;
      --fail: #b42318;
      --blue: #1f5eff;
      --gold: #f2b84b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding: 18px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
    main {{
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
      min-height: calc(100vh - 73px);
    }}
    aside {{
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 18px;
    }}
    section {{ padding: 18px 20px; min-width: 0; }}
    .control-group {{ display: grid; gap: 10px; margin-bottom: 18px; }}
    .segmented {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }}
    .segmented button {{
      border: 0;
      border-right: 1px solid var(--line);
      background: #fff;
      padding: 9px 10px;
      font: inherit;
      cursor: pointer;
    }}
    .segmented button:last-child {{ border-right: 0; }}
    .segmented button[aria-pressed="true"] {{
      color: #fff;
      background: var(--blue);
    }}
    label {{ color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    select, textarea, button.primary {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }}
    select, button.primary {{ min-height: 40px; padding: 8px 10px; }}
    textarea {{
      min-height: 440px;
      resize: vertical;
      padding: 12px;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    button.primary {{
      border-color: var(--blue);
      color: #fff;
      background: var(--blue);
      cursor: pointer;
      font-weight: 700;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 3px 10px;
      border-radius: 999px;
      font-weight: 700;
      border: 1px solid var(--line);
      background: #fff;
    }}
    .status.pass {{ color: var(--ok); border-color: #9bd6bf; }}
    .status.fail {{ color: var(--fail); border-color: #f0a7a2; }}
    .summary {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 70px;
    }}
    .metric strong {{ display: block; font-size: 18px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    .results {{
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }}
    .finding {{
      border: 1px solid var(--line);
      border-left: 4px solid var(--gold);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }}
    .finding.fail {{ border-left-color: var(--fail); }}
    .finding h3 {{ margin: 0 0 6px; font-size: 14px; }}
    .finding p {{ margin: 4px 0; color: var(--muted); }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: #eef2f7;
      padding: 1px 4px;
      border-radius: 4px;
    }}
    .guardrails {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .guardrails div {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 8px;
      color: var(--muted);
    }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 820px) {{
      main {{ grid-template-columns: 1fr; }}
      aside {{ border-right: 0; border-bottom: 1px solid var(--line); }}
      .grid, .guardrails {{ grid-template-columns: 1fr; }}
      textarea {{ min-height: 320px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>ADL Validation Prototype</h1>
    <span class="status" id="mode-status">Local static UI</span>
  </header>
  <main>
    <aside>
      <div class="control-group">
        <label>Input mode</label>
        <div class="segmented" role="group" aria-label="Input mode">
          <button id="mode-example" type="button" aria-pressed="true">Bundled</button>
          <button id="mode-paste" type="button" aria-pressed="false">Pasted</button>
        </div>
      </div>
      <div class="control-group" id="example-controls">
        <label for="example-select">Bundled example</label>
        <select id="example-select"></select>
      </div>
      <div class="control-group">
        <label for="adl-input">ADL YAML</label>
        <textarea id="adl-input" spellcheck="false"></textarea>
      </div>
      <button class="primary" id="validate-button" type="button">Validate ADL</button>
      <p class="muted">Authoritative local command: <code>{html.escape(manifest["authoritativeCommand"])}</code></p>
    </aside>
    <section>
      <div class="summary">
        <span class="status" id="validation-status">Not run</span>
        <span class="muted" id="source-label"></span>
      </div>
      <div class="grid">
        <div class="metric"><strong id="error-count">0</strong><span>validation findings</span></div>
        <div class="metric"><strong id="runtime-flag">false</strong><span>runtime execution allowed</span></div>
        <div class="metric"><strong id="network-flag">false</strong><span>network access</span></div>
      </div>
      <div class="guardrails" id="guardrails"></div>
      <div class="results" id="results"></div>
    </section>
  </main>
  <script id="adl-ui-manifest" type="application/json">{html.escape(manifest_json)}</script>
  <script>
    const manifest = JSON.parse(document.getElementById("adl-ui-manifest").textContent);
    const state = {{ mode: "example", activeKey: manifest.examples[0].key }};
    const select = document.getElementById("example-select");
    const input = document.getElementById("adl-input");
    const results = document.getElementById("results");
    const statusEl = document.getElementById("validation-status");
    const sourceLabel = document.getElementById("source-label");
    const errorCount = document.getElementById("error-count");
    const runtimeFlag = document.getElementById("runtime-flag");
    const networkFlag = document.getElementById("network-flag");
    const guardrails = document.getElementById("guardrails");
    const exampleControls = document.getElementById("example-controls");
    const modeExample = document.getElementById("mode-example");
    const modePaste = document.getElementById("mode-paste");

    function activeExample() {{
      return manifest.examples.find((item) => item.key === state.activeKey) || manifest.examples[0];
    }}

    function setMode(mode) {{
      state.mode = mode;
      modeExample.setAttribute("aria-pressed", String(mode === "example"));
      modePaste.setAttribute("aria-pressed", String(mode === "paste"));
      exampleControls.hidden = mode !== "example";
      if (mode === "example") {{
        input.value = activeExample().source;
        renderValidation(activeExample().validation, activeExample().path);
      }} else {{
        sourceLabel.textContent = "Pasted ADL - prototype browser checks";
        renderValidation(validatePastedAdl(input.value), "pasted ADL");
      }}
    }}

    function renderGuardrails() {{
      guardrails.innerHTML = "";
      Object.entries(manifest.guardrails).forEach(([key, value]) => {{
        const item = document.createElement("div");
        item.innerHTML = `<strong>${{key}}</strong><br><code>${{String(value)}}</code>`;
        guardrails.appendChild(item);
      }});
    }}

    function renderValidation(validation, source) {{
      const passed = validation.status === "pass";
      statusEl.className = `status ${{validation.status}}`;
      statusEl.textContent = passed ? "PASS" : "FAIL";
      sourceLabel.textContent = source;
      errorCount.textContent = String(validation.errorCount);
      runtimeFlag.textContent = String(manifest.guardrails.runtimeExecutionAllowed);
      networkFlag.textContent = String(manifest.guardrails.networkAccess);
      results.innerHTML = "";

      if (passed) {{
        const ok = document.createElement("div");
        ok.className = "finding";
        ok.innerHTML = "<h3>Schema validation passed</h3><p>This view is local/static and does not run the agent.</p>";
        results.appendChild(ok);
        return;
      }}

      validation.errors.forEach((finding) => {{
        const node = document.createElement("div");
        node.className = "finding fail";
        node.innerHTML = `
          <h3>${{finding.location || "ADL"}}: ${{finding.problem || "Validation finding"}}</h3>
          <p><strong>Fix:</strong> ${{finding.fix || "Update the ADL and rerun the local validator."}}</p>
          <p><strong>Reference:</strong> <code>${{finding.reference || manifest.schema}}</code></p>
          <p>${{finding.rationale || "The static UI keeps runtime behavior disabled."}}</p>
        `;
        results.appendChild(node);
      }});
    }}

    function hasPattern(text, pattern) {{
      return pattern.test(text);
    }}

    function validatePastedAdl(text) {{
      const findings = [];
      const checks = [
        ["apiVersion", /^apiVersion:\\s*reddiagent\\.dev\\/v0\\.1\\s*$/m, "Set apiVersion to reddiagent.dev/v0.1."],
        ["kind", /^kind:\\s*Agent\\s*$/m, "Set kind to Agent."],
        ["metadata.name", /^\\s{{2}}name:\\s*[a-z0-9][a-z0-9-]{{1,62}}\\s*$/m, "Use a lowercase kebab-case metadata.name."],
        ["metadata.description", /^\\s{{2}}description:\\s*\\S/m, "Add a non-empty metadata.description."],
        ["model.capability", /^\\s{{2}}capability:\\s*(chat|reasoning|code|vision|audio|embedding|reranking)\\s*$/m, "Use a supported model capability."],
        ["model.providers.preferred", /^\\s{{4}}preferred:\\s*\\S/m, "Choose a preferred provider name as metadata only."],
        ["model.requirements", /^\\s{{2}}requirements:\\s*$/m, "Declare model requirements."],
        ["harness.instructions", /^\\s{{2}}instructions:\\s*$/m, "Add harness instructions."],
        ["harness.runtime.target", /^\\s{{4}}target:\\s*(local-python|hosted-container|serverless|platform-native|openclaw)\\s*$/m, "Use a supported runtime target."],
      ];
      checks.forEach(([location, pattern, fix]) => {{
        if (!hasPattern(text, pattern)) {{
          findings.push({{
            location,
            problem: "Missing or unsupported field in prototype check.",
            fix,
            reference: manifest.schema,
            rationale: "Browser checks are a local preview of the Python JSON Schema validator."
          }});
        }}
      }});
      return {{ status: findings.length ? "fail" : "pass", errorCount: findings.length, errors: findings }};
    }}

    manifest.examples.forEach((item) => {{
      const option = document.createElement("option");
      option.value = item.key;
      option.textContent = `${{item.label}} (${{item.path}})`;
      select.appendChild(option);
    }});
    select.addEventListener("change", () => {{
      state.activeKey = select.value;
      input.value = activeExample().source;
      renderValidation(activeExample().validation, activeExample().path);
    }});
    modeExample.addEventListener("click", () => setMode("example"));
    modePaste.addEventListener("click", () => setMode("paste"));
    document.getElementById("validate-button").addEventListener("click", () => {{
      if (state.mode === "example" && input.value === activeExample().source) {{
        renderValidation(activeExample().validation, activeExample().path);
      }} else {{
        setMode("paste");
      }}
    }});
    input.value = activeExample().source;
    renderGuardrails();
    renderValidation(activeExample().validation, activeExample().path);
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(build_manifest()))
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(f"Wrote {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
