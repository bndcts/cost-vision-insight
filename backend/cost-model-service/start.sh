#!/bin/sh
set -e

export PYTHONPATH="/app"

echo "Starting Cost Model Service..."

# Function to wait for database
wait_for_db() {
    echo "Waiting for PostgreSQL to be ready..."
    max_retries=30
    retry_count=0
    
    until python -c "
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def check_db():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        await engine.dispose()
        return True
    except Exception as e:
        print(f'Database not ready: {e}', file=sys.stderr)
        await engine.dispose()
        return False

sys.exit(0 if asyncio.run(check_db()) else 1)
" 2>/dev/null; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            echo "Error: Database is not available after $max_retries attempts"
            exit 1
        fi
        echo "Database not ready yet... (attempt $retry_count/$max_retries)"
        sleep 2
    done
    
    echo "PostgreSQL is ready!"
}

# Wait for database to be ready
wait_for_db

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Error: Database migrations failed"
    exit 1
fi

echo "Database migrations completed successfully"

INDEX_CSV_PATH="${CMS_INDEX_CSV_PATH:-/app/data/indices.csv}"
if [ -f "$INDEX_CSV_PATH" ]; then
    echo "Loading index data from $INDEX_CSV_PATH..."
    if ! python -m app.scripts.load_indices_from_csv --file "$INDEX_CSV_PATH"; then
        echo "Error: Failed to load index data"
        exit 1
    fi
else
    echo "Error: Index CSV not found at $INDEX_CSV_PATH"
    exit 1
fi

# Start the application
echo "Starting uvicorn server..."
if [ "$CMS_ENV" = "development" ]; then
    echo "Running in development mode with hot-reload enabled"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Running in production mode"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
