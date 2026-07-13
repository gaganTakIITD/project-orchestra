"""Durable priority timers — schedule + fire → promote_backup."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.fulfillment import FulfillmentTask, OutcomeOrder, TaskPreferenceSet
from app.models.identity import DEMO_WORKER_ID, DEMO_WORKER_MEERA_ID, User
from app.models.platform import EventLog, TimerRecord
from app.orchestrator.states import OrderStatus, TaskStatus
from app.orchestrator.timers import DurableTimerService, InMemoryTimerQueue, TimerKind, TimerStatus
from app.services.task_lifecycle import TaskLifecycleService
from app.services.timer_tick import tick_due_timers


def test_schedule_and_fire_timer():
    queue = InMemoryTimerQueue()
    timer = queue.schedule(
        TimerKind.PRIORITY_WINDOW,
        aggregate_id="task-123",
        delay=timedelta(hours=-1),  # already due
        payload={"worker_id": "w1"},
    )
    assert timer.kind == TimerKind.PRIORITY_WINDOW
    due = queue.due()
    assert len(due) == 1
    assert due[0].aggregate_id == "task-123"


@pytest.fixture
async def db_session():
    from app.db.base import Base
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    await engine.dispose()


async def _priority_task(
    session,
    *,
    assigned: uuid.UUID = DEMO_WORKER_ID,
    status: str = TaskStatus.PRIORITY_ACTIVE,
    entries: list[dict] | None = None,
) -> FulfillmentTask:
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        status=OrderStatus.ASSEMBLING_TEAM,
        price=Decimal("14000"),
    )
    session.add(order)
    await session.flush()

    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Logo design",
        status=status,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=Decimal("2000"),
        assigned_worker_id=assigned if status == TaskStatus.PRIORITY_ACTIVE else None,
    )
    session.add(task)
    await session.flush()

    pref = TaskPreferenceSet(
        task_id=task.id,
        order_id=order.id,
        entries=entries
        or [
            {"worker_id": str(DEMO_WORKER_ID), "rank": 1},
            {"worker_id": str(DEMO_WORKER_MEERA_ID), "rank": 2},
            {"worker_id": "usr_worker_kabir", "rank": 3},
        ],
    )
    session.add(pref)
    await session.flush()
    return task


@pytest.mark.asyncio
async def test_durable_schedule_and_tick_promotes_backup(db_session):
    task = await _priority_task(db_session)

    timers = DurableTimerService(db_session)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    row = await timers.schedule(
        kind=TimerKind.PRIORITY_WINDOW,
        aggregate_id=task.id,
        fire_at=past,
        payload={"worker_id": str(DEMO_WORKER_ID)},
    )
    assert row.status == TimerStatus.PENDING
    await db_session.commit()

    results = await tick_due_timers(db_session)
    await db_session.commit()

    assert len(results) == 1
    assert results[0]["action"] == "promote_backup"
    assert results[0]["assigned_worker_id"] == str(DEMO_WORKER_MEERA_ID)

    await db_session.refresh(task)
    assert task.status == TaskStatus.PRIORITY_ACTIVE
    assert task.assigned_worker_id == DEMO_WORKER_MEERA_ID
    assert task.priority_window_ends is not None

    fired = await db_session.get(TimerRecord, row.id)
    assert fired is not None
    assert fired.status == TimerStatus.FIRED

    events = (
        await db_session.execute(
            select(EventLog).where(
                EventLog.aggregate_type == "task",
                EventLog.aggregate_id == task.id,
                EventLog.event_type == "ActivationExpired",
            )
        )
    ).scalars().all()
    assert len(events) == 1
    assert events[0].payload["to_worker_id"] == str(DEMO_WORKER_MEERA_ID)

    pending = (
        await db_session.execute(
            select(TimerRecord).where(
                TimerRecord.aggregate_id == task.id,
                TimerRecord.status == TimerStatus.PENDING,
                TimerRecord.kind == TimerKind.PRIORITY_WINDOW,
            )
        )
    ).scalars().all()
    assert len(pending) == 1


@pytest.mark.asyncio
async def test_accept_interest_schedules_priority_timer(db_session):
    task = await _priority_task(
        db_session,
        status=TaskStatus.INVITED,
        assigned=DEMO_WORKER_ID,
        entries=[
            {"worker_id": str(DEMO_WORKER_ID), "rank": 1},
            {"worker_id": str(DEMO_WORKER_MEERA_ID), "rank": 2},
            {"worker_id": str(uuid.uuid4()), "rank": 3},
        ],
    )
    worker = User(
        id=DEMO_WORKER_ID,
        email="timer-worker@example.com",
        full_name="Timer Worker",
        role="worker",
    )
    db_session.add(worker)
    await db_session.flush()

    lifecycle = TaskLifecycleService(db_session)
    await lifecycle.accept_interest(task=task, worker=worker)
    await db_session.commit()

    assert task.status == TaskStatus.PRIORITY_ACTIVE
    assert task.assigned_worker_id == DEMO_WORKER_ID
    assert task.priority_window_ends is not None

    pending = (
        await db_session.execute(
            select(TimerRecord).where(
                TimerRecord.aggregate_id == task.id,
                TimerRecord.status == TimerStatus.PENDING,
                TimerRecord.kind == TimerKind.PRIORITY_WINDOW,
            )
        )
    ).scalars().all()
    assert len(pending) == 1
    assert pending[0].payload["worker_id"] == str(DEMO_WORKER_ID)


@pytest.mark.asyncio
async def test_timers_tick_endpoint_fires_due(db_session):
    """HTTP tick path used by Cloud Scheduler."""
    task = await _priority_task(db_session)

    timers = DurableTimerService(db_session)
    await timers.schedule(
        kind=TimerKind.PRIORITY_WINDOW,
        aggregate_id=task.id,
        fire_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        payload={"worker_id": str(DEMO_WORKER_ID)},
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/internal/timers/tick")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["fired"] >= 1
    assert any(r.get("action") == "promote_backup" for r in body["results"])

    await db_session.refresh(task)
    assert task.assigned_worker_id == DEMO_WORKER_MEERA_ID


@pytest.mark.asyncio
async def test_promote_backup_exhausts_when_no_uuid_backup(db_session):
    task = await _priority_task(
        db_session,
        entries=[
            {"worker_id": str(DEMO_WORKER_ID), "rank": 1},
            {"worker_id": "usr_worker_meera", "rank": 2},
            {"worker_id": "usr_worker_kabir", "rank": 3},
        ],
    )

    lifecycle = TaskLifecycleService(db_session)
    await lifecycle.promote_backup(task=task)
    await db_session.commit()

    assert task.status == TaskStatus.INVITED
    assert task.assigned_worker_id is None
