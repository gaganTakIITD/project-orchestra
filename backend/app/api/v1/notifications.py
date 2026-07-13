"""GET /notifications stub — empty list until derived event feed lands."""

from fastapi import APIRouter

from app.schemas.notifications import AppNotificationOut

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[AppNotificationOut])
async def list_notifications() -> list[AppNotificationOut]:
    """Return the caller's notifications. Stub: always []."""
    return []
