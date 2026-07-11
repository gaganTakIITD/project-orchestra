from datetime import datetime

from pydantic import BaseModel, Field


class FulfillmentMilestoneOut(BaseModel):
    name: str
    task_ids: list[str]
    client_label: str


class FulfillmentTaskOut(BaseModel):
    id: str
    plan_id: str
    order_id: str
    task_type_id: str
    task_type_slug: str
    title: str
    description: str | None = None
    acceptance_criteria: list[dict]
    status: str
    sequence_order: int
    payout_amount: float
    deadline: datetime | None = None
    assigned_worker_id: str | None = None
    revision_count: int
    revision_limit: int
    priority_window_ends: datetime | None = None
    depends_on: list[str]
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def from_orm_row(cls, row) -> "FulfillmentTaskOut":
        return cls(
            id=str(row.id),
            plan_id=str(row.plan_id) if row.plan_id else "",
            order_id=str(row.order_id),
            task_type_id=str(row.task_type_id) if row.task_type_id else "",
            task_type_slug=row.task_type_slug or "",
            title=row.title,
            description=row.description,
            acceptance_criteria=row.acceptance_criteria or [],
            status=row.status,
            sequence_order=row.sequence_order,
            payout_amount=float(row.payout_amount),
            deadline=row.deadline,
            assigned_worker_id=str(row.assigned_worker_id) if row.assigned_worker_id else None,
            revision_count=row.revision_count,
            revision_limit=row.revision_limit,
            priority_window_ends=row.priority_window_ends,
            depends_on=row.depends_on or [],
            started_at=row.started_at,
            completed_at=row.completed_at,
        )


class FulfillmentPlanOut(BaseModel):
    id: str
    order_id: str
    tasks: list[FulfillmentTaskOut]
    milestones: list[FulfillmentMilestoneOut]
    critical_path_hours: int

    @classmethod
    def from_orm_rows(cls, plan, tasks) -> "FulfillmentPlanOut":
        return cls(
            id=str(plan.id),
            order_id=str(plan.order_id),
            tasks=[FulfillmentTaskOut.from_orm_row(t) for t in tasks],
            milestones=[FulfillmentMilestoneOut(**m) for m in plan.milestones],
            critical_path_hours=plan.critical_path_hours,
        )


class CandidateOut(BaseModel):
    worker_id: str
    full_name: str
    profile_photo_url: str | None = None
    headline: str
    community_type: str
    score: float
    rationale: str
    availability: str
    seller_level: str
    tasks_completed: int
    on_time_pct: float


class SetPreferencesIn(BaseModel):
    ranked_worker_ids: list[str] = Field(min_length=3)


class PreferenceEntryOut(BaseModel):
    worker_id: str
    rank: int


class PreferenceSetOut(BaseModel):
    id: str
    task_id: str
    order_id: str
    entries: list[PreferenceEntryOut]
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "PreferenceSetOut":
        return cls(
            id=str(row.id),
            task_id=str(row.task_id),
            order_id=str(row.order_id),
            entries=[PreferenceEntryOut(**e) for e in row.entries],
            created_at=row.created_at,
        )
