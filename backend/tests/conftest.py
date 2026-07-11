"""Shared pytest fixtures — NullPool avoids async connection reuse flakes."""

import pytest


@pytest.fixture(autouse=True)
async def _dispose_pool_between_tests():
    """Close borrowed connections after each test so the next drop_all is clean."""
    yield
    try:
        from app.db.session import engine

        await engine.dispose()
    except Exception:
        pass
