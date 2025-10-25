FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and install dependencies
COPY pyproject.toml requirements.txt ./
RUN uv pip install --no-cache -r requirements.txt

# Copy application files
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY app ./app
COPY start.sh ./start.sh
COPY .env ./.env

RUN chmod +x /app/start.sh

EXPOSE 8000

ENTRYPOINT ["/app/start.sh"]
