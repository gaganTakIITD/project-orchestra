"""Order delivery bundle + client accept."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import (
    DeliveryBundleRecord,
    FulfillmentTask,
    OutcomeOrder,
    SubmissionRecord,
)
from app.orchestrator.spine import OrderSpine
from app.orchestrator.states import ActorType, OrderStatus, TaskStatus


class DeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_bundle(self, order_id: uuid.UUID) -> DeliveryBundleRecord | None:
        return await self.session.scalar(
            select(DeliveryBundleRecord).where(DeliveryBundleRecord.order_id == order_id)
        )

    async def get_or_build_bundle(self, order: OutcomeOrder) -> DeliveryBundleRecord:
        existing = await self.get_bundle(order.id)
        if existing is not None:
            return existing

        assets = await self._assets_from_submissions(order.id)
        if not assets:
            raise LookupError("No submissions yet — delivery bundle not ready")

        bundle = DeliveryBundleRecord(
            order_id=order.id,
            assets=assets,
            qa_summary="Acceptance criteria reviewed. Bundle ready for client accept.",
            delivered_at=datetime.now(timezone.utc),
        )
        self.session.add(bundle)
        await self.session.flush()
        return bundle

    async def ensure_delivered(self, order: OutcomeOrder) -> OutcomeOrder:
        """Advance order to delivered when all tasks are completed."""
        if order.status in (OrderStatus.DELIVERED, OrderStatus.CLOSED):
            return order

        tasks = list(
            (
                await self.session.execute(
                    select(FulfillmentTask).where(FulfillmentTask.order_id == order.id)
                )
            ).scalars()
        )
        if not tasks or not all(t.status == TaskStatus.COMPLETED for t in tasks):
            raise ValueError("Delivery not ready — not all tasks completed")

        spine = OrderSpine(self.session)

        if order.status == OrderStatus.CONFIRMED:
            await spine.transition(
                order,
                "plan_and_preferences_set",
                actor_type=ActorType.SYSTEM,
                payload={"source": "delivery_bootstrap"},
            )

        if order.status == OrderStatus.ASSEMBLING_TEAM:
            await spine.transition(
                order,
                "first_mutual_start",
                actor_type=ActorType.SYSTEM,
                payload={"source": "delivery_bootstrap"},
            )

        if order.status == OrderStatus.DELIVERY_ACTIVE:
            await spine.transition(
                order,
                "all_tasks_submitted",
                actor_type=ActorType.SYSTEM,
                payload={"task_count": len(tasks)},
            )

        if order.status == OrderStatus.UNDER_QUALITY_CHECK:
            await self.get_or_build_bundle(order)
            await spine.transition(
                order,
                "bundle_ready",
                actor_type=ActorType.SYSTEM,
                payload={"source": "stage_b_stub_qa"},
            )
            order.progress_pct = 100

        if order.status != OrderStatus.DELIVERED:
            raise ValueError(f"Cannot mark delivered from {order.status!r}")

        await self.get_or_build_bundle(order)
        await self.session.flush()
        return order

    async def accept_delivery(
        self, *, order: OutcomeOrder, client_id: uuid.UUID
    ) -> tuple[OutcomeOrder, DeliveryBundleRecord]:
        await self.ensure_delivered(order)

        if order.status != OrderStatus.DELIVERED:
            raise ValueError(f"Cannot accept delivery when order is {order.status!r}")

        spine = OrderSpine(self.session)
        await spine.transition(
            order,
            "client_accept",
            actor_id=client_id,
            actor_type=ActorType.CLIENT,
        )

        bundle = await self.get_or_build_bundle(order)
        bundle.accepted_at = datetime.now(timezone.utc)
        bundle.accepted_by = client_id
        order.progress_pct = 100

        # RAG ingest on OutcomeClosed (Sprint 8).
        try:
            from app.services.rag import RagService

            await RagService(self.session).ingest_from_order(order)
        except Exception:  # noqa: BLE001 — never block accept on RAG
            pass

        await self.session.flush()
        return order, bundle

    async def _latest_submissions(self, order_id: uuid.UUID) -> list[SubmissionRecord]:
        task_ids = (
            await self.session.execute(
                select(FulfillmentTask.id).where(FulfillmentTask.order_id == order_id)
            )
        ).scalars().all()
        if not task_ids:
            return []

        result = await self.session.execute(
            select(SubmissionRecord)
            .where(SubmissionRecord.task_id.in_(list(task_ids)))
            .order_by(SubmissionRecord.submitted_at.desc())
        )
        seen: set[uuid.UUID] = set()
        latest: list[SubmissionRecord] = []
        for sub in result.scalars().all():
            if sub.task_id in seen:
                continue
            seen.add(sub.task_id)
            latest.append(sub)
        return latest

    async def _assets_from_submissions(self, order_id: uuid.UUID) -> list[dict]:
        submissions = await self._latest_submissions(order_id)
        assets: list[dict] = []
        for sub in submissions:
            for i, url in enumerate(sub.asset_urls or []):
                assets.append(
                    {
                        "name": f"Submission v{sub.version} asset {i + 1}",
                        "url": url,
                        "type": _guess_asset_type(url),
                    }
                )
            if sub.notes and not (sub.asset_urls or []):
                assets.append(
                    {
                        "name": f"Notes v{sub.version}",
                        "url": f"notes://task/{sub.task_id}",
                        "type": "text/plain",
                    }
                )
        return assets


def _guess_asset_type(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".svg"):
        return "image/svg+xml"
    if path.endswith(".pdf"):
        return "application/pdf"
    if path.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    if "figma.com" in url:
        return "figma"
    return "url"
