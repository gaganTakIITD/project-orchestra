"""Transactional email via Resend — no-op when RESEND_API_KEY unset."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.api_key = settings.resend_api_key
        self.from_addr = settings.email_from or "Orchestra <noreply@orchestra.local>"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            logger.info(
                "EmailService no-op (RESEND_API_KEY unset): to=%s subject=%s",
                to,
                subject,
            )
            return {"ok": True, "stub": True, "to": to, "subject": subject}

        payload: dict[str, Any] = {
            "from": self.from_addr,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if tags:
            payload["tags"] = [{"name": t, "value": "1"} for t in tags]

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            res.raise_for_status()
            data = res.json()
            return {"ok": True, "stub": False, "id": data.get("id"), "to": to}

    async def send_invite(self, *, to: str, task_title: str) -> dict[str, Any]:
        return await self.send(
            to=to,
            subject=f"You're invited: {task_title}",
            html=f"<p>You have a new task invite: <strong>{task_title}</strong>.</p>",
            tags=["invite"],
        )

    async def send_qa_fail(self, *, to: str, task_title: str, feedback: str) -> dict[str, Any]:
        return await self.send(
            to=to,
            subject=f"QA needs rework: {task_title}",
            html=f"<p>QA feedback on <strong>{task_title}</strong>:</p><p>{feedback}</p>",
            tags=["qa_fail"],
        )

    async def send_delivery(self, *, to: str, order_id: str) -> dict[str, Any]:
        return await self.send(
            to=to,
            subject="Your outcome is ready",
            html=f"<p>Delivery is ready for order <code>{order_id}</code>.</p>",
            tags=["delivery"],
        )
