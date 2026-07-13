from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    catalog,
    chat,
    health,
    intents,
    notifications,
    orders,
    quotes,
    specs,
    tasks,
    taxonomy,
    workers,
    ws,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(catalog.router)
api_router.include_router(taxonomy.router)
api_router.include_router(intents.router)
api_router.include_router(quotes.router)
api_router.include_router(specs.router)
api_router.include_router(orders.router)
api_router.include_router(tasks.router)
api_router.include_router(workers.router)
# Track A — Live Spine WebSocket
api_router.include_router(ws.router)
# Track E — notifications stub
api_router.include_router(notifications.router)
# Track D — read-only admin console
api_router.include_router(admin.router)
