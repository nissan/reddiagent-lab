"""Local source-check gate helpers for ReddiAgent fixture outputs."""

from __future__ import annotations

from typing import Any

from local_tool_registry import APPROVED_SOURCE_TITLES, APPROVED_SOURCE_URLS
from source_check_guidance import guidance_for_source_failure


def check_tool_sources(tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for result in tool_results:
        if result.get("status") != "success":
            continue
        output = result.get("output") or {}
        title = str(output.get("title", ""))
        url = str(output.get("url", ""))
        passed = title in APPROVED_SOURCE_TITLES and url in APPROVED_SOURCE_URLS
        gate_id = "approved-source-output"
        check = {
            "gateId": gate_id,
            "toolId": result["toolId"],
            "status": "pass" if passed else "fail",
            "title": title,
            "url": url,
            "message": (
                "Tool output cites an approved in-repo source."
                if passed
                else "Tool output cites a source outside the approved in-repo source list."
            ),
        }
        if not passed:
            check["guidance"] = guidance_for_source_failure(
                gate_id=gate_id,
                tool_id=result["toolId"],
                title=title,
                url=url,
            ).to_dict()
        checks.append(check)
    return checks


def summarize_source_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    pass_count = sum(1 for check in checks if check["status"] == "pass")
    fail_count = sum(1 for check in checks if check["status"] == "fail")
    return {
        "total": len(checks),
        "passCount": pass_count,
        "failCount": fail_count,
        "requiredFailureCount": fail_count,
        "status": "fail" if fail_count else "pass",
    }
