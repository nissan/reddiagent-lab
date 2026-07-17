#!/usr/bin/env python3
"""Check the ReddiAgent public-review blog draft contract."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "docs" / "blog" / "2026-07-18-reddiagent-open-specs-call-for-review.md"
INDEX = ROOT / "docs" / "INDEX.md"
README = ROOT / "README.md"

REQUIRED_POST_MARKERS = [
    "Draft only; not externally published.",
    "docs/OPEN-SPECS-EXPLAINER.md",
    "docs/PROTECTED-DOCS-PACKAGE.md",
    "specs/ADL-v0.1.md",
    "specs/ADL-v0.1.schema.json",
    "specs/DOMAIN-MODEL-v0.1.md",
    "examples/simple-agent.yaml",
    "examples/tool-agent.yaml",
    "examples/mcp-readonly-agent.yaml",
    "examples/payment-agent.yaml",
    "Stable enough for review and references",
    "Experimental",
    "Report-only",
    "Executable prototype track",
    "Future work",
    "/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py examples/tool-agent.yaml",
    "tests/smoke-validation.sh",
    "tests/PROTECTED-DOCS-PACKAGE-REPORT.md",
    "The next queued issue, `#227`, will add the open-spec review submission template and intake notes.",
    "Do not publish this post externally until Nissan approves",
    "Mainnet remains outside current approval.",
    "This draft is documentation only.",
]

FORBIDDEN_POST_MARKERS = [
    "published at http",
    "published at https",
    "live at http",
    "live at https",
    "mainnet is approved",
]


def main() -> int:
    post = POST.read_text()
    index = INDEX.read_text()
    readme = README.read_text()
    relative_post = "docs/blog/2026-07-18-reddiagent-open-specs-call-for-review.md"

    for marker in REQUIRED_POST_MARKERS:
        assert marker in post, f"Missing blog marker: {marker}"

    lowered = post.lower()
    for marker in FORBIDDEN_POST_MARKERS:
        assert marker not in lowered, f"Forbidden publication marker: {marker}"

    assert relative_post in index
    assert relative_post in readme

    print("PASS public blog draft")
    return 0


if __name__ == "__main__":
    sys.exit(main())
