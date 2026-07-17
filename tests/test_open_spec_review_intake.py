#!/usr/bin/env python3
"""Check the ReddiAgent open-spec review intake contract."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "docs" / "OPEN-SPEC-REVIEW-INTAKE.md"
TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "open-spec-review.md"
EXPLAINER = ROOT / "docs" / "OPEN-SPECS-EXPLAINER.md"
BLOG = ROOT / "docs" / "blog" / "2026-07-18-reddiagent-open-specs-call-for-review.md"
INDEX = ROOT / "docs" / "INDEX.md"
README = ROOT / "README.md"

REQUIRED_INTAKE_MARKERS = [
    "Issue #227. Parent epic: #206.",
    ".github/ISSUE_TEMPLATE/open-spec-review.md",
    "reviewer role",
    "target file, section, example, mapping, fixture, or evidence report",
    "stable, experimental, report-only, executable prototype, or future work",
    "suggested acceptance criteria",
    "prototype/beta separation notes",
    "#220 prototype/beta track",
    "Docs-only corrections",
    "Prototype and Beta Feedback",
    "Mainnet deployment and mainnet runs remain future work",
    "does not publish docs, deploy a site, call provider APIs, invoke MCP servers, access credentials, touch wallets, run devnet/mainnet transactions",
]

REQUIRED_TEMPLATE_MARKERS = [
    "Reviewer Role",
    "Target Surface",
    "State Classification",
    "Problem or Improvement",
    "Suggested Acceptance Criteria",
    "Prototype/Beta Separation",
    "Evidence or Reproduction",
    "Proposed Backlog Shape",
    "Do not include secrets",
    "stable, experimental, report-only, executable prototype, future work",
    "#220 prototype/beta track",
]


def main() -> int:
    intake = INTAKE.read_text()
    template = TEMPLATE.read_text()
    explainer = EXPLAINER.read_text()
    blog = BLOG.read_text()
    index = INDEX.read_text()
    readme = README.read_text()

    for marker in REQUIRED_INTAKE_MARKERS:
        assert marker in intake, f"Missing intake marker: {marker}"

    for marker in REQUIRED_TEMPLATE_MARKERS:
        assert marker in template, f"Missing template marker: {marker}"

    for text in (explainer, blog, index, readme):
        assert "docs/OPEN-SPEC-REVIEW-INTAKE.md" in text

    assert ".github/ISSUE_TEMPLATE/open-spec-review.md" in explainer
    assert ".github/ISSUE_TEMPLATE/open-spec-review.md" in blog

    print("PASS open spec review intake")
    return 0


if __name__ == "__main__":
    sys.exit(main())
