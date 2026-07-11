from datetime import datetime

from pydantic import BaseModel, Field


class WorkerStatsOut(BaseModel):
    worker_id: str
    tasks_completed: int = 0
    on_time_pct: float = 0
    avg_qa_score: float = 0
    avg_rating: float = 0
    response_time_hours: float | None = None
    seller_level: str = "new"
    last_active_at: str | None = None


class WorkerProfileOut(BaseModel):
    user_id: str
    full_name: str
    profile_photo_url: str | None = None
    community_type: str
    headline: str
    bio: str
    availability_status: str
    weekly_hours_available: int
    max_concurrent_tasks: int
    payout_min: float | None = None
    payout_max: float | None = None
    campus_verified: bool
    is_active: bool
    profile_completion_pct: int
    github_url: str | None = None
    figma_url: str | None = None
    behance_url: str | None = None
    linkedin_url: str | None = None
    skills: list[dict] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    task_types: list[dict] = Field(default_factory=list)
    portfolio: list[dict] = Field(default_factory=list)
    stats: WorkerStatsOut | None = None

    @classmethod
    def from_orm_rows(cls, user, profile) -> "WorkerProfileOut":
        stats = profile.stats
        stats_out = WorkerStatsOut(**stats) if isinstance(stats, dict) else None
        return cls(
            user_id=str(user.id),
            full_name=user.full_name,
            profile_photo_url=user.profile_photo_url,
            community_type=profile.community_type,
            headline=profile.headline,
            bio=profile.bio,
            availability_status=profile.availability_status,
            weekly_hours_available=profile.weekly_hours_available,
            max_concurrent_tasks=profile.max_concurrent_tasks,
            payout_min=profile.payout_min,
            payout_max=profile.payout_max,
            campus_verified=profile.campus_verified,
            is_active=profile.is_active and user.is_active,
            profile_completion_pct=profile.profile_completion_pct,
            github_url=profile.github_url,
            figma_url=profile.figma_url,
            behance_url=profile.behance_url,
            linkedin_url=profile.linkedin_url,
            skills=profile.skills or [],
            tools=profile.tools or [],
            task_types=profile.task_types or [],
            portfolio=profile.portfolio or [],
            stats=stats_out,
        )


class CharterSnapshotOut(BaseModel):
    scope: str
    deliverables: list[dict] = Field(default_factory=list)
    acceptance_criteria: list[dict] = Field(default_factory=list)
    price: float
    deadline: str
    revision_limit: int
    out_of_scope: list[str] = Field(default_factory=list)


class CharterOut(BaseModel):
    id: str
    order_id: str
    task_id: str | None = None
    version: int
    snapshot: CharterSnapshotOut
    mutual_start_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "CharterOut":
        snap = row.snapshot or {}
        deadline = snap.get("deadline")
        if hasattr(deadline, "isoformat"):
            deadline = deadline.isoformat()
        return cls(
            id=str(row.id),
            order_id=str(row.order_id),
            task_id=str(row.task_id) if row.task_id else None,
            version=row.version,
            snapshot=CharterSnapshotOut(
                scope=snap.get("scope") or "",
                deliverables=snap.get("deliverables") or [],
                acceptance_criteria=snap.get("acceptance_criteria") or [],
                price=float(snap.get("price") or 0),
                deadline=str(deadline or ""),
                revision_limit=int(snap.get("revision_limit") or 2),
                out_of_scope=snap.get("out_of_scope") or [],
            ),
            mutual_start_at=row.mutual_start_at,
            created_at=row.created_at,
        )


class TaskPacketOut(BaseModel):
    id: str
    task_id: str
    charter_id: str
    version: int
    brief: str
    checklist: list[dict] = Field(default_factory=list)
    client_inputs: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "TaskPacketOut":
        return cls(
            id=str(row.id),
            task_id=str(row.task_id),
            charter_id=str(row.charter_id),
            version=row.version,
            brief=row.brief or "",
            checklist=row.checklist or [],
            client_inputs=row.client_inputs or [],
            dependencies=row.dependencies or [],
            references=row.references or [],
            created_at=row.created_at,
        )
