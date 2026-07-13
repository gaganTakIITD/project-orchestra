#!/usr/bin/env python3
"""Lightweight OpenAPI path contract for CI (Track C / B6).

Hard-fail if core Spine paths are missing. Soft-warn (exit 0) for WebSocket
paths until Track A merges them into the router.

Run from repo root or backend/ after `pip install -e ".[dev]"`:

    python scripts/check_openapi_contract.py
    # or from backend/:
    python ../scripts/check_openapi_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python scripts/check_openapi_contract.py` from repo root without PYTHONPATH.
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

REQUIRED_PATHS = (
    "/api/v1/health",
    "/api/v1/chat/sessions",
    "/api/v1/chat/sessions/{session_id}/finalize",
    "/api/v1/quotes/{quote_id}/accept",
    "/api/v1/orders/{order_id}",
    "/api/v1/orders/{order_id}/milestones",
    "/api/v1/orders/{order_id}/delivery",
    "/api/v1/orders/{order_id}/accept-delivery",
    "/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
    "/api/v1/tasks/{task_id}/discussion",
    "/api/v1/tasks/{task_id}/accept-interest",
    "/api/v1/tasks/{task_id}/submit",
)

# Soft until Track A lands WS routes — warn only, do not fail CI.
SOFT_WS_PATHS = (
    "/api/v1/ws/orders/{order_id}",
    "/api/v1/ws/tasks/{task_id}",
)


def main() -> int:
    from app.main import app

    paths = set(app.openapi().get("paths", {}))
    missing = [p for p in REQUIRED_PATHS if p not in paths]
    if missing:
        print("FAIL: required OpenAPI paths missing:")
        for p in missing:
            print(f"  - {p}")
        return 1

    print(f"OK: {len(REQUIRED_PATHS)} required OpenAPI paths present")

    soft_missing = [p for p in SOFT_WS_PATHS if p not in paths]
    if soft_missing:
        print("SOFT/xfail: WebSocket paths not in OpenAPI yet (Track A):")
        for p in soft_missing:
            print(f"  - {p}")
    else:
        print(f"OK: {len(SOFT_WS_PATHS)} WebSocket OpenAPI paths present")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
