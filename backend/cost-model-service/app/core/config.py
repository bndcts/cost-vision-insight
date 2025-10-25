from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")
    project_name: str = Field(default="cost-model-service")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/cost_model"
    )
    openai_api_key: str | None = None
    openai_model: str = Field(default="gpt-4o-mini")
    index_csv_path: str = Field(default="/app/data/indices.csv")
    env: str = Field(default="development")

    class Config:
        # Don't require .env file - read from environment variables passed by Docker
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "CMS_"
        # Allow .env file to be missing
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
