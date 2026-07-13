"""Worker reputation stats — updated on QA pass/fail."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import WorkerStatsRecord


class WorkerStatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_worker(self, worker_id: uuid.UUID) -> list[WorkerStatsRecord]:
        result = await self.session.execute(
            select(WorkerStatsRecord).where(WorkerStatsRecord.worker_id == worker_id)
        )
        return list(result.scalars().all())

    async def record_qa(
        self,
        *,
        worker_id: uuid.UUID,
        task_type_slug: str | None,
        passed: bool,
        confidence: float | None,
    ) -> WorkerStatsRecord:
        slug = (task_type_slug or "general").strip() or "general"
        row = await self.session.scalar(
            select(WorkerStatsRecord).where(
                WorkerStatsRecord.worker_id == worker_id,
                WorkerStatsRecord.task_type_slug == slug,
            )
        )
        if row is None:
            row = WorkerStatsRecord(
                worker_id=worker_id,
                task_type_slug=slug,
                completed=0,
                reworked=0,
                avg_qa_confidence=None,
            )
            self.session.add(row)
            await self.session.flush()

        if passed:
            row.completed = int(row.completed or 0) + 1
        else:
            row.reworked = int(row.reworked or 0) + 1

        if confidence is not None:
            prev = float(row.avg_qa_confidence) if row.avg_qa_confidence is not None else None
            total_n = int(row.completed or 0) + int(row.reworked or 0)
            if prev is None or total_n <= 1:
                row.avg_qa_confidence = Decimal(str(round(confidence, 3)))
            else:
                # Running average over all QA events for this slug.
                new_avg = ((prev * (total_n - 1)) + confidence) / total_n
                row.avg_qa_confidence = Decimal(str(round(new_avg, 3)))

        await self.session.flush()
        return row
