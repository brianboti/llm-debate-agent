#!/usr/bin/env bash
set -euo pipefail

cd backend
python -m pip install -q -e ".[dev]"
ruff check . --fix
echo "Backend formatted/linted."

