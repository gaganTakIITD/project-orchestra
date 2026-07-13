"""GET /notifications + mark-read — auth-scoped event-projected feed."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.identity import User
from app.schemas.notifications import AppNotificationOut
from app.services.auth import get_current_user_for_me
from app.services.notifications import NotificationService, notification_to_out

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[AppNotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_for_me),
) -> list[AppNotificationOut]:
    """Return the caller's notifications (newest first)."""
    return await NotificationService(db).list_for_user(user.id)


@router.post("/notifications/{notification_id}/read", response_model=AppNotificationOut)
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_for_me),
) -> AppNotificationOut:
    """Mark a notification as read (caller-owned only)."""
    try:
        row = await NotificationService(db).mark_read(
            notification_id=notification_id, user_id=user.id
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Notification not found") from None
    await db.commit()
    return notification_to_out(row)
