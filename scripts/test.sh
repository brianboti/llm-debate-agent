#!/usr/bin/env bash
set -euo pipefail

cd backend
python -m pip install -q -e ".[dev]"
pytest -q
echo "Backend tests OK."

