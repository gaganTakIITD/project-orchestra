from fastapi import APIRouter

from app.api.v1 import (
    admin,
    amendments,
    auth,
    catalog,
    chat,
    health,
    intents,
    knowledge,
    media,
    notifications,
    orders,
    orchestrator,
    quotes,
    specs,
    tasks,
    taxonomy,
    timers,
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
api_router.include_router(amendments.router)
api_router.include_router(tasks.router)
api_router.include_router(workers.router)
api_router.include_router(media.router)
# Track A — Live Spine WebSocket
api_router.include_router(ws.router)
# Track E — in-app notifications (event-projected)
api_router.include_router(notifications.router)
# Durable priority timers (Cloud Scheduler → POST /internal/timers/tick)
api_router.include_router(timers.router)
# Vertex AI Agent Builder (Discovery Engine) grounded knowledge Q&A
api_router.include_router(knowledge.router)
# PM control loop (timers + allowlisted auto promote_backup)
api_router.include_router(orchestrator.router)
# Track D — admin console (verify, taxonomy, AI quality, disputes)
api_router.include_router(admin.router)
