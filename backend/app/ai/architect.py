"""Architect — propose a fulfillment DAG from a frozen OutcomeSpec.

AI proposes; Spine validates via ``validate_dag`` then persists. Deterministic
``build_plan_from_spec`` is the fixture path and the Gemini skeleton.
"""

from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

DEFAULT_MAPPED_TASK_TYPES = [
    "brand_identity",
    "logo_design",
    "figma_ui_design",
    "landing_page_frontend",
    "deployment_devops",
]

ALLOWED_TASK_TYPE_SLUGS = frozenset(DEFAULT_MAPPED_TASK_TYPES)

# Gemini often returns display labels instead of catalog slugs.
_ALIAS_TO_SLUG: dict[str, str] = {
    "brand_identity": "brand_identity",
    "brand identity": "brand_identity",
    "brand strategy": "brand_identity",
    "brand direction": "brand_identity",
    "branding": "brand_identity",
    "logo_design": "logo_design",
    "logo design": "logo_design",
    "logo": "logo_design",
    "figma_ui_design": "figma_ui_design",
    "figma ui design": "figma_ui_design",
    "figma": "figma_ui_design",
    "ui design": "figma_ui_design",
    "ui": "figma_ui_design",
    "landing_page_frontend": "landing_page_frontend",
    "landing page frontend": "landing_page_frontend",
    "landing page": "landing_page_frontend",
    "landing": "landing_page_frontend",
    "frontend": "landing_page_frontend",
    "deployment_devops": "deployment_devops",
    "deployment devops": "deployment_devops",
    "deployment": "deployment_devops",
    "deploy": "deployment_devops",
    "devops": "deployment_devops",
}

# Typical hours from catalog seed — used for critical_path_hours.
_HOURS_BY_SLUG: dict[str, int] = {
    "brand_identity": 4,
    "logo_design": 6,
    "figma_ui_design": 8,
    "landing_page_frontend": 10,
    "deployment_devops": 2,
}

_FIXED_PAYOUT: dict[str, float] = {
    "brand_identity": 1500,
    "logo_design": 2000,
    "figma_ui_design": 3000,
    "landing_page_frontend": 4000,
    "deployment_devops": 1000,
}

_TASK_TEMPLATES: dict[str, dict[str, Any]] = {
    "brand_identity": {
        "title": "Brand direction",
        "description": "Define the visual direction: mood, palette, typography.",
        "acceptance_criteria": [
            {"criterion": "Mood board + palette + type approved", "check_type": "human_required"},
        ],
    },
    "logo_design": {
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
    },
    "figma_ui_design": {
        "title": "UI design",
        "description": "Design the landing page UI in Figma.",
        "acceptance_criteria": [
            {"criterion": "Desktop + mobile frames", "check_type": "human_required"},
        ],
    },
    "landing_page_frontend": {
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
    },
    "deployment_devops": {
        "title": "Deploy",
        "description": "Deploy the landing page to a live URL.",
        "acceptance_criteria": [
            {"criterion": "URL reachable (200)", "check_type": "deterministic", "rule": "url_reachable"},
        ],
    },
}


class InvalidPlanError(ValueError):
    """Raised when a proposed plan fails DAG / catalog validation."""


def normalize_mapped_task_types(raw: list[str] | None) -> list[str]:
    """Map Gemini/human labels onto catalog slugs; fall back to Launch Studio set."""
    ordered: list[str] = []
    seen: set[str] = set()
    for item in raw or []:
        key = str(item).strip().lower().replace("-", " ").replace("_", " ")
        key = " ".join(key.split())
        slug = _ALIAS_TO_SLUG.get(key)
        if slug is None:
            underscored = key.replace(" ", "_")
            if underscored in ALLOWED_TASK_TYPE_SLUGS:
                slug = underscored
            elif "logo" in key:
                slug = "logo_design"
            elif "figma" in key or "ui design" in key:
                slug = "figma_ui_design"
            elif "landing" in key or "frontend" in key:
                slug = "landing_page_frontend"
            elif "deploy" in key or "devops" in key:
                slug = "deployment_devops"
            elif "brand" in key:
                slug = "brand_identity"
        if slug and slug not in seen:
            seen.add(slug)
            ordered.append(slug)
    return ordered or list(DEFAULT_MAPPED_TASK_TYPES)


