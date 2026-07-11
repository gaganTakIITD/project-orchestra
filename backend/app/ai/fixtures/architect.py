"""Fixture-first Architect — 5-task Launch Studio DAG."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


def build_plan_fixture(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
) -> dict[str, Any]:
    """Return plan + task blueprint matching lib/mock-data.ts Launch Studio DAG."""
    now = datetime.now(timezone.utc)
    total_days = max((order_deadline - now).days, 9)

    def offset_days(fraction: float) -> datetime:
        return now + timedelta(days=max(1, int(total_days * fraction)))

    task_ids = [uuid.uuid4() for _ in range(5)]
    id_str = [str(t) for t in task_ids]

    tasks = [
        {
            "id": task_ids[0],
            "task_type_slug": "brand_identity",
            "title": "Brand direction",
            "description": "Define the visual direction: mood, palette, typography.",
            "acceptance_criteria": [
                {"criterion": "Mood board + palette + type approved", "check_type": "human_required"},
            ],
            "status": "ready",
            "sequence_order": 1,
            "payout_amount": 1500,
            "deadline": offset_days(0.33),
            "depends_on": [],
        },
        {
            "id": task_ids[1],
            "task_type_slug": "logo_design",
            "title": "Logo design",
            "description": "Design the logo in SVG + PNG.",
            "acceptance_criteria": [
                {
                    "criterion": "Logo delivered in SVG and PNG",
                    "check_type": "deterministic",
                    "rule": "files_include_format(['svg','png'])",
                },
                {
                    "criterion": "Matches approved brand direction",
                    "check_type": "ai_judged",
                    "rubric": "Consistent with mood board and palette.",
                },
            ],
            "status": "blocked",
            "sequence_order": 2,
            "payout_amount": 2000,
            "deadline": offset_days(0.55),
            "depends_on": [id_str[0]],
        },
        {
            "id": task_ids[2],
            "task_type_slug": "figma_ui_design",
            "title": "UI design",
            "description": "Design the landing page UI in Figma.",
            "acceptance_criteria": [
                {"criterion": "Desktop + mobile frames", "check_type": "human_required"},
            ],
            "status": "blocked",
            "sequence_order": 3,
            "payout_amount": 3000,
            "deadline": offset_days(0.7),
            "depends_on": [id_str[1]],
        },
        {
            "id": task_ids[3],
            "task_type_slug": "landing_page_frontend",
            "title": "Build landing page",
            "description": "Implement the landing page (Next.js + Tailwind).",
            "acceptance_criteria": [
                {
                    "criterion": "Lighthouse performance >= 70 on mobile",
                    "check_type": "deterministic",
                    "rule": "lighthouse_performance >= 70",
                },
                {
                    "criterion": "Responsive on mobile and desktop",
                    "check_type": "deterministic",
                    "rule": "responsive_check_pass",
                },
            ],
            "status": "blocked",
            "sequence_order": 4,
            "payout_amount": 4000,
            "deadline": offset_days(0.85),
            "depends_on": [id_str[2]],
        },
        {
            "id": task_ids[4],
            "task_type_slug": "deployment_devops",
            "title": "Deploy",
            "description": "Deploy the landing page to a live URL.",
            "acceptance_criteria": [
                {"criterion": "URL reachable (200)", "check_type": "deterministic", "rule": "url_reachable"},
            ],
            "status": "blocked",
            "sequence_order": 5,
            "payout_amount": 1000,
            "deadline": order_deadline,
            "depends_on": [id_str[3]],
        },
    ]

    milestones = [
        {
            "name": "Brand ready",
            "task_ids": [id_str[0], id_str[1]],
            "client_label": "Brand identity complete",
        },
        {
            "name": "Design ready",
            "task_ids": [id_str[2]],
            "client_label": "UI design complete",
        },
        {
            "name": "Live site",
            "task_ids": [id_str[3], id_str[4]],
            "client_label": "Website live",
        },
    ]

    return {
        "critical_path_hours": 30,
        "milestones": milestones,
        "tasks": tasks,
    }


def match_candidates_fixture(*, task_id: uuid.UUID) -> list[dict[str, Any]]:
    """Fixture Matcher shortlist — same shape as lib/mock-data mockCandidates."""
    _ = task_id
    return [
        {
            "worker_id": "usr_worker_rohan",
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
