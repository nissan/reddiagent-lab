#!/usr/bin/env python3
"""Pytest harness for the script-style test files in this directory.

Most files under ``tests/test_*.py`` in this repo are *script-style*: they
define a module-level ``main() -> int`` with bare asserts and are executed via
``python tests/<file>`` (see ``tests/smoke-validation.sh``). Pytest collects
nothing from them, so a plain ``pytest tests/`` silently skips ~90% of the
suite.

This module discovers those files (via ``ast`` parsing -- no imports, so
collection has no side effects) and parametrizes one test that runs each file
as a subprocess from the repo root, asserting exit code 0 and surfacing
stdout/stderr on failure.

Discovery rule: a file is script-style iff it defines a module-level ``main``
function AND contains no pytest-collectable tests (no module-level
``test_*``/``async test_*`` functions and no ``Test*`` classes). Files that
pytest already collects normally are therefore excluded automatically, as is
this harness itself.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent

# Generous per-file ceiling so a hung subprocess chain cannot stall the whole
# suite; the slowest current script finishes well under this.
PER_FILE_TIMEOUT_SECONDS = 120


def _is_script_style(path: Path) -> bool:
    """True if the file defines module-level main() and no pytest-collectables."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        # Let a syntactically broken test file fail loudly in the run step
        # rather than silently dropping out of discovery.
        return True

    has_main = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "main":
                has_main = True
            if node.name.startswith("test_"):
                return False  # pytest collects this file already
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            return False  # pytest collects this file already
    return has_main


def _discover_script_style_files() -> list[Path]:
    self_path = Path(__file__).resolve()
    return sorted(
        path
        for path in TESTS_DIR.glob("test_*.py")
        if path.resolve() != self_path and _is_script_style(path)
    )


SCRIPT_STYLE_FILES = _discover_script_style_files()


def test_discovery_found_script_style_files() -> None:
    """Guard: discovery must keep finding the script-style suite.

    If this number ever collapses (e.g. the glob or repo layout changes),
    fail loudly instead of green-barring an empty parametrize list.
    """
    assert len(SCRIPT_STYLE_FILES) >= 80, (
        f"Only {len(SCRIPT_STYLE_FILES)} script-style test files discovered; "
        "expected the full suite (~88). Discovery is likely broken."
    )


@pytest.mark.parametrize(
    "script_path",
    SCRIPT_STYLE_FILES,
    ids=[path.stem for path in SCRIPT_STYLE_FILES],
)
def test_script_style_file(script_path: Path) -> None:
    """Run one script-style test file and require exit code 0."""
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=PER_FILE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            f"{script_path.name} timed out after {PER_FILE_TIMEOUT_SECONDS}s\n"
            f"--- stdout ---\n{exc.stdout or ''}\n"
            f"--- stderr ---\n{exc.stderr or ''}"
        )
    if proc.returncode != 0:
        pytest.fail(
            f"{script_path.name} exited with code {proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}"
        )
