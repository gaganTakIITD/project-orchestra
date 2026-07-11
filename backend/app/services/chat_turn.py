"""Shared turn result for sync and streaming chat paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ai.gateway import SpecTurn


@dataclass
class TurnResult:
    draft: dict[str, Any]
    assistant_body: str
    completeness_pct: int
    missing_fields: list[str]
    ready_for_quote: bool
    turn: SpecTurn
