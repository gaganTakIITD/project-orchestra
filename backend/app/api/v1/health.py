from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.catalog import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    if settings.gemini_required and not settings.gemini_enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "Vertex Gemini required when APP_ENV=production or REQUIRE_GEMINI=true. "
                "Set GEMINI_AUTH=vertex and VERTEX_PROJECT=raystartup. "
                "Do not use GEMINI_API_KEY (AI Studio). See docs/GCP_BILLING_SPLIT.md."
            ),
        )
    return HealthOut(status="ok", service="orchestra-api", env=settings.app_env)
