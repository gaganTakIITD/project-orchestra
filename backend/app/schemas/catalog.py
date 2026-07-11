from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutcomeSkuOut(BaseModel):
    """Mirrors lib/types.ts OutcomeSku — snake_case JSON for frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    category: str
    description: str
    base_price: float
    typical_days: int
    revision_limit: int

    @classmethod
    def from_orm_row(cls, row) -> "OutcomeSkuOut":
        return cls(
            id=str(row.id),
            slug=row.slug,
            name=row.name,
            category=row.category,
            description=row.description,
            base_price=float(row.base_price),
            typical_days=row.typical_days,
            revision_limit=row.revision_limit,
        )


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    category: str

    @classmethod
    def from_orm_row(cls, row) -> "SkillOut":
        return cls(id=str(row.id), name=row.name, slug=row.slug, category=row.category)


class ToolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    category: str | None = None

    @classmethod
    def from_orm_row(cls, row) -> "ToolOut":
        return cls(
            id=str(row.id),
            name=row.name,
            slug=row.slug,
            category=row.category,
        )


class TaskTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    community_type: str
    description: str | None = None
    typical_hours: float | None = None

    @classmethod
    def from_orm_row(cls, row) -> "TaskTypeOut":
        return cls(
            id=str(row.id),
            name=row.name,
            slug=row.slug,
            community_type=row.community_type,
            description=row.description,
            typical_hours=float(row.typical_hours) if row.typical_hours is not None else None,
        )


class HealthOut(BaseModel):
    status: str = "ok"
    service: str = "orchestra-api"
    env: str
