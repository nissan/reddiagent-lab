#!/usr/bin/env python3
"""Build a deterministic local beta review UI for runtime package artifacts."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package.json"
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "beta-operator-dry-run-package-scenarios.json"
DEFAULT_HTML = ROOT / "docs" / "beta-review-ui.html"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_operator_dry_run_package  # noqa: E402


SENSITIVE_KEYS = {
    "apiKey",
    "api_key",
    "authorization",
    "credential",
    "credentials",
    "password",
    "paymentProof",
    "privateKey",
    "rawPrompt",
    "rawSecret",
    "secret",
    "token",
    "walletHandle",
}
SENSITIVE_VALUE_MARKERS = (
    "begin private key",
    "sk-",
    "ghp_",
    "xoxb-",
    "authorization:",
    "api_key=",
    "password=",
    "private_key=",
)
REQUIRED_EVIDENCE = {
    "tests/fixtures/beta-local-runtime-rc-gate.json",
    "tests/fixtures/beta-local-runtime-rc-gate-scenarios.json",
    "tests/fixtures/beta-release-readiness.json",
    "tests/fixtures/beta-operator-control-harness.json",
    "tests/fixtures/local-executable-runtime-prototype.json",
    "tests/fixtures/beta-operator-dry-run-package-scenarios.json",
}
REQUIRED_STOP_EVENTS = {"runtime.disabled", "rollback.started", "rollback.completed"}
REQUIRED_BOUNDARY_FALSE = {
    "liveRuntimeActivation",
    "networkAccess",
    "credentialAccess",
    "mcpInvocation",
    "paymentAccess",
    "providerApiAccess",
    "devnetAccess",
    "productionGatewayAccess",
    "mainnetAccess",
    "externalSpend",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return doc


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def finding(path: str, reason: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def recursive_sensitive_findings(value: Any, path: str = "$") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in SENSITIVE_KEYS:
                findings.append(finding(child_path, "Credential-like or private payload key is not allowed in the review UI artifact."))
            findings.extend(recursive_sensitive_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(recursive_sensitive_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            findings.append(finding(path, "Credential-like or private payload value is not allowed in the review UI artifact."))
    return findings


def result_by_kind(package: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [result for result in package.get("results", []) if result.get("kind") == kind]


def positive_result(package: dict[str, Any]) -> dict[str, Any] | None:
    positives = result_by_kind(package, "positive")
    return positives[0] if positives else None


def fail_closed_cues(package: dict[str, Any]) -> list[dict[str, Any]]:
    cues = []
    for result in result_by_kind(package, "negative"):
        cues.append(
            {
                "id": result.get("id"),
                "status": result.get("status"),
                "failClosed": result.get("status") == "fail" and bool(result.get("findings")),
                "findingPaths": [item.get("path") for item in result.get("findings", [])],
            }
        )
    return cues


def validate_package(package: dict[str, Any], current_package: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    positive = positive_result(package)

    if package.get("status") != "pass":
        findings.append(finding("package.status", "Runtime package artifact must pass before UI export."))
    if current_package != package:
        findings.append(finding("package.currentEvidence", "Current package output must match the pinned package artifact."))
    if positive is None:
        findings.append(finding("package.results", "A passing positive runtime package scenario is required."))
        return findings

    if positive.get("status") != "pass":
        findings.append(finding("positive.status", "Positive runtime package scenario must pass."))
    if not positive.get("selectedAdlPath"):
        findings.append(finding("positive.selectedAdlPath", "Selected ADL path is required."))
    elif not (ROOT / str(positive["selectedAdlPath"])).exists():
        findings.append(finding("positive.selectedAdlPath", "Selected ADL path must exist locally."))

    rc_gate = positive.get("rcGateEvidence", {})
    if rc_gate.get("status") != "pass":
        findings.append(finding("positive.rcGateEvidence.status", "RC gate evidence must pass."))
    if rc_gate.get("currentEvidenceMatchesPinned") is not True:
        findings.append(finding("positive.rcGateEvidence.currentEvidenceMatchesPinned", "RC gate evidence must match the pinned artifact."))
    if "not approved" not in str(rc_gate.get("mainnetStatement", "")).lower():
        findings.append(finding("positive.rcGateEvidence.mainnetStatement", "Mainnet-not-approved language is required."))

    boundaries = package.get("boundaries", {})
    for key in REQUIRED_BOUNDARY_FALSE:
        if boundaries.get(key) is not False:
            findings.append(finding(f"package.boundaries.{key}", f"{key} must be false for the local review UI."))

    if positive.get("liveRuntimeRequested") is not False:
        findings.append(finding("positive.liveRuntimeRequested", "Live runtime requests fail closed for review UI export."))
    if positive.get("mainnetRequested") is not False:
        findings.append(finding("positive.mainnetRequested", "Mainnet requests fail closed for review UI export."))

    evidence_index = positive.get("evidenceIndex", [])
    evidence_paths = {item.get("path") for item in evidence_index if isinstance(item, dict)}
    missing = sorted(REQUIRED_EVIDENCE - evidence_paths)
    if missing:
        findings.append(finding("positive.evidenceIndex", f"Missing evidence index entries: {', '.join(missing)}"))
    for index, item in enumerate(evidence_index):
        if not item.get("exists") or not item.get("sha256"):
            findings.append(finding(f"positive.evidenceIndex[{index}]", "Evidence index entries must exist and include sha256 hashes."))

    stop_events = {
        entry.get("event")
        for entry in positive.get("stopRollbackDryRunTranscript", [])
        if "--dry-run" in str(entry.get("command", "")) and entry.get("exitCode") == 0
    }
    if not REQUIRED_STOP_EVENTS <= stop_events:
        findings.append(finding("positive.stopRollbackDryRunTranscript", "Disable, rollback start, and rollback complete dry-run events are required."))

    cues = fail_closed_cues(package)
    if not cues:
        findings.append(finding("package.results", "At least one negative fail-closed scenario is required."))
    for cue in cues:
        if cue["failClosed"] is not True:
            findings.append(finding(f"negative.{cue['id']}", "Negative scenarios must fail closed with findings."))
    cue_paths = {path for cue in cues for path in cue["findingPaths"]}
    if "liveRuntimeRequested" not in cue_paths:
        findings.append(finding("negative.liveRuntimeRequested", "A live runtime request must be represented as a fail-closed cue."))
    if "mainnetRequested" not in cue_paths:
        findings.append(finding("negative.mainnetRequested", "A mainnet request must be represented as a fail-closed cue."))

    findings.extend(recursive_sensitive_findings(package, "package"))
    return findings


def build_review(package: dict[str, Any], current_package: dict[str, Any], package_path: Path) -> dict[str, Any]:
    validation_findings = validate_package(package, current_package)
    positive = positive_result(package) or {}
    rc_gate = positive.get("rcGateEvidence", {})
    review = {
        "mode": "beta-runtime-package-review-ui",
        "issue": 246,
        "parentEpic": 220,
        "status": "pass" if not validation_findings else "fail",
        "findings": validation_findings,
        "sourcePackage": rel_path(package_path),
        "releaseId": package.get("releaseId"),
        "selectedAdlPath": positive.get("selectedAdlPath"),
        "operatorIdentity": positive.get("operatorIdentity"),
        "rcGateStatus": rc_gate.get("status"),
        "currentEvidenceMatchesPinned": rc_gate.get("currentEvidenceMatchesPinned"),
        "runtimeMode": positive.get("runtimeMode"),
        "environment": positive.get("environment"),
        "boundaries": package.get("boundaries"),
        "reviewPanels": [
            {
                "id": "package-summary",
                "title": "Package Summary",
                "rows": [
                    {"label": "Release", "value": package.get("releaseId")},
                    {"label": "Selected ADL", "value": positive.get("selectedAdlPath")},
                    {"label": "RC gate", "value": rc_gate.get("status")},
                    {"label": "Pinned evidence", "value": "matches" if rc_gate.get("currentEvidenceMatchesPinned") else "stale"},
                ],
            },
            {
                "id": "operator-transcript",
                "title": "Operator Transcript",
                "rows": positive.get("operatorCommandTranscript", []),
            },
            {
                "id": "rollback-transcript",
                "title": "Stop And Rollback",
                "rows": positive.get("stopRollbackDryRunTranscript", []),
            },
            {
                "id": "evidence-index",
                "title": "Evidence Index",
                "rows": positive.get("evidenceIndex", []),
            },
            {
                "id": "fail-closed-cues",
                "title": "Fail-Closed Cues",
                "rows": fail_closed_cues(package),
            },
        ],
        "htmlPath": rel_path(DEFAULT_HTML),
    }
    review["html"] = render_html(review)
    return review


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def status_class(value: Any) -> str:
    return "pass" if value in {True, "pass", "matches"} else "fail" if value in {False, "fail", "stale"} else "muted"


def render_rows(rows: list[Any]) -> str:
    rendered = []
    for row in rows:
        if isinstance(row, dict):
            cells = "".join(f"<td>{esc(key)}</td><td>{esc(value)}</td>" for key, value in row.items())
            rendered.append(f"<tr>{cells}</tr>")
        else:
            rendered.append(f"<tr><td>{esc(row)}</td></tr>")
    return "\n".join(rendered)


def render_panel(panel: dict[str, Any]) -> str:
    rows = panel.get("rows", [])
    if panel["id"] == "package-summary":
        content = "\n".join(
            f"<div class=\"summary-row\"><span>{esc(row['label'])}</span><strong class=\"{status_class(row['value'])}\">{esc(row['value'])}</strong></div>"
            for row in rows
        )
    else:
        content = f"<table><tbody>{render_rows(rows)}</tbody></table>"
    return f"""<section id="{esc(panel['id'])}">
  <h2>{esc(panel['title'])}</h2>
  {content}
