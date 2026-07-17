"""Reliability gates — order Spine matrix + priority timeout on HTTP tick path."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import DEMO_WORKER_ID, DEMO_WORKER_MEERA_ID
from app.models.platform import EventLog, TimerRecord
from app.orchestrator.spine import OrderSpine
from app.orchestrator.states import OrderStatus, TaskStatus
from app.orchestrator.timers import DurableTimerService, TimerKind, TimerStatus
from app.orchestrator.transitions import (
    ORDER_TRANSITIONS,
    IllegalTransitionError,
    resolve_transition,
)


# --- Order transition graph (no DB) ---


@pytest.mark.parametrize(
    "from_status,event,to_status",
    [
        (from_s, event, to_s)
        for (from_s, event), to_s in ORDER_TRANSITIONS.items()
    ],
)
def test_order_legal_transitions(from_status: str, event: str, to_status: str):
    assert (
        resolve_transition("order", ORDER_TRANSITIONS, from_status, event)
        == to_status
    )


@pytest.mark.parametrize(
    "from_status,event",
    [
        ("confirmed", "bundle_ready"),
        ("delivered", "plan_and_preferences_set"),
        ("closed", "client_accept"),
        ("assembling_team", "cancel"),
        ("blocked", "dependencies_met"),  # task event on order aggregate
    ],
)
def test_order_illegal_transitions_raise(from_status: str, event: str):
    with pytest.raises(IllegalTransitionError) as exc:
        resolve_transition("order", ORDER_TRANSITIONS, from_status, event)
    assert exc.value.aggregate == "order"
    assert exc.value.from_status == from_status
    assert exc.value.event == event


def test_closed_order_cannot_transition():
    with pytest.raises(IllegalTransitionError):
        resolve_transition("order", ORDER_TRANSITIONS, "closed", "client_accept")


# --- Order Spine integration (Postgres) ---


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


@pytest.mark.asyncio
async def test_order_spine_transitions_persist_events(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        status=OrderStatus.CONFIRMED,
        price=14000,
    )
    db_session.add(order)
    await db_session.flush()

    spine = OrderSpine(db_session)

    await spine.transition(order, "plan_and_preferences_set", actor_type="client")
    assert order.status == OrderStatus.ASSEMBLING_TEAM

    await spine.transition(order, "first_mutual_start")
    assert order.status == OrderStatus.DELIVERY_ACTIVE

    await db_session.commit()

    result = await db_session.execute(
        select(EventLog).where(
            EventLog.aggregate_type == "order",
            EventLog.aggregate_id == order.id,
        )
    )
    events = result.scalars().all()
    assert len(events) == 2
    assert events[0].payload["from_status"] == "confirmed"
    assert events[0].payload["to_status"] == "assembling_team"
    assert events[1].payload["to_status"] == "delivery_active"


@pytest.mark.asyncio
async def test_order_spine_illegal_transition_in_db(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        status=OrderStatus.CONFIRMED,
        price=1000,
    )
    db_session.add(order)
    await db_session.flush()

    spine = OrderSpine(db_session)
    with pytest.raises(IllegalTransitionError):
        await spine.transition(order, "client_accept")


# --- Priority timeout via HTTP tick (scheduler path) ---


@pytest.fixture
async def api_client():
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)
            await seed_demo_worker(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


_DEMO_RANKED = [
    str(DEMO_WORKER_ID),
    str(DEMO_WORKER_MEERA_ID),
    "usr_worker_kabir",
]


@pytest.mark.asyncio
async def test_priority_window_tick_promotes_backup_worker(api_client: AsyncClient):
    """Accept-interest → due timer → POST /internal/timers/tick → backup assigned."""
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "Launch Studio brand and landing for HealthTrack.",
            "attachments": [],
        },
    )
    assert create.status_code == 201
    quote_id = create.json()["quote_id"]

    accept = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept.status_code == 200
    order_id = accept.json()["order_id"]

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    task_id = next(t["id"] for t in plan["tasks"] if t["status"] == TaskStatus.READY)

    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": list(_DEMO_RANKED)},
    )
    assert pref.status_code == 200

    accept_interest = await api_client.post(
        f"/api/v1/tasks/{task_id}/accept-interest"
    )
    assert accept_interest.status_code == 200
    assert accept_interest.json()["status"] == "accepted"

    # Force timer due (simulates Cloud Scheduler tick after priority window).
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        task = await session.get(FulfillmentTask, uuid.UUID(task_id))
        assert task is not None
        assert task.assigned_worker_id == DEMO_WORKER_ID

        timers = DurableTimerService(session)
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        row = await timers.schedule(
            kind=TimerKind.PRIORITY_WINDOW,
            aggregate_id=task.id,
            fire_at=past,
            payload={"worker_id": str(DEMO_WORKER_ID)},
        )
        assert row.status == TimerStatus.PENDING
        await session.commit()

    tick = await api_client.post("/api/v1/internal/timers/tick")
    assert tick.status_code == 200, tick.text
    body = tick.json()
    assert body["fired"] >= 1
    assert any(r.get("action") == "promote_backup" for r in body["results"])

    async with AsyncSessionLocal() as session:
        task = await session.get(FulfillmentTask, uuid.UUID(task_id))
        assert task is not None
        assert task.assigned_worker_id == DEMO_WORKER_MEERA_ID
        assert task.status == TaskStatus.PRIORITY_ACTIVE

        fired = (
            await session.execute(
                select(TimerRecord).where(
                    TimerRecord.aggregate_id == task.id,
                    TimerRecord.status == TimerStatus.FIRED,
                )
            )
        ).scalars().all()
        assert len(fired) >= 1

        expired = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "task",
                    EventLog.aggregate_id == task.id,
                    EventLog.event_type == "ActivationExpired",
                )
            )
        ).scalars().all()
        assert len(expired) == 1
        assert expired[0].payload["to_worker_id"] == str(DEMO_WORKER_MEERA_ID)
