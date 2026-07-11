from fastapi import APIRouter

from app.api.v1 import auth, catalog, health, intents, orders, quotes, taxonomy

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(taxonomy.router)
api_router.include_router(intents.router)
api_router.include_router(quotes.router)
api_router.include_router(orders.router)
