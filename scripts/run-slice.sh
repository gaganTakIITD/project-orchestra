#!/usr/bin/env bash
# Drive intent/chat → finalize → accept → submit → delivery (Track C / B6).
#
# Prerequisites:
#   docker compose up -d postgres
#   docker compose stop api   # if api shares the same DB (ASGI resets schema)
#   cd backend && pip install -e ".[dev]"
#
# Usage:
#   ./scripts/run-slice.sh
#   ./scripts/run-slice.sh --http http://localhost:8000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python scripts/run-slice.py "$@"
