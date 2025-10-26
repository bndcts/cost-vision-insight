from fastapi import APIRouter

from app.api.routes import analyze, articles, cost_models, health, indices, orders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analyze.router)
api_router.include_router(articles.router)
api_router.include_router(indices.router)
api_router.include_router(cost_models.router)
api_router.include_router(orders.router)
