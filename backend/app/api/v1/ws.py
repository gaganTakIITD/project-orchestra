"""WebSocket live channels — order:{id} and task:{id} via in-process EventBus."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import User
from app.orchestrator.event_bus import get_event_bus
from app.services.auth import resolve_user

router = APIRouter(tags=["ws"])


class _QueryAuthRequest:
    """Shim so resolve_user can read ?token= and ?role= from a WebSocket."""

    def __init__(self, websocket: WebSocket) -> None:
        token = websocket.query_params.get("token")
        role = websocket.query_params.get("role")
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if role:
            headers["X-Orchestra-Role"] = role
        self.headers = headers


async def _resolve_ws_user(
    websocket: WebSocket,
    session: AsyncSession,
    *,
    prefer_role: str,
) -> User:
    role = websocket.query_params.get("role") or prefer_role
    if role not in ("client", "worker"):
        role = prefer_role
    # Demo mode: allow connect without token (resolve_user ignores token).
    if settings.auth_mode == "clerk" and not websocket.query_params.get("token"):
        raise HTTPException(status_code=401, detail="token query param required")
    return await resolve_user(session, _QueryAuthRequest(websocket), prefer_role=role)


async def _authorize_order(session: AsyncSession, user: User, order_id: uuid.UUID) -> OutcomeOrder:
    order = await session.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if settings.auth_mode == "demo":
        return order
    if user.role == "client" and order.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this order")
    return order


async def _authorize_task(session: AsyncSession, user: User, task_id: uuid.UUID) -> FulfillmentTask:
    task = await session.get(FulfillmentTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if settings.auth_mode == "demo":
        return task
    order = await session.get(OutcomeOrder, task.order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role == "client" and order.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this task")
    if (
        user.role == "worker"
        and task.assigned_worker_id is not None
        and task.assigned_worker_id != user.id
    ):
        raise HTTPException(status_code=403, detail="Not allowed for this task")
    return task


async def _pump_channel(websocket: WebSocket, channel: str) -> None:
    bus = get_event_bus()
    queue = bus.add_subscriber(channel)
    await websocket.accept()
    try:
        while True:
            next_event = asyncio.create_task(queue.get())
            next_client = asyncio.create_task(websocket.receive())
            done, pending = await asyncio.wait(
                {next_event, next_client},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            if next_client in done:
                break
            await websocket.send_json(next_event.result())
    except WebSocketDisconnect:
        pass
    finally:
        bus.remove_subscriber(channel, queue)


@router.websocket("/ws/orders/{order_id}")
async def ws_order(websocket: WebSocket, order_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        try:
            user = await _resolve_ws_user(websocket, session, prefer_role="client")
            await _authorize_order(session, user, order_id)
        except HTTPException as exc:
            await websocket.close(code=4400 + (exc.status_code % 100))
            return

    await _pump_channel(websocket, f"order:{order_id}")


@router.websocket("/ws/tasks/{task_id}")
async def ws_task(websocket: WebSocket, task_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        try:
            user = await _resolve_ws_user(websocket, session, prefer_role="worker")
            await _authorize_task(session, user, task_id)
        except HTTPException as exc:
            await websocket.close(code=4400 + (exc.status_code % 100))
            return

    await _pump_channel(websocket, f"task:{task_id}")
