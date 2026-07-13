"""Architect — DAG validation, spec-driven fixture, gateway + build_plan."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.ai.architect import (
    ALLOWED_TASK_TYPE_SLUGS,
    InvalidPlanError,
    build_plan_from_spec,
    normalize_mapped_task_types,
    validate_dag,
)
from app.ai.gateway import generate_plan_proposal
from app.config import settings
from app.models.commerce import Intent, OutcomeSpecRecord
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID
from app.models.platform import AiDecisionLog
from app.orchestrator.states import OrderStatus, TaskStatus
from app.services.fulfillment import FulfillmentService


def _deadline(days: int = 14) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def _linear_blueprint(slugs: list[str]) -> dict:
    ids = [uuid.uuid4() for _ in slugs]
    id_str = [str(i) for i in ids]
    tasks = []
    for i, slug in enumerate(slugs):
        tasks.append(
            {
                "id": ids[i],
                "task_type_slug": slug,
                "title": slug,
                "description": slug,
                "acceptance_criteria": [],
                "sequence_order": i + 1,
                "payout_amount": 1000,
                "deadline": _deadline(),
                "depends_on": [] if i == 0 else [id_str[i - 1]],
            }
        )
    return {
        "critical_path_hours": 10,
        "milestones": [{"name": "All", "task_ids": id_str, "client_label": "Done"}],
        "tasks": tasks,
    }


def test_validate_dag_accepts_linear():
    blueprint = _linear_blueprint(["brand_identity", "logo_design", "figma_ui_design"])
    validate_dag(
        blueprint,
        mapped_task_types=["brand_identity", "logo_design", "figma_ui_design"],
        allowed_slugs=ALLOWED_TASK_TYPE_SLUGS,
    )


def test_validate_dag_rejects_cycle():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # Root A; B↔C cycle
    blueprint = {
        "critical_path_hours": 4,
        "milestones": [],
        "tasks": [
            {
                "id": a,
                "task_type_slug": "brand_identity",
                "title": "A",
                "description": "",
                "acceptance_criteria": [],
                "sequence_order": 1,
                "payout_amount": 1,
                "deadline": _deadline(),
                "depends_on": [],
            },
            {
                "id": b,
                "task_type_slug": "logo_design",
                "title": "B",
                "description": "",
                "acceptance_criteria": [],
                "sequence_order": 2,
                "payout_amount": 1,
                "deadline": _deadline(),
                "depends_on": [str(a), str(c)],
            },
            {
                "id": c,
                "task_type_slug": "figma_ui_design",
                "title": "C",
                "description": "",
                "acceptance_criteria": [],
                "sequence_order": 3,
                "payout_amount": 1,
                "deadline": _deadline(),
                "depends_on": [str(b)],
            },
        ],
    }
    with pytest.raises(InvalidPlanError, match="cycle"):
        validate_dag(blueprint, allowed_slugs=ALLOWED_TASK_TYPE_SLUGS)


def test_validate_dag_rejects_unknown_slug():
    blueprint = _linear_blueprint(["brand_identity"])
    blueprint["tasks"][0]["task_type_slug"] = "fake_type"
    with pytest.raises(InvalidPlanError, match="Unknown task_type_slug"):
        validate_dag(blueprint, allowed_slugs=ALLOWED_TASK_TYPE_SLUGS)


def test_validate_dag_rejects_missing_root():
    a, b = uuid.uuid4(), uuid.uuid4()
    # Both depend on each other via a third missing pattern — make each depend
    # on the other so there is no empty depends_on (also a cycle).
    blueprint = {
        "critical_path_hours": 4,
        "milestones": [],
        "tasks": [
            {
                "id": a,
                "task_type_slug": "brand_identity",
                "title": "A",
                "description": "",
                "acceptance_criteria": [],
                "sequence_order": 1,
                "payout_amount": 1,
                "deadline": _deadline(),
                "depends_on": [str(b)],
            },
            {
                "id": b,
                "task_type_slug": "logo_design",
                "title": "B",
                "description": "",
                "acceptance_criteria": [],
                "sequence_order": 2,
                "payout_amount": 1,
                "deadline": _deadline(),
                "depends_on": [str(a)],
            },
        ],
    }
    with pytest.raises(InvalidPlanError):
        validate_dag(blueprint, allowed_slugs=ALLOWED_TASK_TYPE_SLUGS)


def test_fixture_plan_honors_mapped_types():
    mapped = ["brand_identity", "logo_design"]
    plan = build_plan_from_spec(
        order_id=uuid.uuid4(),
        order_deadline=_deadline(),
        revision_limit=2,
        order_price=6000,
        mapped_task_types=mapped,
    )
    slugs = [t["task_type_slug"] for t in plan["tasks"]]
    assert slugs == mapped
    assert len(plan["tasks"]) == 2
    assert plan["tasks"][0]["depends_on"] == []
    assert plan["tasks"][1]["depends_on"] == [str(plan["tasks"][0]["id"])]


def test_fixture_plan_defaults_to_launch_studio():
    plan = build_plan_from_spec(
        order_id=uuid.uuid4(),
        order_deadline=_deadline(),
        revision_limit=2,
        mapped_task_types=[],
    )
    assert len(plan["tasks"]) == 5
    assert len(plan["milestones"]) == 3
    assert plan["tasks"][0]["task_type_slug"] == "brand_identity"


def test_normalize_human_labels_from_gemini():
    assert normalize_mapped_task_types(["Brand Strategy", "Logo Design", "Landing Page"]) == [
        "brand_identity",
        "logo_design",
        "landing_page_frontend",
    ]
    plan = build_plan_from_spec(
        order_id=uuid.uuid4(),
        order_deadline=_deadline(),
        revision_limit=2,
        order_price=14000,
        mapped_task_types=["Brand Strategy", "UI Design", "Deployment"],
    )
    assert [t["task_type_slug"] for t in plan["tasks"]] == [
        "brand_identity",
        "figma_ui_design",
        "deployment_devops",
    ]


def test_gateway_fixture_path(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    proposal = generate_plan_proposal(
        order_id=uuid.uuid4(),
        order_deadline=_deadline(),
        revision_limit=2,
        order_price=14000,
        spec={
            "outcome_statement": "Brand + logo only",
            "mapped_task_types": ["brand_identity", "logo_design"],
            "deliverables": [],
            "acceptance_criteria": [],
        },
    )
    assert proposal.source == "fixture"
    assert proposal.error is None
    slugs = [t["task_type_slug"] for t in proposal.plan["tasks"]]
    assert slugs == ["brand_identity", "logo_design"]
    validate_dag(
        proposal.plan,
        mapped_task_types=["brand_identity", "logo_design"],
        allowed_slugs=ALLOWED_TASK_TYPE_SLUGS,
    )


@pytest.fixture
async def db_session():
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
            yield session
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")


@pytest.mark.asyncio
async def test_build_plan_uses_spec_types(db_session, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    mapped = ["brand_identity", "logo_design"]
    intent = Intent(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        raw_text="Brand and logo only",
        attachments=[],
        status="captured",
    )
    db_session.add(intent)
    await db_session.flush()

    spec = OutcomeSpecRecord(
        id=uuid.uuid4(),
        intent_id=intent.id,
        outcome_statement="Brand identity and logo for HealthTrack.",
        deliverables=[{"name": "Logo", "format": "SVG", "required": True}],
        acceptance_criteria=[],
        in_scope=["Logo"],
        out_of_scope=["Landing page"],
        assumptions=[],
        client_inputs_required=["company_name"],
        mapped_task_types=mapped,
        risk_tier="L1",
        version=1,
        frozen_at=datetime.now(timezone.utc),
    )
    db_session.add(spec)
    await db_session.flush()

    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        quote_id=None,
        spec_id=spec.id,
        status=OrderStatus.CONFIRMED,
        price=Decimal("6000.00"),
        deadline=_deadline(),
        revision_limit=2,
    )
    db_session.add(order)
    await db_session.flush()

    svc = FulfillmentService(db_session)
    plan = await svc.build_plan(order=order, spec=spec)
    await db_session.flush()

    tasks = (
        await db_session.execute(
            select(FulfillmentTask)
            .where(FulfillmentTask.order_id == order.id)
            .order_by(FulfillmentTask.sequence_order)
        )
    ).scalars().all()
    assert len(tasks) == 2
    assert [t.task_type_slug for t in tasks] == mapped
    assert tasks[0].status == TaskStatus.READY
    assert tasks[1].status == TaskStatus.BLOCKED

    logs = (
        await db_session.execute(
            select(AiDecisionLog).where(AiDecisionLog.agent_type == "architect")
        )
    ).scalars().all()
    assert len(logs) >= 1
    assert logs[0].source == "fixture"
    assert logs[0].output_draft["task_count"] == 2
    assert plan.critical_path_hours == 10  # 4 + 6
