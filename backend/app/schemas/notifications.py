"""Notification schemas — mirrors lib/types.ts AppNotification."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AppNotificationOut(BaseModel):
    """Mirrors lib/types.ts AppNotification — snake_case JSON for frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: str
    title: str
    body: str
    ref_type: str | None = None
    ref_id: str | None = None
    read: bool
    created_at: datetime
