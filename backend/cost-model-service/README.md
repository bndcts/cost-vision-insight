# Cost Model Service

Backend API service for cost modeling and estimation.

## Tech Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **uv** - Fast Python package manager

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Install Dependencies

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
CMS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model
CMS_OPENAI_API_KEY=your-api-key-here
CMS_OPENAI_MODEL=gpt-4o-mini
```

### Database Setup

```bash
# Run migrations
alembic upgrade head
```

### TAC Index Data

- Place `indices.csv` in `backend/indices.csv` (already git-ignored).  
- `docker-compose.yml` mounts the CSV into the backend container at `/app/data/indices.csv` and `start.sh` automatically runs `python -m app.scripts.load_indices_from_csv --file /app/data/indices.csv` on every container startup, so the indices table is refreshed without manual steps.
- Supported mass units (`t`, `kg`, `g`) are converted to a normalized `value_per_gram`. Other units (e.g., `MWh`, `h`) are stored as-is with `value_per_gram = null`.

Manual reload command (if you change the CSV while the container is running):

```bash
docker-compose run --rm \
  --entrypoint python \
  cost-model-service \
  -m app.scripts.load_indices_from_csv --file /app/data/indices.csv
```

### Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Development

### Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or just the cost-model-service
docker-compose up --build cost-model-service

# View logs
docker-compose logs -f cost-model-service

# Stop services
docker-compose down

# Clean everything (including volumes)
docker-compose down -v
```

### Verify Database Schema

```bash
# Connect to database
docker-compose exec cost-model-db psql -U postgres -d cost_model

# List tables
\dt

# Exit
\q
```

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
cost-model-service/
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── app/
│   ├── api/             # API routes
│   │   └── routes/      # Endpoint definitions
│   ├── core/            # Core configuration
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Modern Python project config
└── start.sh            # Container startup script
```

## Database Models

- **Articles** - Product/article definitions
- **Indices** - Price indices for cost modeling
- **Cost Models** - Article-to-index relationships
- **Orders** - Historical order data

## Adding Dependencies

```bash
# Add a new dependency
uv pip install package-name

# Freeze dependencies
uv pip freeze > requirements.txt

# Or update pyproject.toml and sync
uv pip sync pyproject.toml
```

## Running Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check `CMS_DATABASE_URL` environment variable
- The start.sh script includes retry logic for database connectivity

### Migration Failures

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Reset database (WARNING: destroys data)
docker-compose down -v
docker-compose up --build
```
