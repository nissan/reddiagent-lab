#!/usr/bin/env python3
"""Build the protected publishable documentation package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_FLAGS = {
    "runtimeExecutionAllowed": False,
    "networkAccess": False,
    "paymentAccess": False,
    "mcpInvocation": False,
    "providerModelApiCalls": False,
    "credentialLookupOrStorage": False,
    "deploymentAllowed": False,
    "publishingAllowed": False,
    "universalPasswordSelected": False,
    "writesRuntimeCode": False,
}
ACCESS_MODEL = {
    "mode": "protected-static-share",
    "recommendedProtection": "single shared password or equivalent platform access control selected outside this repo at publish time",
    "passwordStorage": "do not commit or generate the password in this repository",
    "advisorSharing": "share URL and password/access grant out-of-band after Nissan approves the deployment target",
    "rotation": "rotate by changing the hosting/access-control layer, not repo docs",
}
CRAWLER_CONTROLS = {
    "robotsTxt": "User-agent: *\nDisallow: /\n",
    "htmlMetaRobots": "noindex, nofollow, noarchive",
    "httpHeader": "X-Robots-Tag: noindex, nofollow, noarchive",
    "sitemap": "omit sitemap.xml for protected package",
}
STATIC_PACKAGE_ARTIFACTS = [
    {
        "path": "docs/publishable-package/index.html",
        "status": "planned-static-artifact",
        "purpose": "Partner/advisor landing page with links to packaged docs sections.",
    },
    {
        "path": "docs/publishable-package/robots.txt",
        "status": "planned-static-artifact",
        "purpose": "Default crawler exclusion for the whole protected package.",
    },
    {
        "path": "docs/publishable-package/noindex-headers.txt",
        "status": "planned-static-artifact",
        "purpose": "Hosting header reminder for X-Robots-Tag controls.",
    },
    {
        "path": "docs/publishable-package/package-manifest.json",
        "status": "generated-by-this-script",
        "purpose": "Machine-readable package contents, access model, and guardrails.",
    },
]
CONTENT_SECTIONS = [
    {
        "id": "entrypoints",
        "label": "Entrypoints",
        "required": [
            "README.md",
            "docs/INDEX.md",
            "docs/REDDIAGENT-VISION-ROADMAP.md",
            "docs/PROTECTED-DOCS-PACKAGE.md",
        ],
    },
    {
        "id": "roadmap",
        "label": "Roadmap and backlog",
        "required": [
            "docs/ROADMAP.md",
            "docs/IMPLEMENTATION-BACKLOG.md",
            "docs/NEXT-10-IMPLEMENTATION-ISSUES.md",
        ],
    },
    {
        "id": "architecture",
        "label": "Architecture",
        "required": [
            "docs/REDDIAGENT-ARCHITECTURE.md",
            "docs/ARCHITECTURE-THESIS.md",
            "docs/PRODUCT-PRINCIPLES.md",
            "docs/POSITIONING-MEMO.md",
        ],
    },
    {
        "id": "decisions",
        "label": "ADR register",
        "required": [
            "docs/adr/0000-adr-index.md",
            "docs/adr/0001-adl-is-the-canonical-source-of-truth.md",
            "docs/adr/0002-static-compatibility-before-runtime-execution.md",
            "docs/adr/0003-harness-is-a-first-class-product-surface.md",
            "docs/adr/0004-mcp-and-payment-boundaries-fail-closed.md",
            "docs/adr/0005-receipts-and-reputation-layer-above-payment-evidence.md",
            "docs/adr/0006-provider-adapters-start-as-compatibility-reports.md",
            "docs/adr/0007-vercel-eve-is-a-static-export-target.md",
        ],
    },
    {
        "id": "specs",
        "label": "Specs",
        "required": [
            "specs/ADL-v0.1.md",
            "specs/DOMAIN-MODEL-v0.1.md",
            "specs/PROVIDER-MAPPING-v0.1.md",
            "specs/HARNESS-LIFECYCLE-v0.1.md",
            "specs/RUNTIME-DEPLOYMENT-v0.1.md",
            "specs/SECURITY-PERMISSIONS-v0.1.md",
            "specs/OBSERVABILITY-v0.1.md",
            "specs/CONFORMANCE-v0.1.md",
            "specs/RAP-BRIDGE-v0.1.md",
            "specs/X402-DRY-RUN-RECEIPT-v0.1.md",
            "specs/REPUTATION-SIGNALS-v0.1.md",
        ],
    },
    {
        "id": "mappings",
        "label": "Mappings",
        "required": [
            "mappings/AGENT-SPEC.md",
            "mappings/OPENAI.md",
            "mappings/ANTHROPIC.md",
            "mappings/GEMINI.md",
            "mappings/LANGGRAPH.md",
            "mappings/LLAMAINDEX.md",
            "mappings/STRANDS.md",
        ],
    },
    {
        "id": "research",
        "label": "Research entrypoints",
        "required": [
            "research/RESEARCH-TAXONOMY.md",
            "research/SOURCE-MAP.md",
            "research/FRAMEWORK-MATRIX.md",
            "research/PLATFORM-MATRIX.md",
            "research/HOMEBREW-OPEN-SOURCE-MATRIX.md",
            "research/2026-07-08-x402-mcp-micropayments.md",
            "research/2026-07-17-vercel-eve-impact.md",
        ],
    },
    {
        "id": "evidence",
        "label": "Evidence reports",
        "required": [
            "tests/AGENT-SPEC-COMPATIBILITY-REPORT.md",
            "tests/MCP-READINESS-EVIDENCE-REPORT.md",
            "tests/RAP-BRIDGE-REPORT.md",
            "tests/STATIC-EXPORT-TARGET-PARITY-MATRIX-REPORT.md",
            "tests/PROTECTED-DOCS-PACKAGE-REPORT.md",
        ],
    },
]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path_text: str) -> dict:
    path = ROOT / path_text
    exists = path.exists()
    record = {
        "path": path_text,
        "exists": exists,
        "kind": "file" if path.is_file() else "missing",
    }
    if exists and path.is_file():
        record["sha256"] = file_digest(path)
        record["bytes"] = path.stat().st_size
    return record


def section_record(section: dict) -> dict:
    files = [file_record(path) for path in section["required"]]
    missing = [item["path"] for item in files if not item["exists"]]
    return {
        "id": section["id"],
        "label": section["label"],
        "status": "ready" if not missing else "blocked-missing-files",
        "requiredCount": len(files),
        "missing": missing,
        "files": files,
    }


def package_manifest() -> dict:
    sections = [section_record(section) for section in CONTENT_SECTIONS]
    missing = [
        missing_path
        for section in sections
        for missing_path in section["missing"]
    ]
    return {
        "format": "protected-docs-package-manifest",
        "issue": 210,
        "parentEpic": 206,
        "status": "ready-for-static-package-review" if not missing else "blocked-missing-files",
        "packageIntent": "Prepare a protected, noindex documentation package for partner/advisor review without deploying it.",
        "accessModel": ACCESS_MODEL,
        "crawlerControls": CRAWLER_CONTROLS,
        "staticPackageArtifacts": STATIC_PACKAGE_ARTIFACTS,
        "contentSections": sections,
        "missingRequiredFiles": missing,
        "separationOfConcerns": {
            "publicDocsConcern": "Curated narrative and navigation surfaces only.",
            "protectedDocsConcern": "Password/access-controlled static package with noindex controls.",
            "runtimeCodeConcern": "Runtime code, credentials, provider calls, MCP invocation, payment rails, and deployment remain outside this package.",
        },
        "approvalGate": {
            "deploymentRequiresNissanApproval": True,
            "passwordSelectionRequiresNissanApproval": True,
            "mainnetAllowed": False,
            "allowedNow": "static manifest review and local package planning only",
        },
        **BOUNDARY_FLAGS,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated manifest JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = package_manifest()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if payload["status"] == "ready-for-static-package-review" else 1


if __name__ == "__main__":
    sys.exit(main())
