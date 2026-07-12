#!/usr/bin/env python3
"""Static aggregation checks for deterministic MCP adapter result packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_RESULT_STATUSES = {"pass", "error", "denied"}
ALLOWED_ERROR_CODES = {
    "adapter.contract.invalid",
    "adapter.timeout",
    "adapter.unavailable",
    "capability.denied",
    "source.required",
}
FORBIDDEN_LIVE_FIELDS = {
    "serverUrl",
    "command",
    "env",
    "headers",
    "credentials",
    "rawError",
    "stack",
    "traceback",
}
REQUIRED_OUTPUT_FIELDS = ["title", "url", "snippet"]


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    resolved = path if path.is_absolute() else ROOT / path
    return json.loads(resolved.read_text())


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def access_is_static(payload: dict) -> bool:
    return (
        payload.get("networkAccess") is False
        and payload.get("mcpInvocation") is False
        and payload.get("paymentAccess") is False
    )


def add_finding(findings: list[dict], field: str, reason: str) -> None:
    findings.append({"status": "fail", "field": field, "reason": reason})


def check_output(result: dict, findings: list[dict], index: int) -> None:
    output = result.get("output")
    if not isinstance(output, dict):
        add_finding(
            findings,
            f"results[{index}].output",
            "Passing MCP adapter results must include a source-checkable output object.",
        )
        return

    for field in REQUIRED_OUTPUT_FIELDS:
        if not non_empty_string(output.get(field)):
            add_finding(
                findings,
                f"results[{index}].output.{field}",
                "Passing MCP adapter outputs must include non-empty title, url, and snippet strings.",
            )


def check_error(result: dict, findings: list[dict], index: int) -> None:
    if result.get("output") is not None:
        add_finding(
            findings,
            f"results[{index}].output",
            "Failed MCP adapter results must not include output payload data.",
        )

    error = result.get("error")
    if not isinstance(error, dict):
        add_finding(
            findings,
            f"results[{index}].error",
            "Failed MCP adapter results must include a bounded error object.",
        )
        return

    if error.get("code") not in ALLOWED_ERROR_CODES:
        add_finding(
            findings,
            f"results[{index}].error.code",
            "MCP adapter result error code is not in the reviewed static allowlist.",
        )

    if not non_empty_string(error.get("message")):
        add_finding(
            findings,
            f"results[{index}].error.message",
            "MCP adapter result errors must include a bounded builder-facing message.",
        )

    if not isinstance(error.get("retryable"), bool):
        add_finding(
            findings,
            f"results[{index}].error.retryable",
            "MCP adapter result error retryability must be explicit.",
        )

    for field in sorted(FORBIDDEN_LIVE_FIELDS):
        if field in error:
            add_finding(
                findings,
                f"results[{index}].error.{field}",
                "MCP adapter aggregation must not expose raw runtime, server, auth, or environment details.",
            )


def check_result(result: dict, result_ids: set[str], findings: list[dict], index: int) -> None:
    if result.get("adapter") != "mcp":
        add_finding(findings, f"results[{index}].adapter", "Every aggregated result must declare adapter=mcp.")

    result_id = result.get("resultId")
    if not non_empty_string(result_id):
        add_finding(findings, f"results[{index}].resultId", "Every aggregated result must have a non-empty resultId.")
    elif result_id in result_ids:
        add_finding(findings, f"results[{index}].resultId", "Aggregated MCP resultIds must be unique.")
    else:
        result_ids.add(result_id)

    for field in ["serverRef", "toolId", "toolName"]:
        if not non_empty_string(result.get(field)):
            add_finding(
                findings,
                f"results[{index}].{field}",
                "Aggregated MCP result identity fields must be non-empty strings.",
            )

    status = result.get("status")
    if status not in ALLOWED_RESULT_STATUSES:
        add_finding(
            findings,
            f"results[{index}].status",
            "Aggregated MCP result status must be pass, error, or denied.",
        )

    if not access_is_static(result):
        add_finding(
            findings,
            f"results[{index}].access",
            "Aggregated MCP results must not claim network, invocation, or payment access.",
        )

    for field in sorted(FORBIDDEN_LIVE_FIELDS):
        if field in result:
            add_finding(
                findings,
                f"results[{index}].{field}",
                "MCP adapter aggregation must not expose raw runtime, server, auth, or environment details.",
            )

    if status == "pass":
        check_output(result, findings, index)
        if "error" in result:
            add_finding(
                findings,
                f"results[{index}].error",
                "Passing MCP adapter results must not include error objects.",
            )
    elif status in {"error", "denied"}:
        check_error(result, findings, index)


def check_completion(package: dict, findings: list[dict]) -> None:
    results = package.get("results")
    completion = package.get("completion")

    if not isinstance(results, list) or not isinstance(completion, dict):
        return

    passed = sum(1 for result in results if result.get("status") == "pass")
    failed = sum(1 for result in results if result.get("status") in {"error", "denied"})
    expected_required_gate_status = "fail" if failed else "pass"

    expected = {
        "resultCount": len(results),
        "passedCount": passed,
        "failedCount": failed,
        "requiredGateStatus": expected_required_gate_status,
        "status": expected_required_gate_status,
    }

    for field, expected_value in expected.items():
        if completion.get(field) != expected_value:
            add_finding(
                findings,
                f"completion.{field}",
                "MCP adapter aggregate completion must match result statuses and counts.",
            )

    if completion.get("completionImpact") != (
        "required-gate-fail" if failed else "required-gate-pass"
    ):
        add_finding(
            findings,
            "completion.completionImpact",
            "MCP adapter aggregate completionImpact must reflect required gate outcome.",
        )

    if not access_is_static(completion):
        add_finding(
            findings,
            "completion.access",
            "MCP adapter aggregate completion must not claim network, invocation, or payment access.",
        )


def check_package(package: dict) -> list[dict]:
    findings: list[dict] = []

    if package.get("adapter") != "mcp":
        add_finding(findings, "adapter", "MCP adapter aggregation package must declare adapter=mcp.")

    if not non_empty_string(package.get("packageId")):
        add_finding(findings, "packageId", "MCP adapter aggregation package must have a non-empty packageId.")

    if package.get("aggregationMode") != "static-reviewed":
        add_finding(findings, "aggregationMode", "MCP adapter aggregation must use aggregationMode=static-reviewed.")

    if not access_is_static(package):
        add_finding(findings, "access", "MCP adapter aggregation package must not claim network, invocation, or payment access.")

    for field in sorted(FORBIDDEN_LIVE_FIELDS):
        if field in package:
            add_finding(
                findings,
                field,
                "MCP adapter aggregation must not expose raw runtime, server, auth, or environment details.",
            )

    results = package.get("results")
    if not isinstance(results, list) or not results:
        add_finding(findings, "results", "MCP adapter aggregation package must include at least one result.")
        return findings

    result_ids: set[str] = set()
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            add_finding(findings, f"results[{index}]", "Every aggregated MCP result must be an object.")
            continue
        check_result(result, result_ids, findings, index)

    check_completion(package, findings)
    return findings


def report(path: Path) -> dict:
    package = read_json(path)
    findings = check_package(package)
    return {
        "path": display_path(path),
        "mode": "static-mcp-adapter-aggregation-check",
        "adapter": package.get("adapter"),
        "packageId": package.get("packageId"),
        "networkAccess": False,
        "mcpInvocation": False,
        "paymentAccess": False,
        "status": "fail" if findings else "pass",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    result = report(args.fixture)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
