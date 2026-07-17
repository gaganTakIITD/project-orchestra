"""Matcher Preference Chat — rule-based turns over Candidate shortlist.

AI proposes ranking explanations / reorders; Spine persists PreferenceSet on finalize.
Deterministic (no Gemini yet) — uses existing match_candidates scores + rationales.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


MIN_RANKED = 3


def required_ranked_count(candidate_count: int) -> int:
    """Pilot-friendly floor: need min(3, pool) ranked workers, at least 1 when pool > 0."""
    if candidate_count <= 0:
        return 1
    return max(1, min(MIN_RANKED, candidate_count))


@dataclass
class MatcherTurn:
    """Proposal for one preference-chat turn — not persisted state."""

    candidates: list[dict[str, Any]]
    reply: str
    ready_to_confirm: bool
    version: int
    source: str = "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float = 0.9
    error: str | None = None


def opening_matcher_message(candidates: list[dict[str, Any]], *, task_title: str | None = None) -> str:
    n = len(candidates)
    if n == 0:
        return (
            "I couldn't find live workers for this task yet. "
            "Check back once more talent has completed onboarding."
        )
    top = candidates[0]
    label = f" for {task_title}" if task_title else ""
    names = ", ".join(c["full_name"] for c in candidates[:3])
    extra = f" (+{n - 3} more)" if n > 3 else ""
    return (
        f"I found {n} strong match{'es' if n != 1 else ''}{label}. "
        f"Top picks: {names}{extra}. "
        f"{top['full_name']} leads (score {top['score']:.2f}) — {top['rationale']}. "
        "Ask me why someone ranks where they do, or say things like "
        '"move Meera to #1" or "confirm these three."'
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_candidate(candidates: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
    n = _normalize(needle)
    if not n:
        return None
    # Exact / substring on full_name
    for c in candidates:
        name = _normalize(c.get("full_name") or "")
        if n == name or n in name or name in n:
            return c
    # First name token
    for c in candidates:
        first = _normalize((c.get("full_name") or "").split()[0] if c.get("full_name") else "")
        if first and (n == first or first in n or n in first):
            return c
    # Rank ordinal: "#1", "number 1", "rank 2"
    m = re.search(r"(?:#|number|rank|no\.?)\s*(\d+)", n)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    return None


def _move_to_rank(
    candidates: list[dict[str, Any]], worker_id: str, new_rank: int
) -> list[dict[str, Any]]:
    """1-based new_rank; clamps to list bounds."""
    ordered = list(candidates)
    idx = next((i for i, c in enumerate(ordered) if c["worker_id"] == worker_id), None)
    if idx is None:
        return ordered
    item = ordered.pop(idx)
    target = max(0, min(new_rank - 1, len(ordered)))
    ordered.insert(target, item)
    return ordered


def _swap(candidates: list[dict[str, Any]], a_id: str, b_id: str) -> list[dict[str, Any]]:
    ordered = list(candidates)
    i = next((j for j, c in enumerate(ordered) if c["worker_id"] == a_id), None)
    k = next((j for j, c in enumerate(ordered) if c["worker_id"] == b_id), None)
    if i is None or k is None:
        return ordered
    ordered[i], ordered[k] = ordered[k], ordered[i]
    return ordered


def _ranking_summary(candidates: list[dict[str, Any]], *, limit: int = 5) -> str:
    lines = []
    for i, c in enumerate(candidates[:limit], start=1):
        lines.append(f"{i}. {c['full_name']} ({c['score']:.2f}) — {c['rationale']}")
    if len(candidates) > limit:
        lines.append(f"…and {len(candidates) - limit} more.")
    return "\n".join(lines)


def compile_matcher_turn(
    *,
    candidates: list[dict[str, Any]],
    user_message: str,
    version: int,
) -> MatcherTurn:
    """Rule-based Matcher turn: explain, reorder, or confirm readiness."""
    text = _normalize(user_message)
    ordered = list(candidates)
    next_version = version + 1
    min_needed = required_ranked_count(len(ordered))
    ready = len(ordered) >= min_needed

    # Confirm intent
    if re.search(r"\b(confirm|finalize|lock in|looks good|these (?:3|three)|submit)\b", text):
        if len(ordered) < min_needed:
            reply = (
                f"I only have {len(ordered)} candidate(s) ranked — need at least {min_needed} "
                "before we can confirm. Ask me to explain the shortlist or wait for more matches."
            )
            return MatcherTurn(
                candidates=ordered,
                reply=reply,
                ready_to_confirm=False,
                version=version,
            )
        reply = (
            f"Great — ranking locked for confirm:\n{_ranking_summary(ordered, limit=min_needed)}\n\n"
            "Hit Confirm ranking when you're ready and I'll submit your PreferenceSet."
        )
        return MatcherTurn(
            candidates=ordered,
            reply=reply,
            ready_to_confirm=True,
            version=next_version,
        )

    # Why / explain
    if re.search(r"\b(why|explain|rationale|how come|tell me about)\b", text):
        target = _find_candidate(ordered, text)
        if target is None and ordered:
            target = ordered[0]
        if target is None:
            reply = "There's no shortlist yet to explain."
        else:
            rank = next(i for i, c in enumerate(ordered) if c["worker_id"] == target["worker_id"]) + 1
            reply = (
                f"{target['full_name']} is #{rank} (score {target['score']:.2f}). "
                f"{target['rationale']}. "
                f"{target['tasks_completed']} tasks completed, {target['on_time_pct']:.0f}% on-time, "
                f"{target['seller_level']} seller, currently {target['availability']}."
            )
        return MatcherTurn(
            candidates=ordered,
            reply=reply,
            ready_to_confirm=ready,
            version=version,
        )

    # Move X to #N / make X first / rank X higher
    move_match = re.search(
        r"(?:move|put|rank|place)\s+(.+?)\s+(?:to\s+)?(?:#|number|rank\s*)?(\d+|first|top|second|third)",
        text,
    )
    make_first = re.search(r"(?:make|set)\s+(.+?)\s+(?:#?1|first|top|number one)", text)
    if move_match or make_first:
        if move_match:
            name_part = move_match.group(1).strip()
            rank_token = move_match.group(2)
        else:
            assert make_first is not None
            name_part = make_first.group(1).strip()
            rank_token = "1"
        rank_map = {"first": 1, "top": 1, "second": 2, "third": 3}
        new_rank = rank_map.get(rank_token, int(rank_token) if rank_token.isdigit() else 1)
        target = _find_candidate(ordered, name_part)
        if target is None:
            reply = (
                f"I couldn't find anyone matching “{name_part}” in the shortlist. "
                f"Current ranking:\n{_ranking_summary(ordered)}"
            )
            return MatcherTurn(
                candidates=ordered,
                reply=reply,
                ready_to_confirm=ready,
                version=version,
            )
        ordered = _move_to_rank(ordered, target["worker_id"], new_rank)
        reply = (
            f"Updated — {target['full_name']} is now #{new_rank}.\n{_ranking_summary(ordered)}\n\n"
            + (
                "You have enough for a PreferenceSet. Say confirm when ready."
                if len(ordered) >= min_needed
                else f"Need {min_needed - len(ordered)} more before confirm."
            )
        )
        return MatcherTurn(
            candidates=ordered,
            reply=reply,
            ready_to_confirm=len(ordered) >= min_needed,
            version=next_version,
        )

    # Swap A and B
    swap_match = re.search(r"swap\s+(.+?)\s+(?:and|with)\s+(.+)", text)
    if swap_match:
        a = _find_candidate(ordered, swap_match.group(1))
        b = _find_candidate(ordered, swap_match.group(2))
        if a and b:
            ordered = _swap(ordered, a["worker_id"], b["worker_id"])
            reply = f"Swapped {a['full_name']} and {b['full_name']}.\n{_ranking_summary(ordered)}"
            return MatcherTurn(
                candidates=ordered,
                reply=reply,
                ready_to_confirm=len(ordered) >= min_needed,
                version=next_version,
            )

    # Default — summarize shortlist
    if not ordered:
        reply = "No candidates in the shortlist yet."
        return MatcherTurn(
            candidates=ordered,
            reply=reply,
            ready_to_confirm=False,
            version=version,
        )

    reply = (
        f"Here's the current Matcher shortlist:\n{_ranking_summary(ordered)}\n\n"
        "Ask why someone is ranked where they are, reorder with "
        '"move Name to #1", or say confirm when the top 3 look right.'
    )
    return MatcherTurn(
        candidates=ordered,
        reply=reply,
        ready_to_confirm=ready,
        version=version,
    )
