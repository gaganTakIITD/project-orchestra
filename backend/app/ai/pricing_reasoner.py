"""Pricing Reasoner chat — explain quote SKU drivers / risk; finalize → accept_quote.

Fixture-first (no Gemini yet). AI proposes replies + ready_to_confirm;
Spine accepts the quote only on finalize.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ai.fixtures.pricing_reasoner import (
    explain_deadline,
    explain_drivers,
    explain_risk,
    opening_pricing_message as opening_pricing_message,
)


@dataclass
class PricingTurn:
    """Proposal for one pricing-confirm turn — not persisted state."""

    reply: str
    ready_to_confirm: bool
    version: int
    quote_id: str
    source: str = "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float = 0.9
    error: str | None = None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def compile_pricing_turn(
    *,
    quote: dict[str, Any],
    user_message: str,
    version: int,
) -> PricingTurn:
    """Rule-based Pricing Reasoner turn over an issued quote snapshot."""
    text = _normalize(user_message)
    quote_id = str(quote.get("quote_id") or "")
    next_version = version + 1
    ready = True  # issued quote is always accept-ready once client confirms

    if re.search(r"\b(confirm|accept|finalize|lock in|looks good|agree|proceed)\b", text):
        reply = (
            "Great — you're ready to accept this quote. "
            "Hit Confirm & begin (or finalize this chat) and we'll create your order."
        )
        return PricingTurn(
            reply=reply,
            ready_to_confirm=True,
            version=next_version,
            quote_id=quote_id,
        )

    if re.search(r"\b(risk|tier|confidence|rework)\b", text):
        return PricingTurn(
            reply=explain_risk(quote),
            ready_to_confirm=ready,
            version=version,
            quote_id=quote_id,
        )

    if re.search(r"\b(deadline|timeline|how long|days|when)\b", text):
        return PricingTurn(
            reply=explain_deadline(quote),
            ready_to_confirm=ready,
            version=version,
            quote_id=quote_id,
        )

    if re.search(r"\b(why|price|pricing|cost|driver|sku|expensive|cheap|breakdown)\b", text):
        return PricingTurn(
            reply=explain_drivers(quote),
            ready_to_confirm=ready,
            version=version,
            quote_id=quote_id,
        )

    # Default — summarize quote
    price = quote.get("price")
    risk = quote.get("risk_tier") or "L1"
    sku = quote.get("sku_name") or quote.get("sku_slug") or "package"
    reply = (
        f"Quote summary: ₹{float(price):,.0f} for {sku}, risk {risk}. "
        "Ask about drivers, risk, or deadline — or say confirm when you're ready to accept."
    )
    return PricingTurn(
        reply=reply,
        ready_to_confirm=ready,
        version=version,
        quote_id=quote_id,
    )
