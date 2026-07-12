#!/usr/bin/env python3
"""Static MCP readiness release checklist drift checks."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "MCP-READINESS-RELEASE-CHECKLIST.md"

REQUIRED_REFERENCES = [
    "tests/MCP-ADAPTER-SHAPE-REPORT.md",
    "tests/MCP-ADAPTER-CONTRACT-REPORT.md",
    "tests/MCP-ADAPTER-ERROR-SEMANTICS-REPORT.md",
    "tests/MCP-ADAPTER-AGGREGATION-REPORT.md",
    "tests/MCP-ADAPTER-SOURCE-CHECK-REPORT.md",
    "tests/MCP-SERVER-RESOLUTION-REPORT.md",
    "tests/MCP-CAPABILITY-POLICY-REPORT.md",
    "tests/MCP-READINESS-EVIDENCE-REPORT.md",
    "docs/LOCAL-RUNNER-READINESS-BUNDLE.md",
    "tests/smoke-validation.sh",
    "tests/test_adapter_readiness.py",
    "tests/test_mcp_adapter_contract.py",
    "tests/test_mcp_adapter_error_semantics.py",
    "tests/test_mcp_adapter_aggregation.py",
    "tests/test_mcp_adapter_source_check.py",
    "tests/test_mcp_server_resolution.py",
    "tests/test_mcp_capability_policy.py",
    "tests/test_mcp_readiness_evidence.py",
    "tests/test_readiness_bundle.py",
    "networkAccess=false",
    "mcpInvocation=false",
    "paymentAccess=false",
    "No live MCP server resolution or invocation has been implemented.",
    "Do not resolve or invoke MCP servers yet.",
]


def main() -> int:
    checklist = CHECKLIST.read_text()

    for reference in REQUIRED_REFERENCES:
        assert reference in checklist, f"Missing MCP readiness release reference: {reference}"

    review_items = [line for line in checklist.splitlines() if line.startswith("- [ ] ")]
    assert len(review_items) >= 8, "MCP readiness release checklist is too thin."

    print("PASS MCP readiness release checklist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
