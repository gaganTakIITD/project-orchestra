from datetime import datetime

from pydantic import BaseModel, Field


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
