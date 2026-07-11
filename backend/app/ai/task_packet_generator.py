"""Task Packet Generator — OutcomeSpec + Architect task → Charter + TaskPacket.

AI proposes (or fixture builds) the worker job card. Spine freezes Charter;
TaskPacket is the operational checklist the worker executes.
"""

from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def generate_charter_and_packet(
    *,
    order_id: uuid.UUID,
    task: Any,
    spec: dict[str, Any],
    order_price_share: float,
    order_deadline: datetime | None,
    revision_limit: int,
    dependency_titles: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (charter_fields, packet_fields) ready to persist.

    Fixture-first — replace body with Gemini Flash structured output later.
    """
    charter_id = uuid.uuid4()
    packet_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    deliverables = _slice_deliverables(spec.get("deliverables") or [], task.task_type_slug)
    criteria = list(task.acceptance_criteria or [])
    if not criteria:
        criteria = _default_criteria(task.title)

    scope = (
        task.description
        or f"Complete «{task.title}» as part of: {spec.get('outcome_statement') or 'the confirmed outcome'}."
    )

    charter = {
        "id": charter_id,
        "order_id": order_id,
        "task_id": task.id,
        "version": 1,
        "snapshot": {
            "scope": scope,
            "deliverables": deliverables,
            "acceptance_criteria": criteria,
            "price": float(order_price_share),
            "deadline": (task.deadline or order_deadline or now).isoformat(),
            "revision_limit": revision_limit,
            "out_of_scope": list(spec.get("out_of_scope") or []),
        },
        "mutual_start_at": None,
        "created_at": now,
    }

    checklist = []
    for i, ac in enumerate(criteria):
        label = ac.get("criterion") if isinstance(ac, dict) else str(ac)
        checklist.append(
            {
                "id": f"chk_{i + 1}",
                "label": label,
                "source_criterion": label,
                "required": True,
                "done": False,
            }
        )

    # Practical extras for the worker job card
    if task.task_type_slug == "logo_design":
        checklist.append(
            {
                "id": f"chk_{len(checklist) + 1}",
                "label": "Confirm mark works at favicon / small sizes",
                "required": True,
                "done": False,
            }
        )

    brief = (
        f"Job card for «{task.title}». "
        f"Deliver against the checklist; match the outcome: "
        f"{(spec.get('outcome_statement') or '')[:180]}"
    ).strip()

    packet = {
        "id": packet_id,
        "task_id": task.id,
        "charter_id": charter_id,
        "version": 1,
        "brief": brief,
        "checklist": checklist,
        "client_inputs": list(spec.get("client_inputs_required") or []),
        "dependencies": list(dependency_titles or []),
        "references": [],
        "created_at": now,
    }

    return charter, packet


def _slice_deliverables(deliverables: list, task_type_slug: str | None) -> list[dict]:
    mapping = {
        "brand_identity": ["Brand guide", "Mood"],
        "logo_design": ["Logo"],
        "figma_ui_design": ["Figma"],
        "landing_page_frontend": ["landing", "page", "Website"],
        "deployment_devops": ["Live", "URL", "Deploy"],
    }
    keys = mapping.get(task_type_slug or "", [])
    if not keys or not deliverables:
        return deepcopy(deliverables[:1]) if deliverables else []

    matched = []
    for d in deliverables:
        name = (d.get("name") if isinstance(d, dict) else str(d)).lower()
        if any(k.lower() in name for k in keys):
            matched.append(deepcopy(d) if isinstance(d, dict) else {"name": str(d), "format": "", "required": True})
    return matched or (deepcopy(deliverables[:1]) if deliverables else [])


def _default_criteria(title: str) -> list[dict]:
    return [
        {
            "criterion": f"«{title}» delivered and reviewed",
            "check_type": "human_required",
        }
    ]
