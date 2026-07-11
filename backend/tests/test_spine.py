import uuid

import pytest
from sqlalchemy import select

from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.platform import EventLog
from app.orchestrator.spine import OrderSpine, TaskSpine
from app.orchestrator.states import OrderStatus, TaskStatus
from app.orchestrator.transitions import IllegalTransitionError, resolve_transition, TASK_TRANSITIONS


# --- Pure transition graph tests (no DB) ---


def test_task_blocked_to_ready_to_invited():
    status = "blocked"
    status = resolve_transition("task", TASK_TRANSITIONS, status, "dependencies_met")
    assert status == "ready"
    status = resolve_transition("task", TASK_TRANSITIONS, status, "preferences_set")
    assert status == "invited"


def test_illegal_task_transition_raises():
    with pytest.raises(IllegalTransitionError) as exc:
        resolve_transition("task", TASK_TRANSITIONS, "blocked", "preferences_set")
    assert exc.value.from_status == "blocked"
    assert exc.value.event == "preferences_set"


def test_completed_task_cannot_transition():
    with pytest.raises(IllegalTransitionError):
        resolve_transition("task", TASK_TRANSITIONS, "completed", "submitted")


# --- Integration tests (Postgres via docker-compose or skip) ---


@pytest.fixture
async def db_session():
    """Use real Postgres if available; skip otherwise."""
    from app.config import settings
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


@pytest.mark.asyncio
async def test_spine_task_transitions_persist_events(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        status=OrderStatus.CONFIRMED,
        price=14000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Logo design",
        status=TaskStatus.BLOCKED,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=2000,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()

    spine = TaskSpine(db_session)

    await spine.transition(task, "dependencies_met")
    assert task.status == TaskStatus.READY

    await spine.transition(task, "preferences_set", actor_type="client")
    assert task.status == TaskStatus.INVITED

    await db_session.commit()

    result = await db_session.execute(
        select(EventLog).where(
            EventLog.aggregate_type == "task",
            EventLog.aggregate_id == task.id,
        )
    )
    events = result.scalars().all()
    assert len(events) == 2
    assert events[0].payload["from_status"] == "blocked"
    assert events[0].payload["to_status"] == "ready"
    assert events[1].event_type == "PreferencesSet"


@pytest.mark.asyncio
async def test_spine_illegal_transition_in_db(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        status=OrderStatus.CONFIRMED,
        price=1000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Test",
        status=TaskStatus.BLOCKED,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=1000,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()

    spine = TaskSpine(db_session)
    with pytest.raises(IllegalTransitionError):
        await spine.transition(task, "preferences_set")
