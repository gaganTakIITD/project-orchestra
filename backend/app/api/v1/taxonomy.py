from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalog import Skill, TaskType, Tool
from app.schemas.catalog import SkillOut, TaskTypeOut, ToolOut

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("/skills", response_model=list[SkillOut])
async def list_skills(
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[SkillOut]:
    stmt = select(Skill).order_by(Skill.name)
    if category:
        stmt = stmt.where(Skill.category == category)
    result = await db.execute(stmt)
    return [SkillOut.from_orm_row(r) for r in result.scalars().all()]


@router.get("/tools", response_model=list[ToolOut])
async def list_tools(db: AsyncSession = Depends(get_db)) -> list[ToolOut]:
    result = await db.execute(select(Tool).order_by(Tool.name))
    return [ToolOut.from_orm_row(r) for r in result.scalars().all()]


@router.get("/task-types", response_model=list[TaskTypeOut])
async def list_task_types(
    community: str | None = Query(default=None, alias="community"),
    db: AsyncSession = Depends(get_db),
) -> list[TaskTypeOut]:
    stmt = select(TaskType).order_by(TaskType.name)
    if community:
        stmt = stmt.where(TaskType.community_type == community)
    result = await db.execute(stmt)
    return [TaskTypeOut.from_orm_row(r) for r in result.scalars().all()]
