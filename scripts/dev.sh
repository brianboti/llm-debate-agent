#!/usr/bin/env bash
set -euo pipefail

# Runs backend + web together (simple local dev).
# Requires:
# - backend venv activated (or python available)
# - web deps installed (npm install)
#
# If you prefer two terminals, run:
#   make dev-backend
#   make dev-web

cleanup() {
  if [[ -n "${BACK_PID:-}" ]]; then kill "${BACK_PID}" 2>/dev/null || true; fi
  if [[ -n "${WEB_PID:-}" ]]; then kill "${WEB_PID}" 2>/dev/null || true; fi
}
trap cleanup EXIT

echo "Starting backend on http://localhost:8000 ..."
( cd backend && uvicorn src.app:app --reload --port 8000 ) &
BACK_PID=$!

echo "Starting web on http://localhost:5173 ..."
( cd web && npm run dev ) &
WEB_PID=$!

echo ""
echo "Dev servers running:"
echo "  Backend: http://localhost:8000"
echo "  Web:     http://localhost:5173"
echo ""
wait