def validate_dag(
    blueprint: dict[str, Any],
    *,
    mapped_task_types: list[str] | None = None,
    allowed_slugs: frozenset[str] | set[str] | None = None,
) -> None:
    """Hard-gate a plan blueprint before Spine persist.

    Checks: ≥1 root, deps exist, acyclic (Kahn), known slugs, milestone refs,
    and mapped_task_types coverage when the frozen spec lists types.
    """
    allowed = allowed_slugs if allowed_slugs is not None else ALLOWED_TASK_TYPE_SLUGS
    tasks = blueprint.get("tasks") or []
    if not tasks:
        raise InvalidPlanError("Plan must include at least one task")

    id_set: set[str] = set()
    for task in tasks:
        tid = str(task["id"])
        if tid in id_set:
            raise InvalidPlanError(f"Duplicate task id: {tid}")
        id_set.add(tid)

    roots = 0
    indegree: dict[str, int] = {str(t["id"]): 0 for t in tasks}
    children: dict[str, list[str]] = defaultdict(list)

    for task in tasks:
        tid = str(task["id"])
        slug = task.get("task_type_slug") or ""
        if slug not in allowed:
            raise InvalidPlanError(f"Unknown task_type_slug: {slug!r}")

        deps = task.get("depends_on") or []
        if not deps:
            roots += 1
        for dep in deps:
            dep_s = str(dep)
            if dep_s not in id_set:
                raise InvalidPlanError(f"depends_on ref {dep_s} not in plan")
            if dep_s == tid:
                raise InvalidPlanError(f"Task {tid} depends on itself")
            children[dep_s].append(tid)
            indegree[tid] += 1

    if roots < 1:
        raise InvalidPlanError("Plan must have at least one root task (empty depends_on)")

    # Kahn topological sort — cycle if not all nodes visited.
    queue: deque[str] = deque([tid for tid, deg in indegree.items() if deg == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited != len(tasks):
        raise InvalidPlanError("Plan DAG contains a cycle")

    for milestone in blueprint.get("milestones") or []:
        for mid in milestone.get("task_ids") or []:
            if str(mid) not in id_set:
                raise InvalidPlanError(f"Milestone task_id {mid} not in plan")

    required = [s for s in (mapped_task_types or []) if s]
    if required:
        present = {t.get("task_type_slug") for t in tasks}
        missing = [s for s in required if s not in present]
        if missing:
            raise InvalidPlanError(f"mapped_task_types missing from plan: {missing}")


def build_plan_from_spec(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
    order_price: Decimal | float | None = None,
    mapped_task_types: list[str] | None = None,
    outcome_statement: str = "",
) -> dict[str, Any]:
    """Deterministic Architect — one task per mapped type, linear chain.

    Empty ``mapped_task_types`` falls back to the Launch Studio five-type list
    so existing intent→accept tests keep a 5-task plan.
    """
    _ = order_id, revision_limit, outcome_statement  # reserved for richer templates
    slugs = normalize_mapped_task_types(mapped_task_types)
    # Dedupe while preserving order (normalize already dedupes)
    ordered = slugs

    now = datetime.now(timezone.utc)
    total_days = max((order_deadline - now).days, max(9, len(ordered) * 2))

    def offset_days(fraction: float) -> datetime:
        return now + timedelta(days=max(1, int(total_days * fraction)))

    n = len(ordered)
    task_ids = [uuid.uuid4() for _ in range(n)]
    id_str = [str(t) for t in task_ids]

    payouts = _allocate_payouts(ordered, order_price)

    tasks: list[dict[str, Any]] = []
    for i, slug in enumerate(ordered):
        template = _TASK_TEMPLATES.get(slug) or {
            "title": slug.replace("_", " ").title(),
            "description": f"Complete the {slug.replace('_', ' ')} workstream.",
            "acceptance_criteria": [
                {"criterion": f"{slug} deliverable accepted", "check_type": "human_required"},
            ],
        }
        fraction = 1.0 if i == n - 1 else (i + 1) / (n + 1)
        deadline = order_deadline if i == n - 1 else offset_days(fraction)
        tasks.append(
            {
                "id": task_ids[i],
                "task_type_slug": slug,
                "title": template["title"],
                "description": template["description"],
                "acceptance_criteria": list(template["acceptance_criteria"]),
                "status": "ready" if i == 0 else "blocked",
                "sequence_order": i + 1,
                "payout_amount": payouts[i],
                "deadline": deadline,
                "depends_on": [] if i == 0 else [id_str[i - 1]],
            }
        )

    milestones = _build_milestones(tasks, id_str)
    critical_path_hours = sum(_HOURS_BY_SLUG.get(s, 4) for s in ordered)

    blueprint = {
        "critical_path_hours": critical_path_hours,
        "milestones": milestones,
        "tasks": tasks,
    }
    validate_dag(blueprint, mapped_task_types=ordered, allowed_slugs=ALLOWED_TASK_TYPE_SLUGS)
    return blueprint


def _allocate_payouts(slugs: list[str], order_price: Decimal | float | None) -> list[float]:
    """Prefer fixed catalog amounts when known; else split 80% of order price."""
    if all(s in _FIXED_PAYOUT for s in slugs):
        return [_FIXED_PAYOUT[s] for s in slugs]

    if order_price is not None and float(order_price) > 0:
        pool = float(order_price) * 0.8
        weights = [_HOURS_BY_SLUG.get(s, 4) for s in slugs]
        total_w = sum(weights) or len(slugs)
        raw = [round(pool * (w / total_w), 2) for w in weights]
        # Fix rounding drift on last task
        drift = round(pool - sum(raw), 2)
        raw[-1] = round(raw[-1] + drift, 2)
        return raw

    return [_FIXED_PAYOUT.get(s, 1000.0) for s in slugs]


def _build_milestones(tasks: list[dict[str, Any]], id_str: list[str]) -> list[dict[str, Any]]:
    n = len(tasks)
    if n == 1:
        return [
            {
                "name": "Delivery",
                "task_ids": [id_str[0]],
                "client_label": tasks[0]["title"],
            }
        ]
    if n == 2:
        return [
            {
                "name": "First milestone",
                "task_ids": [id_str[0]],
                "client_label": tasks[0]["title"],
            },
            {
                "name": "Complete",
                "task_ids": [id_str[1]],
                "client_label": tasks[1]["title"],
            },
        ]

    # ~thirds for 3+ tasks (matches Launch Studio: brand / design / live)
    a = max(1, n // 3)
    b = max(a + 1, (2 * n) // 3)
    groups = [
        ("Brand ready", "Brand identity complete", id_str[:a]),
        ("Design ready", "UI design complete", id_str[a:b]),
        ("Live site", "Website live", id_str[b:]),
    ]
    return [
        {"name": name, "task_ids": tids, "client_label": label}
        for name, label, tids in groups
        if tids
    ]
