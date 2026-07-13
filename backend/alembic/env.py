"""Alembic environment — async locally; sync Cloud SQL Connector on Cloud Run."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app import models  # noqa: F401
from app.config import settings
from app.db.base import Base
from app.db.session import _db_name, _db_password, _db_user

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_cloud_sql() -> None:
    """Sync pg8000 + Cloud SQL Connector — avoids async ConnectorLoopError under Alembic."""
    from google.cloud.sql.connector import Connector, IPTypes

    ip_type = (
        IPTypes.PRIVATE
        if settings.cloud_sql_ip_type.lower() == "private"
        else IPTypes.PUBLIC
    )
    connector = Connector()

    def getconn():
        return connector.connect(
            settings.cloud_sql_instance,
            "pg8000",
            user=_db_user(),
            password=_db_password(),
            db=_db_name(),
            enable_iam_auth=False,
            ip_type=ip_type,
        )

    engine = create_engine("postgresql+pg8000://", creator=getconn, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            do_run_migrations(connection)
    finally:
        engine.dispose()
        connector.close()


async def run_migrations_online_async() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=settings.db_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    if settings.cloud_sql_instance:
        run_migrations_cloud_sql()
    else:
        asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
