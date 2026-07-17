import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.seed import (
    purge_seed_workers,
    seed_catalog,
    seed_demo_client,
    seed_demo_worker_pool,
)
from app.db.session import AsyncSessionLocal, engine
from app.models import catalog, chat, commerce, fulfillment, identity, platform  # noqa: F401


async def _timer_tick_loop(stop: asyncio.Event) -> None:
    """Dev/prod optional loop — Cloud Scheduler can call /internal/timers/tick instead."""
    from app.services.timer_tick import tick_due_timers

    interval = float(settings.timer_tick_seconds)
    if interval <= 0:
        return
    while not stop.is_set():
        try:
            async with AsyncSessionLocal() as session:
                await tick_due_timers(session)
                await session.commit()
        except Exception:
            # Never crash the API process on timer errors
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional Sentry (no-op when SENTRY_DSN unset).
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        except Exception:
            pass

    # Prod / REQUIRE_GEMINI: refuse to start without a key (no silent AI fixtures).
    settings.ensure_gemini_configured()

    # Dev/test convenience only. In production set AUTO_CREATE_ALL=false and apply
    # the versioned schema with `alembic upgrade head` (see docker-compose api cmd).
    if settings.auto_create_all:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    if settings.auto_seed:
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)
            if settings.auth_mode == "clerk":
                # Prod: strip seeded talent from the live matcher pool.
                await purge_seed_workers(session)
            else:
                # Local demo + pytest: keep active seed pool for matcher fixtures.
                await seed_demo_worker_pool(session)

    stop = asyncio.Event()
    tick_task: asyncio.Task | None = None
    if settings.timer_tick_seconds > 0:
        tick_task = asyncio.create_task(_timer_tick_loop(stop))

    yield

    stop.set()
    if tick_task is not None:
        tick_task.cancel()
        try:
            await tick_task
        except asyncio.CancelledError:
            pass

    await engine.dispose()


app = FastAPI(
    title="Project Orchestra API",
    description="Outcome-as-a-Service — Spine + services + AI gateway",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
