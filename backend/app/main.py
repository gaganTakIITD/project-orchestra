from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.seed import seed_catalog, seed_demo_client
from app.db.session import AsyncSessionLocal, engine
from app.models import catalog, chat, commerce, fulfillment, identity, platform  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev/test convenience only. In production set AUTO_CREATE_ALL=false and apply
    # the versioned schema with `alembic upgrade head` (see docker-compose api cmd).
    if settings.auto_create_all:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    if settings.auto_seed:
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)

    yield

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
