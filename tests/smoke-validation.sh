#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
/Users/loki/.pyenv/versions/3.14.3/bin/python3 scripts/validate_examples.py

