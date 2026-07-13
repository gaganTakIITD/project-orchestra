from collections.abc import AsyncGenerator

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_connector = None


def _db_user() -> str:
    # postgresql+asyncpg://USER:PASS@host/DB
    try:
        return settings.database_url.split("://", 1)[1].split(":", 1)[0]
    except IndexError:
        return "postgres"


def _db_password() -> str:
    try:
        after_user = settings.database_url.split("://", 1)[1].split(":", 1)[1]
        return after_user.rsplit("@", 1)[0]
    except IndexError:
        return ""


def _db_name() -> str:
    try:
        return settings.database_url.rsplit("/", 1)[-1].split("?")[0] or "orchestra"
    except IndexError:
        return "orchestra"


def _build_engine():
    """Create async engine — Cloud SQL Connector when CLOUD_SQL_INSTANCE is set."""
    common = dict(
        echo=settings.app_env == "development",
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
    )

    if settings.cloud_sql_instance:
        from google.cloud.sql.connector import Connector, IPTypes

        ip_type = (
            IPTypes.PRIVATE
            if settings.cloud_sql_ip_type.lower() == "private"
            else IPTypes.PUBLIC
        )

        async def getconn():
            # Lazy init with the running loop (avoids ConnectorLoopError).
            global _connector
            if _connector is None:
                _connector = Connector(loop=asyncio.get_running_loop())
            return await _connector.connect_async(
                settings.cloud_sql_instance,
                "asyncpg",
                user=_db_user(),
                password=_db_password(),
                db=_db_name(),
                enable_iam_auth=False,
                ip_type=ip_type,
            )

        return create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
            **common,
        )

    return create_async_engine(
        settings.database_url,
        connect_args=settings.db_connect_args,
        **common,
    )


engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
