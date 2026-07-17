from datetime import datetime

from pydantic import BaseModel, Field


class EnrichPlanOut(BaseModel):
    """POST /orders/{id}/enrich-plan — progressive AI polish after fast confirm."""

    order_id: str
    status: str  # enriched | partial | skipped | unchanged
    tasks_total: int
    tasks_enriched: int
    tasks_failed: int
    message: str = ""


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


class SubmitWorkIn(BaseModel):
    notes: str = ""
    asset_urls: list[str] = Field(default_factory=list)


class TaskStatusOut(BaseModel):
    status: str


class SubmissionOut(BaseModel):
    id: str
    task_id: str
    worker_id: str
    notes: str | None = None
    asset_urls: list[str]
    version: int
    submitted_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "SubmissionOut":
        return cls(
            id=str(row.id),
            task_id=str(row.task_id),
            worker_id=str(row.worker_id),
            notes=row.notes,
            asset_urls=row.asset_urls or [],
            version=row.version,
            submitted_at=row.submitted_at,
        )


class DiscussionMessageIn(BaseModel):
    body: str = Field(min_length=1)
    message_type: str = "clarification"
    attachments: list[str] = Field(default_factory=list)


class DiscussionMessageOut(BaseModel):
    id: str
    thread_id: str
    sender_id: str
    sender_name: str
    body: str
    message_type: str
    attachments: list[str]
    scope_flagged: bool
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "DiscussionMessageOut":
        return cls(
            id=str(row.id),
            thread_id=str(row.thread_id),
            sender_id=str(row.sender_id),
            sender_name=row.sender_name,
            body=row.body,
            message_type=row.message_type,
            attachments=row.attachments or [],
            scope_flagged=bool(row.scope_flagged),
            created_at=row.created_at,
        )


class DiscussionThreadOut(BaseModel):
    id: str
    task_id: str
    order_id: str
    status: str
    messages: list[DiscussionMessageOut]

    @classmethod
    def from_orm_rows(cls, thread, messages) -> "DiscussionThreadOut":
        return cls(
            id=str(thread.id),
            task_id=str(thread.task_id),
            order_id=str(thread.order_id),
            status=thread.status,
            messages=[DiscussionMessageOut.from_orm_row(m) for m in messages],
        )


class DeliveryBundleAssetOut(BaseModel):
    name: str
    url: str
    type: str


class DeliveryBundleOut(BaseModel):
    id: str
    order_id: str
    assets: list[DeliveryBundleAssetOut]
    qa_summary: str
    delivered_at: datetime
    accepted_at: datetime | None = None
    accepted_by: str | None = None

    @classmethod
    def from_orm_row(cls, row) -> "DeliveryBundleOut":
        return cls(
            id=str(row.id),
            order_id=str(row.order_id),
            assets=[DeliveryBundleAssetOut(**a) for a in (row.assets or [])],
            qa_summary=row.qa_summary or "",
            delivered_at=row.delivered_at,
            accepted_at=row.accepted_at,
            accepted_by=str(row.accepted_by) if row.accepted_by else None,
        )
