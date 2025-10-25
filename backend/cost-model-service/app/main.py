from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import get_settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()


settings = get_settings()

app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)