</section>"""


def render_html(review: dict[str, Any]) -> str:
    panels = "\n".join(render_panel(panel) for panel in review["reviewPanels"])
    boundaries = "\n".join(
        f"<li><span>{esc(key)}</span><strong class=\"{status_class(value)}\">{esc(value)}</strong></li>"
        for key, value in sorted((review.get("boundaries") or {}).items())
    )
    findings = "\n".join(
        f"<li><strong>{esc(item['path'])}</strong>: {esc(item['reason'])}</li>"
        for item in review.get("findings", [])
    ) or "<li>No export blockers.</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReddiAgent Beta Review UI</title>
  <style>
    :root {{ color-scheme: light; --ink: #17201b; --muted: #5b675f; --line: #cbd8d0; --panel: #f7f9f7; --good: #11643d; --bad: #9d2830; --warn: #7d5a11; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #ffffff; }}
    header {{ padding: 28px 32px 18px; border-bottom: 1px solid var(--line); }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px 28px 36px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; color: var(--muted); font-size: 14px; }}
    .badge {{ border: 1px solid var(--line); padding: 4px 8px; border-radius: 6px; background: var(--panel); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 16px; align-items: start; }}
    section {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: var(--panel); overflow: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    td {{ border-top: 1px solid var(--line); padding: 8px 6px; vertical-align: top; overflow-wrap: anywhere; }}
    .summary-row, .boundaries li {{ display: flex; justify-content: space-between; gap: 16px; padding: 7px 0; border-top: 1px solid var(--line); }}
    .boundaries {{ list-style: none; margin: 0; padding: 0; font-size: 13px; }}
    .pass {{ color: var(--good); }}
    .fail {{ color: var(--bad); }}
    .muted {{ color: var(--muted); }}
    .findings {{ margin: 16px 0; }}
    .findings li {{ margin: 6px 0; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1>ReddiAgent Beta Review UI</h1>
    <div class="meta">
      <span class="badge">Issue #{esc(review["issue"])}</span>
      <span class="badge">Status: {esc(review["status"])}</span>
      <span class="badge">Release: {esc(review.get("releaseId"))}</span>
      <span class="badge">ADL: {esc(review.get("selectedAdlPath"))}</span>
      <span class="badge">Local only</span>
    </div>
  </header>
  <main>
    <section class="findings">
      <h2>Export Gate</h2>
      <ul>{findings}</ul>
    </section>
    <section>
      <h2>Boundary Status</h2>
      <ul class="boundaries">{boundaries}</ul>
    </section>
    <div class="grid">{panels}</div>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", nargs="?", default=str(DEFAULT_PACKAGE))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html-output", type=Path)
    args = parser.parse_args()

    package_path = Path(args.package)
    package = load_json(package_path)
    current_package = beta_operator_dry_run_package.build_report(load_json(DEFAULT_SCENARIOS))
    review = build_review(package, current_package, package_path)
    html_payload = review.pop("html")
    json_payload = json.dumps(review, indent=2, sort_keys=True) + "\n"

    if args.output:
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_payload)
    if args.html_output:
        html_path = args.html_output if args.html_output.is_absolute() else ROOT / args.html_output
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_payload)
    sys.stdout.write(json_payload)
    return 0 if review["status"] == "pass" else 3


if __name__ == "__main__":
    sys.exit(main())
