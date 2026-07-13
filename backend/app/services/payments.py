"""Razorpay adapter stub — gated by PAYMENTS_ENABLED."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class RazorpayAdapter:
    """Create payment order stub when enabled + keys set; else no-op success."""

    def create_order(
        self,
        *,
        order_id: uuid.UUID,
        amount: float,
        currency: str = "INR",
    ) -> dict[str, Any]:
        if not settings.payments_enabled:
            logger.info("Razorpay no-op (PAYMENTS_ENABLED=false) order=%s", order_id)
            return {
                "ok": True,
                "stub": True,
                "provider": "none",
                "orchestra_order_id": str(order_id),
                "amount": amount,
            }

        if not (settings.razorpay_key_id and settings.razorpay_key_secret):
            logger.info("Razorpay no-op (keys unset) order=%s", order_id)
            return {
                "ok": True,
                "stub": True,
                "provider": "razorpay_missing_keys",
                "orchestra_order_id": str(order_id),
                "amount": amount,
            }

        # Stub create — real SDK call deferred until harden is green.
        rz_id = f"order_stub_{uuid.uuid4().hex[:12]}"
        logger.info("Razorpay stub order created %s for %s", rz_id, order_id)
        return {
            "ok": True,
            "stub": True,
            "provider": "razorpay",
            "razorpay_order_id": rz_id,
            "orchestra_order_id": str(order_id),
            "amount": amount,
            "currency": currency,
            "key_id": settings.razorpay_key_id,
        }
