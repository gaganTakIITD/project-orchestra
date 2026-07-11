from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import DEMO_CLIENT_ID, DEMO_WORKER_ID, User, WorkerProfileRecord


async def get_demo_client(session: AsyncSession) -> User:
    """Return the seeded demo client until JWT auth is wired."""
    user = await session.get(User, DEMO_CLIENT_ID)
    if user is None:
        raise RuntimeError("Demo client not seeded — run with AUTO_SEED=true")
    return user


async def get_demo_worker(session: AsyncSession) -> User:
    """Return the seeded demo worker until JWT auth is wired."""
    user = await session.get(User, DEMO_WORKER_ID)
    if user is None:
        raise RuntimeError("Demo worker not seeded — run with AUTO_SEED=true")
    return user


async def get_demo_worker_profile(session: AsyncSession) -> WorkerProfileRecord:
    profile = await session.get(WorkerProfileRecord, DEMO_WORKER_ID)
    if profile is None:
        raise RuntimeError("Demo worker profile not seeded — run with AUTO_SEED=true")
    return profile
