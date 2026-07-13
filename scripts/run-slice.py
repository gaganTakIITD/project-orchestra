#!/usr/bin/env python3
"""Drive the product vertical slice: chat finalize -> accept -> submit -> delivery.

Mirrors backend/tests/test_product_smoke.py::test_chat_path_finalize_to_delivery_accept.

Modes
-----
  Default (--asgi): in-process ASGI client against Postgres (no uvicorn).
  --http URL:       hit a running API (docker compose / Cloud Run).

Prerequisites (ASGI / local)
----------------------------
  docker compose up -d postgres
  # If the compose `api` service is also up, stop it first — ASGI resets schema
  # and will deadlock against a live API on the same database:
  #   docker compose stop api
  cd backend && pip install -e ".[dev]"

How to run
----------
  # Windows
  .\\scripts\\run-slice.ps1
  # Unix
  ./scripts/run-slice.sh
  # or
  python scripts/run-slice.py
  python scripts/run-slice.py --http http://localhost:8000

Env: DATABASE_URL (ASGI), AUTH_MODE=demo (default).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Quiet SQLAlchemy chatter during the demo script.
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Demo worker id — same as app.models.identity.DEMO_WORKER_ID
DEMO_WORKER_ID = "00000000-0000-4000-8000-000000000020"

_PASSING_ASSETS = [
    "https://files.example/logo.svg",
    "https://files.example/logo.png",
    "https://files.example/out.pdf",
    "https://preview.example/live",
]

_SCOPE_BODY = (
    "HealthTrack — chronic condition tracking startup. Brand + landing page, "
    "trustworthy healthcare tone. Tagline: Your health, tracked. "
    "References: apple.com"
)


def _log(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


async def _ok(resp, label: str):
    if resp.is_success:
        return resp
    body = (resp.text or "")[:500]
    raise RuntimeError(f"{label}: HTTP {resp.status_code} — {body}")


async def _complete_ready_task(client, task_id: str) -> None:
    r = await _ok(await client.post(f"/api/v1/tasks/{task_id}/accept-interest"), "accept-interest")
    assert r.json()["status"] == "accepted", r.text

    r = await _ok(await client.post(f"/api/v1/tasks/{task_id}/ready-to-start"), "ready-to-start")
    assert r.json()["status"] == "in_progress", r.text

    r = await _ok(
        await client.post(
            f"/api/v1/tasks/{task_id}/submit",
            json={
                "notes": "Work product attached. lighthouse: 85",
                "asset_urls": list(_PASSING_ASSETS),
            },
        ),
        "submit",
    )
    assert r.json()["status"] == "completed", r.text
    _log(f"  task {task_id[:8]}... -> completed")


async def _run_slice(client) -> str:
    """Chat path through closed delivery. Returns final order status."""
    _log("1) chat session")
    start = await _ok(await client.post("/api/v1/chat/sessions"), "create chat session")
    sid = start.json()["id"]

    _log("2) scope message")
    detailed = await _ok(
        await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            json={"body": _SCOPE_BODY},
        ),
        "chat message",
    )
    assert detailed.json()["ready_for_quote"] is True, detailed.text

    _log("3) finalize -> quote")
    fin = await _ok(
        await client.post(f"/api/v1/chat/sessions/{sid}/finalize"),
        "finalize",
    )
    quote_id = fin.json()["quote_id"]
    _log(f"   quote_id={quote_id}")

    _log("4) accept quote -> order")
    accept_quote = await _ok(
        await client.post(f"/api/v1/quotes/{quote_id}/accept"),
        "accept quote",
    )
    order_id = accept_quote.json()["order_id"]
    _log(f"   order_id={order_id}")

    _log("5) walk DAG (prefs -> accept -> start -> submit)")
    for i in range(8):
        plan = (await client.get(f"/api/v1/orders/{order_id}/milestones")).json()
        ready = [t for t in plan["tasks"] if t["status"] == "ready"]
        if not ready:
            break
        task_id = ready[0]["id"]
        if i == 0:
            pref = await _ok(
                await client.post(
                    f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
                    json={
                        "ranked_worker_ids": [
                            DEMO_WORKER_ID,
                            "usr_worker_meera",
                            "usr_worker_kabir",
                        ]
                    },
                ),
                "preferences",
            )
            assert pref.status_code == 200
        await _complete_ready_task(client, task_id)
    else:
        raise RuntimeError("DAG did not finish within task budget")

    order = (await client.get(f"/api/v1/orders/{order_id}")).json()
    status = order["status"]
    _log(f"6) order status={status}")
    if status != "delivered":
        raise RuntimeError(f"expected delivered, got {status}")

    delivery = await _ok(
        await client.get(f"/api/v1/orders/{order_id}/delivery"),
        "delivery",
    )
    assets = delivery.json().get("assets") or []
    _log(f"7) delivery assets={len(assets)}")
    if not assets:
        raise RuntimeError("delivery bundle has no assets")

    closed = await _ok(
        await client.post(f"/api/v1/orders/{order_id}/accept-delivery"),
        "accept-delivery",
    )
    final = closed.json()["status"]
    _log(f"8) accept-delivery -> {final}")
    if final != "closed":
        raise RuntimeError(f"expected closed, got {final}")
    return final


async def _prepare_asgi_db() -> None:
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_catalog(session)
        await seed_demo_client(session)
        await seed_demo_worker(session)


async def run_asgi() -> str:
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    _log("Mode: ASGI (in-process). Resetting + seeding Postgres...")
    try:
        await _prepare_asgi_db()
    except Exception as e:
        raise SystemExit(
            f"Database unavailable ({e}).\n"
            "Start Postgres: docker compose up -d postgres\n"
            "If compose api is running on the same DB: docker compose stop api\n"
            "Then: cd backend && pip install -e \".[dev]\" && python ../scripts/run-slice.py"
        ) from e

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await _run_slice(client)


async def run_http(base_url: str) -> str:
    from httpx import AsyncClient

    root = base_url.rstrip("/")
    _log(f"Mode: HTTP -> {root}")
    async with AsyncClient(base_url=root, timeout=120.0) as client:
        health = await client.get("/api/v1/health")
        health.raise_for_status()
        return await _run_slice(client)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run product vertical slice end-to-end")
    parser.add_argument(
        "--http",
        metavar="URL",
        help="Hit a live API (e.g. http://localhost:8000). Default is in-process ASGI.",
    )
    args = parser.parse_args()

    try:
        if args.http:
            final = asyncio.run(run_http(args.http))
        else:
            final = asyncio.run(run_asgi())
    except SystemExit:
        raise
    except Exception as e:
        _log(f"FAIL: {e}")
        return 1

    _log(f"\nDELIVERED (order {final})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
