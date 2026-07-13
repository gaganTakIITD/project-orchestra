from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


from pydantic import BaseModel, Field


class SetRoleIn(BaseModel):
    """PATCH /auth/role — choose client or worker portal (admin is Clerk-only)."""

    role: str = Field(pattern="^(client|worker)$")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    profile_photo_url: str | None = None
    phone: str | None = None
    is_active: bool
    email_verified: bool
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "UserOut":
        return cls(
            id=str(row.id),
            email=row.email,
            full_name=row.full_name,
            role=row.role,
            profile_photo_url=row.profile_photo_url,
            phone=row.phone,
            is_active=row.is_active,
            email_verified=row.email_verified,
            created_at=row.created_at,
        )
