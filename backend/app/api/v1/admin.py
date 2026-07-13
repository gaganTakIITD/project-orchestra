"""Admin console — orders, events, AI audit, worker verify, taxonomy CRUD, disputes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalog import OutcomeSku, Skill, TaskType, Tool
from app.models.fulfillment import DisputeCaseRecord, FulfillmentTask, OutcomeOrder
from app.models.identity import User, WorkerProfileRecord
from app.models.platform import AiDecisionLog, EventLog
from app.schemas.admin import (
    AdminAiDecisionListOut,
    AdminAiDecisionOut,
    AdminEventListOut,
    AdminEventOut,
    AdminOrderListOut,
    AdminOrderOut,
)
from app.schemas.catalog import OutcomeSkuOut, SkillOut, TaskTypeOut, ToolOut
from app.schemas.worker import WorkerProfileOut
from app.services.auth import get_current_admin
from app.services.dispute import DisputeService
from app.services.worker_stats import WorkerStatsService

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminWorkerListOut(BaseModel):
    workers: list[WorkerProfileOut] = Field(default_factory=list)


class AdminAiQualityOut(BaseModel):
    count: int = 0
    avg_confidence: float | None = None
    escalate_count: int = 0
    by_agent: dict[str, int] = Field(default_factory=dict)


class TaxonomySkillIn(BaseModel):
    name: str
    slug: str
    category: str


class TaxonomyToolIn(BaseModel):
    name: str
    slug: str
    category: str | None = None


class TaxonomyTaskTypeIn(BaseModel):
    name: str
    slug: str
    community_type: str
    description: str | None = None
    typical_hours: float | None = None


class TaxonomySkuIn(BaseModel):
    name: str
    slug: str
    category: str
    description: str = ""
    base_price: float
    typical_days: int
    revision_limit: int = 2
    is_active: bool = True


class DisputeResolveIn(BaseModel):
    resolution: str


class DisputeOut(BaseModel):
    id: str
    order_id: str
    task_id: str | None = None
    raised_by: str
    reason: str
    status: str
    resolution: str | None = None
    resolved_by: str | None = None
    created_at: str

    @classmethod
    def from_orm_row(cls, row: DisputeCaseRecord) -> "DisputeOut":
        return cls(
            id=str(row.id),
            order_id=str(row.order_id),
            task_id=str(row.task_id) if row.task_id else None,
            raised_by=str(row.raised_by),
            reason=row.reason,
            status=row.status,
            resolution=row.resolution,
            resolved_by=str(row.resolved_by) if row.resolved_by else None,
            created_at=row.created_at.isoformat() if row.created_at else "",
        )


@router.get("/orders", response_model=AdminOrderListOut)
async def list_orders(
    status: str | None = Query(default=None, description="Filter by order status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminOrderListOut:
    stmt = select(OutcomeOrder).order_by(OutcomeOrder.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(OutcomeOrder.status == status)
    rows = (await db.scalars(stmt)).all()
    return AdminOrderListOut(orders=[AdminOrderOut.from_orm_row(r) for r in rows])


@router.get("/orders/{order_id}/events", response_model=AdminEventListOut)
async def list_order_events(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminEventListOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    task_ids = list(
        await db.scalars(
            select(FulfillmentTask.id).where(FulfillmentTask.order_id == order_id)
        )
    )

    conditions = [
        (EventLog.aggregate_type == "order") & (EventLog.aggregate_id == order_id),
    ]
    if task_ids:
        conditions.append(
            (EventLog.aggregate_type == "task") & (EventLog.aggregate_id.in_(task_ids))
        )

    stmt = (
        select(EventLog)
        .where(or_(*conditions))
        .order_by(EventLog.created_at.asc())
    )
    events = (await db.scalars(stmt)).all()
    return AdminEventListOut(
        order_id=str(order_id),
        events=[AdminEventOut.from_orm_row(e) for e in events],
    )


@router.get("/ai-decisions", response_model=AdminAiDecisionListOut)
async def list_ai_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminAiDecisionListOut:
    stmt = (
        select(AiDecisionLog)
        .order_by(AiDecisionLog.created_at.desc())
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()
    return AdminAiDecisionListOut(
        decisions=[AdminAiDecisionOut.from_orm_row(r) for r in rows]
    )


@router.get("/ai-quality", response_model=AdminAiQualityOut)
async def ai_quality_summary(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminAiQualityOut:
    rows = (await db.scalars(select(AiDecisionLog))).all()
    if not rows:
        return AdminAiQualityOut()

    confidences = [float(r.confidence) for r in rows if r.confidence is not None]
    escalate = 0
    by_agent: dict[str, int] = {}
    for r in rows:
        by_agent[r.agent_type] = by_agent.get(r.agent_type, 0) + 1
        draft = r.output_draft if isinstance(r.output_draft, dict) else {}
        action = str(draft.get("action") or draft.get("policy_result") or "").lower()
        if "escalat" in action or action == "escalate":
            escalate += 1
        if r.error:
            escalate += 0  # keep count focused on explicit escalate actions

    return AdminAiQualityOut(
        count=len(rows),
        avg_confidence=(sum(confidences) / len(confidences)) if confidences else None,
        escalate_count=escalate,
        by_agent=by_agent,
    )


@router.get("/workers", response_model=AdminWorkerListOut)
async def list_workers(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminWorkerListOut:
    result = await db.execute(
        select(User, WorkerProfileRecord)
        .join(WorkerProfileRecord, WorkerProfileRecord.user_id == User.id)
        .where(User.role == "worker")
        .order_by(User.full_name)
    )
    workers: list[WorkerProfileOut] = []
    stats_svc = WorkerStatsService(db)
    for user, profile in result.all():
        tt = await stats_svc.list_for_worker(user.id)
        workers.append(WorkerProfileOut.from_orm_rows(user, profile, task_type_stats=tt))
    return AdminWorkerListOut(workers=workers)


@router.post("/workers/{worker_id}/verify", response_model=WorkerProfileOut)
async def verify_worker(
    worker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> WorkerProfileOut:
    return await _set_verified(db, worker_id, True, admin.id)


@router.post("/workers/{worker_id}/unverify", response_model=WorkerProfileOut)
async def unverify_worker(
    worker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> WorkerProfileOut:
    return await _set_verified(db, worker_id, False, admin.id)


async def _set_verified(
    db: AsyncSession, worker_id: uuid.UUID, verified: bool, admin_id: uuid.UUID
) -> WorkerProfileOut:
    from app.orchestrator.events import EventWriter
    from app.orchestrator.states import ActorType

    user = await db.get(User, worker_id)
    profile = await db.get(WorkerProfileRecord, worker_id)
    if user is None or profile is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    profile.campus_verified = verified
    await EventWriter(db).emit(
        aggregate_type="user",
        aggregate_id=worker_id,
        event_type="WorkerVerified" if verified else "WorkerUnverified",
        actor_id=admin_id,
        actor_type=ActorType.ADMIN,
        payload={"campus_verified": verified},
    )
    await db.commit()
    tt = await WorkerStatsService(db).list_for_worker(worker_id)
    return WorkerProfileOut.from_orm_rows(user, profile, task_type_stats=tt)


# --- Taxonomy CRUD (public GET remains under /taxonomy) ---


@router.post("/taxonomy/skills", response_model=SkillOut)
async def create_skill(
    body: TaxonomySkillIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> SkillOut:
    row = Skill(name=body.name, slug=body.slug, category=body.category)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SkillOut.from_orm_row(row)


@router.patch("/taxonomy/skills/{skill_id}", response_model=SkillOut)
async def patch_skill(
    skill_id: uuid.UUID,
    body: TaxonomySkillIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> SkillOut:
    row = await db.get(Skill, skill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    row.name, row.slug, row.category = body.name, body.slug, body.category
    await db.commit()
    await db.refresh(row)
    return SkillOut.from_orm_row(row)


@router.delete("/taxonomy/skills/{skill_id}")
async def delete_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, str]:
    row = await db.get(Skill, skill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}


@router.post("/taxonomy/tools", response_model=ToolOut)
async def create_tool(
    body: TaxonomyToolIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> ToolOut:
    row = Tool(name=body.name, slug=body.slug, category=body.category)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ToolOut.from_orm_row(row)


@router.patch("/taxonomy/tools/{tool_id}", response_model=ToolOut)
async def patch_tool(
    tool_id: uuid.UUID,
    body: TaxonomyToolIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> ToolOut:
    row = await db.get(Tool, tool_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    row.name, row.slug, row.category = body.name, body.slug, body.category
    await db.commit()
    await db.refresh(row)
    return ToolOut.from_orm_row(row)


@router.delete("/taxonomy/tools/{tool_id}")
async def delete_tool(
    tool_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, str]:
    row = await db.get(Tool, tool_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}


@router.post("/taxonomy/task_types", response_model=TaskTypeOut)
@router.post("/taxonomy/task-types", response_model=TaskTypeOut)
async def create_task_type(
    body: TaxonomyTaskTypeIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> TaskTypeOut:
    row = TaskType(
        name=body.name,
        slug=body.slug,
        community_type=body.community_type,
        description=body.description,
        typical_hours=body.typical_hours,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TaskTypeOut.from_orm_row(row)


@router.patch("/taxonomy/task_types/{task_type_id}", response_model=TaskTypeOut)
@router.patch("/taxonomy/task-types/{task_type_id}", response_model=TaskTypeOut)
async def patch_task_type(
    task_type_id: uuid.UUID,
    body: TaxonomyTaskTypeIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> TaskTypeOut:
    row = await db.get(TaskType, task_type_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    row.name = body.name
    row.slug = body.slug
    row.community_type = body.community_type
    row.description = body.description
    row.typical_hours = body.typical_hours
    await db.commit()
    await db.refresh(row)
    return TaskTypeOut.from_orm_row(row)


@router.delete("/taxonomy/task_types/{task_type_id}")
@router.delete("/taxonomy/task-types/{task_type_id}")
async def delete_task_type(
    task_type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, str]:
    row = await db.get(TaskType, task_type_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}


@router.post("/taxonomy/skus", response_model=OutcomeSkuOut)
async def create_sku(
    body: TaxonomySkuIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> OutcomeSkuOut:
    row = OutcomeSku(
        name=body.name,
        slug=body.slug,
        category=body.category,
        description=body.description,
        base_price=body.base_price,
        typical_days=body.typical_days,
        revision_limit=body.revision_limit,
        is_active=body.is_active,
        template_spec={},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return OutcomeSkuOut.from_orm_row(row)


@router.patch("/taxonomy/skus/{sku_id}", response_model=OutcomeSkuOut)
async def patch_sku(
    sku_id: uuid.UUID,
    body: TaxonomySkuIn,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> OutcomeSkuOut:
    row = await db.get(OutcomeSku, sku_id)
    if row is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    row.name = body.name
    row.slug = body.slug
    row.category = body.category
    row.description = body.description
    row.base_price = body.base_price
    row.typical_days = body.typical_days
    row.revision_limit = body.revision_limit
    row.is_active = body.is_active
    await db.commit()
    await db.refresh(row)
    return OutcomeSkuOut.from_orm_row(row)


@router.delete("/taxonomy/skus/{sku_id}")
async def delete_sku(
    sku_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, str]:
    row = await db.get(OutcomeSku, sku_id)
    if row is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeOut)
async def resolve_dispute(
    dispute_id: uuid.UUID,
    body: DisputeResolveIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> DisputeOut:
    row = await db.get(DisputeCaseRecord, dispute_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    try:
        row = await DisputeService(db).resolve(
            dispute=row, resolved_by=admin.id, resolution=body.resolution
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return DisputeOut.from_orm_row(row)
