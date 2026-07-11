from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import DEMO_CLIENT_ID, User


async def get_demo_client(session: AsyncSession) -> User:
    """Return the seeded demo client until JWT auth is wired."""
    user = await session.get(User, DEMO_CLIENT_ID)
    if user is None:
        raise RuntimeError("Demo client not seeded — run with AUTO_SEED=true")
    return user
