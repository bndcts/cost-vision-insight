from fastapi import APIRouter

from app.api.routes import articles, cost_models, estimates, health, indices, orders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(articles.router)
api_router.include_router(indices.router)
api_router.include_router(cost_models.router)
api_router.include_router(orders.router)
api_router.include_router(estimates.router)
