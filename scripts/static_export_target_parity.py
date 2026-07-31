#!/usr/bin/env python3
"""Build a static export-target parity matrix from Prosumer Builder plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from prosumer_builder_plan import (
    BOUNDARY_FLAGS,
    DEFAULT_EXAMPLES,
    EXPORT_MATRIX_TARGETS,
    ROOT,
    display_path,
    plan_for,
)


DEFAULT_INVALID_EXAMPLES = [
    ROOT / "examples" / "invalid" / "missing-instructions.yaml",
]


def summarize_targets(agent_rows: list[dict]) -> list[dict]:
    summaries = []
    for target in EXPORT_MATRIX_TARGETS:
        target_id = target["target"]
        rows = []
        for agent in agent_rows:
            matches = [row for row in agent["rows"] if row["target"] == target_id]
            if matches:
                rows.append((agent, matches[0]))
        readiness_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        blocked_by: set[str] = set()
        metadata_only: set[str] = set()
        for _agent, row in rows:
            readiness_counts[row["readiness"]] = readiness_counts.get(row["readiness"], 0) + 1
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
            blocked_by.update(row["blockedBy"])
            metadata_only.update(row["metadataOnlySections"])
            metadata_only.update(row["metadataOnlyExtensions"])
        summaries.append(
            {
                "target": target_id,
                "label": target["label"],
                "authoritativeCheck": target["authoritativeCheck"],
                "agentCount": len(rows),
                "readinessCounts": readiness_counts,
                "statusCounts": status_counts,
                "blockedBy": sorted(blocked_by),
                "metadataOnly": sorted(metadata_only),
                **BOUNDARY_FLAGS,
            }
        )
    return summaries


def parity_matrix(paths: list[Path]) -> dict:
    plans = [plan_for(path) for path in paths]
    agent_rows = []
    for plan in plans:
        export_steps = [step for step in plan["flow"] if step["id"] == "export"]
        rows = export_steps[0]["staticUiExportMatrix"]
        agent_rows.append(
            {
                "agent": plan["agent"],
                "source": plan["source"],
                "supported": plan["supported"],
                "unsupportedFeatures": plan["unsupportedFeatures"],
                "metadataOnlyExtensions": plan["metadataOnlyExtensions"],
                "rows": rows,
            }
        )
    return {
        "format": "static-export-target-parity-matrix",
        "issue": 196,
        "buzzIssue": 425,
        "sources": [display_path(path) for path in paths],
        "targetOrder": [target["target"] for target in EXPORT_MATRIX_TARGETS],
        **BOUNDARY_FLAGS,
        "agents": agent_rows,
        "targetSummary": summarize_targets(agent_rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--valid-only",
        action="store_true",
        help="Use only the default valid ADL examples when no paths are supplied.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.paths:
        paths = args.paths
    elif args.valid_only:
        paths = list(DEFAULT_EXAMPLES)
    else:
        paths = [*DEFAULT_EXAMPLES, *DEFAULT_INVALID_EXAMPLES]
    print(json.dumps(parity_matrix(paths), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
