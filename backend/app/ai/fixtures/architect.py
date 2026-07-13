"""Fixture-first Architect — thin wrapper over spec-driven builder."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.ai.architect import DEFAULT_MAPPED_TASK_TYPES, build_plan_from_spec


def build_plan_fixture(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
    mapped_task_types: list[str] | None = None,
    order_price: float | None = None,
) -> dict[str, Any]:
    """Return plan + task blueprint (Launch Studio DAG when types omitted)."""
    return build_plan_from_spec(
        order_id=order_id,
        order_deadline=order_deadline,
        revision_limit=revision_limit,
        order_price=order_price,
        mapped_task_types=mapped_task_types or list(DEFAULT_MAPPED_TASK_TYPES),
    )


def match_candidates_fixture(*, task_id: uuid.UUID) -> list[dict[str, Any]]:
    """Fixture Matcher shortlist — demo worker UUID matches DEMO_WORKER_ID seed."""
    from app.models.identity import DEMO_WORKER_ID

    _ = task_id
    wid = str(DEMO_WORKER_ID)
    return [
        {
            "worker_id": wid,
            "full_name": "Rohan Verma",
            "profile_photo_url": None,
            "headline": "Brand & logo designer — clean, systematic identities",
            "community_type": "design",
            "score": 0.92,
            "rationale": "Expert in logo_design, 27 completed tasks, 96% on-time, healthcare brand in portfolio.",
            "availability": "available",
            "seller_level": "trusted",
            "tasks_completed": 27,
            "on_time_pct": 96,
        },
        {
            "worker_id": "usr_worker_meera",
            "full_name": "Meera Nair",
            "profile_photo_url": None,
            "headline": "Identity designer, motion-curious",
            "community_type": "design",
            "score": 0.86,
            "rationale": "Advanced logo_design, strong minimalist portfolio, 94% on-time.",
            "availability": "available",
            "seller_level": "rising",
            "tasks_completed": 14,
            "on_time_pct": 94,
        },
        {
            "worker_id": "usr_worker_kabir",
            "full_name": "Kabir Anand",
            "profile_photo_url": None,
            "headline": "Designer & illustrator",
            "community_type": "design",
            "score": 0.79,
            "rationale": "Good fit on style; fewer healthcare samples; 90% on-time.",
            "availability": "busy",
            "seller_level": "rising",
            "tasks_completed": 9,
            "on_time_pct": 90,
        },
    ]
