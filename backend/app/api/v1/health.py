from fastapi import APIRouter

from app.config import settings
from app.schemas.catalog import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok", service="orchestra-api", env=settings.app_env)
