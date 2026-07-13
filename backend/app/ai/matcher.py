"""DB-backed Matcher — filter + score worker_profiles for a task shortlist.

AI never mutates state: this module only returns Candidate-shaped dicts.
Spine / fulfillment owns preference transitions.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask
from app.models.identity import User, WorkerProfileRecord
from app.schemas.worker import PROFILE_LIVE_THRESHOLD

PROFICIENCY_WEIGHT = {
    "beginner": 0.25,
    "intermediate": 0.5,
    "advanced": 0.75,
    "expert": 1.0,
}


def _task_type_slugs(profile: WorkerProfileRecord) -> set[str]:
    return {
        str(tt.get("slug") or "").lower()
        for tt in (profile.task_types or [])
        if isinstance(tt, dict) and tt.get("slug")
    }


def _skill_names(profile: WorkerProfileRecord) -> set[str]:
    names: set[str] = set()
    for skill in profile.skills or []:
        if isinstance(skill, dict) and skill.get("name"):
            names.add(str(skill["name"]).lower())
    return names


def _task_type_proficiency(profile: WorkerProfileRecord, slug: str) -> float:
    for tt in profile.task_types or []:
        if isinstance(tt, dict) and str(tt.get("slug") or "").lower() == slug.lower():
            return PROFICIENCY_WEIGHT.get(str(tt.get("proficiency") or "intermediate"), 0.5)
    return 0.0


def _matches_task(profile: WorkerProfileRecord, task_type_slug: str | None) -> bool:
    """Eligible if task_type slug matches, or skill/name overlaps the slug tokens."""
    if not task_type_slug:
        return True
    slug = task_type_slug.lower()
    if slug in _task_type_slugs(profile):
        return True
    # soft skill overlap: "logo_design" ↔ skill "Logo Design"
    token = slug.replace("_", " ")
    for name in _skill_names(profile):
        if token in name or name.replace(" ", "_") == slug:
            return True
    return False


def score_candidate(
    *,
    profile: WorkerProfileRecord,
    task_type_slug: str | None,
) -> tuple[float, str]:
    """Return (score 0–1, rationale). Deterministic — no Gemini yet."""
    slug = (task_type_slug or "").lower()
    type_fit = _task_type_proficiency(profile, slug) if slug else 0.4
    if type_fit == 0.0 and _matches_task(profile, slug):
        type_fit = 0.45

    stats = profile.stats if isinstance(profile.stats, dict) else {}
    tasks_completed = int(stats.get("tasks_completed") or 0)
    on_time = float(stats.get("on_time_pct") or 0)
    experience = min(tasks_completed / 30.0, 1.0) * 0.25
    reliability = min(on_time / 100.0, 1.0) * 0.2

    avail_bonus = 0.1 if profile.availability_status == "available" else 0.0
    completion_bonus = 0.05 if profile.profile_completion_pct >= 90 else 0.0

    score = min(1.0, round(0.4 * type_fit + experience + reliability + avail_bonus + completion_bonus, 4))
    if score < 0.35:
        score = max(score, 0.35)

    seller = str(stats.get("seller_level") or "new")
    rationale_bits = []
    if type_fit >= 0.75:
        rationale_bits.append(f"Strong {slug or 'task'} fit")
    elif type_fit > 0:
        rationale_bits.append(f"Matches {slug or 'task'}")
    if tasks_completed:
        rationale_bits.append(f"{tasks_completed} completed")
    if on_time:
        rationale_bits.append(f"{on_time:.0f}% on-time")
    if seller and seller != "new":
        rationale_bits.append(f"{seller} seller")
    rationale = ", ".join(rationale_bits) or "Eligible worker in matching pool"
    return score, rationale


def candidate_from_profile(
    *,
    user: User,
    profile: WorkerProfileRecord,
    score: float,
    rationale: str,
) -> dict[str, Any]:
    stats = profile.stats if isinstance(profile.stats, dict) else {}
    return {
        "worker_id": str(user.id),
        "full_name": user.full_name,
        "profile_photo_url": user.profile_photo_url,
        "headline": profile.headline or "",
        "community_type": profile.community_type,
        "score": score,
        "rationale": rationale,
        "availability": profile.availability_status,
        "seller_level": str(stats.get("seller_level") or "new"),
        "tasks_completed": int(stats.get("tasks_completed") or 0),
        "on_time_pct": float(stats.get("on_time_pct") or 0),
    }


async def match_candidates(
    session: AsyncSession,
    *,
    task: FulfillmentTask | None = None,
    task_id: uuid.UUID | None = None,
    task_type_slug: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Filter live worker_profiles and return ranked Candidate shapes.

    Empty pool → empty list (caller decides how to surface that).
    """
    slug = task_type_slug
    if task is not None:
        slug = task.task_type_slug or slug
    elif task_id is not None and slug is None:
        row = await session.get(FulfillmentTask, task_id)
        if row is not None:
            slug = row.task_type_slug

    result = await session.execute(
        select(User, WorkerProfileRecord)
        .join(WorkerProfileRecord, WorkerProfileRecord.user_id == User.id)
        .where(
            User.role == "worker",
            User.is_active.is_(True),
            WorkerProfileRecord.is_active.is_(True),
            WorkerProfileRecord.profile_completion_pct >= PROFILE_LIVE_THRESHOLD,
            WorkerProfileRecord.availability_status.in_(("available", "busy")),
        )
    )
    rows = list(result.all())

    scored: list[tuple[float, dict[str, Any]]] = []
    for user, profile in rows:
        if not _matches_task(profile, slug):
            continue
        score, rationale = score_candidate(profile=profile, task_type_slug=slug)
        scored.append(
            (
                score,
                candidate_from_profile(user=user, profile=profile, score=score, rationale=rationale),
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1]["full_name"]))
    return [c for _, c in scored[:limit]]
