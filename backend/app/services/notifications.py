"""In-app notifications — project selected event_log rows; list + mark-read."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.platform import EventLog, Notification
from app.schemas.notifications import AppNotificationOut

# Event types that fan out to notification rows (Spine catalog names).
_PROJECTED_EVENTS = frozenset(
    {
        "PreferencesSet",
        "InterestAccepted",
        "ActivationGranted",
        "QualityPassed",
        "QualityFailed",
        "OutcomeDelivered",
        "OutcomeClosed",
    }
)


def _parse_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def notification_to_out(row: Notification) -> AppNotificationOut:
    return AppNotificationOut(
        id=str(row.id),
        user_id=str(row.user_id),
        type=row.type,
        title=row.title,
        body=row.body,
        ref_type=row.ref_type,
        ref_id=str(row.ref_id) if row.ref_id else None,
        read=row.read,
        created_at=row.created_at,
    )


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[AppNotificationOut]:
        rows = (
            await self.session.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
            )
        ).scalars().all()
        return [notification_to_out(r) for r in rows]

    async def mark_read(self, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        row = await self.session.get(Notification, notification_id)
        if row is None or row.user_id != user_id:
            raise LookupError("Notification not found")
        if not row.read:
            row.read = True
            await self.session.flush()
        return row

    async def project_from_event(self, entry: EventLog) -> list[Notification]:
        """Create notification rows for a freshly flushed event_log entry."""
        if entry.event_type not in _PROJECTED_EVENTS:
            return []

        payload = dict(entry.payload or {})
        created: list[Notification] = []

        if entry.event_type == "PreferencesSet" and entry.aggregate_type == "task":
            created.extend(await self._project_invite(entry, payload))
        elif entry.event_type == "InterestAccepted" and entry.aggregate_type == "task":
            created.extend(await self._project_interest(entry, payload))
        elif entry.event_type == "ActivationGranted" and entry.aggregate_type == "task":
            created.extend(await self._project_priority(entry, payload))
        elif entry.event_type == "QualityPassed" and entry.aggregate_type == "task":
            created.extend(await self._project_qa(entry, payload, passed=True))
        elif entry.event_type == "QualityFailed" and entry.aggregate_type == "task":
            created.extend(await self._project_qa(entry, payload, passed=False))
        elif entry.event_type == "OutcomeDelivered" and entry.aggregate_type == "order":
            created.extend(await self._project_delivery(entry, ready=True))
        elif entry.event_type == "OutcomeClosed" and entry.aggregate_type == "order":
            created.extend(await self._project_delivery(entry, ready=False))

        for row in created:
            self.session.add(row)
        if created:
            await self.session.flush()
        return created

    async def _task_and_order(
        self, entry: EventLog, payload: dict[str, Any]
    ) -> tuple[FulfillmentTask | None, OutcomeOrder | None]:
        task = await self.session.get(FulfillmentTask, entry.aggregate_id)
        order_id = _parse_uuid(payload.get("order_id"))
        if order_id is None and task is not None:
            order_id = task.order_id
        order = await self.session.get(OutcomeOrder, order_id) if order_id else None
        return task, order

    async def _add(
        self,
        *,
        entry: EventLog,
        user_id: uuid.UUID,
        ntype: str,
        title: str,
        body: str,
        ref_type: str,
        ref_id: uuid.UUID,
    ) -> Notification:
        return Notification(
            user_id=user_id,
            type=ntype,
            title=title,
            body=body,
            ref_type=ref_type,
            ref_id=ref_id,
            read=False,
            source_event_id=entry.id,
        )

    def _worker_ids_from_invite_payload(self, payload: dict[str, Any]) -> list[uuid.UUID]:
        ids: list[uuid.UUID] = []
        ranked = payload.get("ranked_worker_ids") or []
        if isinstance(ranked, list):
            for raw in ranked:
                uid = _parse_uuid(raw)
                if uid is not None:
                    ids.append(uid)
        if not ids:
            uid = _parse_uuid(payload.get("worker_id"))
            if uid is not None:
                ids.append(uid)
        # Dedupe, preserve order
        seen: set[uuid.UUID] = set()
        out: list[uuid.UUID] = []
        for uid in ids:
            if uid not in seen:
                seen.add(uid)
                out.append(uid)
        return out

    async def _project_invite(
        self, entry: EventLog, payload: dict[str, Any]
    ) -> list[Notification]:
        # Order-level PreferencesSet (plan_and_preferences_set) — skip; task emit covers invite.
        if entry.aggregate_type != "task":
            return []
        task, _order = await self._task_and_order(entry, payload)
        title_label = task.title if task else "a task"
        workers = self._worker_ids_from_invite_payload(payload)
        return [
            await self._add(
                entry=entry,
                user_id=wid,
                ntype="invite",
                title="You're invited",
                body=f"You've been preferred for {title_label}. Accept interest to claim priority.",
                ref_type="task",
                ref_id=entry.aggregate_id,
            )
            for wid in workers
        ]

    async def _project_interest(
        self, entry: EventLog, payload: dict[str, Any]
    ) -> list[Notification]:
        task, order = await self._task_and_order(entry, payload)
        worker_id = _parse_uuid(payload.get("worker_id")) or (
            task.assigned_worker_id if task else None
        )
        title_label = task.title if task else "a task"
        rows: list[Notification] = []
        if worker_id is not None:
            rows.append(
                await self._add(
                    entry=entry,
                    user_id=worker_id,
                    ntype="interest_accepted",
                    title="Interest accepted",
                    body=f"You're in the interest pool for {title_label}.",
                    ref_type="task",
                    ref_id=entry.aggregate_id,
                )
            )
        if order is not None:
            rows.append(
                await self._add(
                    entry=entry,
                    user_id=order.client_id,
                    ntype="interest_accepted",
                    title="Worker interested",
                    body=f"A worker accepted interest on {title_label}.",
                    ref_type="task",
                    ref_id=entry.aggregate_id,
                )
            )
        return rows

    async def _project_priority(
        self, entry: EventLog, payload: dict[str, Any]
    ) -> list[Notification]:
        task, order = await self._task_and_order(entry, payload)
        worker_id = _parse_uuid(payload.get("worker_id")) or (
            task.assigned_worker_id if task else None
        )
        title_label = task.title if task else "a task"
        rows: list[Notification] = []
        if worker_id is not None:
            rows.append(
                await self._add(
                    entry=entry,
                    user_id=worker_id,
                    ntype="priority_granted",
                    title="You have priority",
                    body=f"You're first in line for {title_label}. Start within your priority window.",
                    ref_type="task",
                    ref_id=entry.aggregate_id,
                )
            )
        if order is not None:
            rows.append(
                await self._add(
                    entry=entry,
                    user_id=order.client_id,
                    ntype="priority_granted",
                    title="Priority assigned",
                    body=f"A worker has priority on {title_label}.",
                    ref_type="task",
                    ref_id=entry.aggregate_id,
                )
            )
        return rows

    async def _project_qa(
        self, entry: EventLog, payload: dict[str, Any], *, passed: bool
    ) -> list[Notification]:
        task, order = await self._task_and_order(entry, payload)
        worker_id = task.assigned_worker_id if task else None
        title_label = task.title if task else "a task"
        rows: list[Notification] = []
        if worker_id is not None:
            if passed:
                rows.append(
                    await self._add(
                        entry=entry,
                        user_id=worker_id,
                        ntype="qa_pass",
                        title="QA passed",
                        body=f"{title_label} passed quality review.",
                        ref_type="task",
                        ref_id=entry.aggregate_id,
                    )
                )
            else:
                rows.append(
                    await self._add(
                        entry=entry,
                        user_id=worker_id,
                        ntype="qa_fail",
                        title="QA needs rework",
                        body=f"{title_label} did not pass QA — please revise and resubmit.",
                        ref_type="task",
                        ref_id=entry.aggregate_id,
                    )
                )
        if not passed and order is not None:
            rows.append(
                await self._add(
                    entry=entry,
                    user_id=order.client_id,
                    ntype="qa_fail",
                    title="Revision in progress",
                    body=f"{title_label} is being revised after QA feedback.",
                    ref_type="task",
                    ref_id=entry.aggregate_id,
                )
            )
        return rows

    async def _project_delivery(
        self, entry: EventLog, *, ready: bool
    ) -> list[Notification]:
        order = await self.session.get(OutcomeOrder, entry.aggregate_id)
        if order is None:
            return []
        if ready:
            return [
                await self._add(
                    entry=entry,
                    user_id=order.client_id,
                    ntype="delivery_ready",
                    title="Delivery ready",
                    body="Your outcome is ready for review.",
                    ref_type="order",
                    ref_id=entry.aggregate_id,
                )
            ]
        return [
            await self._add(
                entry=entry,
                user_id=order.client_id,
                ntype="delivery_accepted",
                title="Delivery accepted",
                body="Outcome closed — thanks for confirming delivery.",
                ref_type="order",
                ref_id=entry.aggregate_id,
            )
        ]
