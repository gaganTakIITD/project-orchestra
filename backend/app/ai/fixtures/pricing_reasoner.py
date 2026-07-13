"""Fixture Pricing Reasoner — explain quote drivers without Gemini."""

from __future__ import annotations

from typing import Any


def opening_pricing_message(quote: dict[str, Any]) -> str:
    price = quote.get("price")
    risk = quote.get("risk_tier") or "L1"
    sku = quote.get("sku_name") or quote.get("sku_slug") or "this package"
    rationale = quote.get("ai_rationale") or "Priced from the SKU base band for this scope."
    return (
        f"Here's your quote for {sku}: ₹{price:,.0f} at risk tier {risk}. "
        f"{rationale} "
        "Ask about price drivers, risk, or deadline — or say confirm when you're ready to accept."
    )


def explain_drivers(quote: dict[str, Any]) -> str:
    sku = quote.get("sku_name") or quote.get("sku_slug") or "the selected SKU"
    base = quote.get("sku_base_price")
    price = quote.get("price")
    tasks = quote.get("mapped_task_types") or []
    deliverables = quote.get("deliverable_count") or 0
    revisions = quote.get("revision_limit") or 0
    lines = [
        f"Price drivers for this quote (₹{price:,.0f}):",
        f"• SKU base: {sku}"
        + (f" (₹{float(base):,.0f})" if base is not None else ""),
        f"• Scope size: {deliverables} deliverable(s), {len(tasks)} mapped task type(s)",
        f"• Revision rounds included: {revisions}",
    ]
    if quote.get("ai_rationale"):
        lines.append(f"• Reasoner note: {quote['ai_rationale']}")
    return "\n".join(lines)


def explain_risk(quote: dict[str, Any]) -> str:
    risk = quote.get("risk_tier") or "L1"
    confidence = quote.get("ai_confidence")
    conf_txt = (
        f" AI confidence is {float(confidence) * 100:.0f}%."
        if confidence is not None
        else ""
    )
    tier_notes = {
        "L0": "L0 is low-risk / highly deterministic checks — pricing stays near the SKU base.",
        "L1": "L1 is standard delivery risk — fixed price with included revisions absorbs typical rework.",
        "L2": "L2 means higher ambiguity or judgment-heavy QA — contingency is already in the quote band.",
    }
    note = tier_notes.get(risk, f"Risk tier {risk} informs QA depth and contingency.")
    return f"Risk for this quote is {risk}. {note}{conf_txt}"


def explain_deadline(quote: dict[str, Any]) -> str:
    deadline = quote.get("deadline") or "the quoted deadline"
    typical = quote.get("sku_typical_days")
    extra = f" Typical SKU lead time is about {typical} days." if typical else ""
    return (
        f"The deadline is {deadline}.{extra} "
        "It's derived from the SKU typical_days band for this package, not a custom bid."
    )
