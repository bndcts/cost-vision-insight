# Cost Model Service - Backend API

> FastAPI backend for AI-powered cost modeling and estimation

## Overview

RESTful API built with FastAPI that provides cost estimation, document processing, and semantic search capabilities using OpenAI GPT-4 and Weaviate vector database.

## Tech Stack

- **FastAPI 0.110.0** - Web framework
- **PostgreSQL 15** + **SQLAlchemy 2.0** - Database & ORM
- **Alembic 1.13.1** - Database migrations
- **OpenAI 2.6.1** - GPT-4 integration
- **Weaviate 4.17.0** - Vector database for RAG
- **Uvicorn 0.29.0** - ASGI server

## Quick Start

### Docker (Recommended)

```bash
docker-compose up --build cost-model-service
```

### Local Development

```bash
cd backend/cost-model-service

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CMS_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model"
export CMS_OPENAI_API_KEY="sk-proj-your-key"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

```http
GET /api/v1/health
```

### Articles

```http
POST   /api/v1/articles                  # Create (supports file upload)
GET    /api/v1/articles                  # List all
GET    /api/v1/articles/{id}             # Get by ID
PATCH  /api/v1/articles/{id}             # Update
DELETE /api/v1/articles/{id}             # Delete
GET    /api/v1/articles/{id}/similar     # Find similar (RAG)
```

### Cost Estimation

```http
POST /api/v1/estimates
Content-Type: application/json

{
  "article_id": "uuid",
  "quantity": 100,
  "target_date": "2024-03-15"
}
```

### Price Indices

```http
GET  /api/v1/indices              # List all
POST /api/v1/indices              # Create
GET  /api/v1/indices/{id}         # Get by ID
GET  /api/v1/indices/by-name/{name}  # Get by name
```

### Cost Models

```http
GET  /api/v1/cost-models                    # List all
POST /api/v1/cost-models                    # Create
GET  /api/v1/cost-models/article/{id}       # Get by article
```

### Orders

```http
GET  /api/v1/orders               # List all
POST /api/v1/orders               # Create
GET  /api/v1/orders/{id}          # Get by ID
```

## Database Schema

### Main Tables

**articles** - Product information
- `id` (UUID), `name`, `description`, `weight_grams`, `materials` (JSON), `processes` (JSON)
- `file_path`, `file_name`, `processing_status`, `extracted_text`, `direct_cost_eur`

**indices** - Price index data
- `id` (UUID), `name`, `date`, `value`, `unit`, `value_per_gram`, `category`

**cost_models** - Article-to-index relationships
- `id` (UUID), `article_id` (FK), `index_id` (FK), `weight`, `description`

**orders** - Historical order data
- `id` (UUID), `article_name`, `quantity`, `unit_price`, `total_price`, `order_date`, `supplier`

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

## Services

### OpenAI Client
Handles GPT-4 integration for text analysis and specification extraction.

### Article Processor
Processes uploaded documents (PDF/text), extracts specifications using OpenAI, updates articles asynchronously.

### Weaviate Service
Manages vector embeddings and semantic similarity search for finding related articles.

### Cost Model Builder
Builds and manages cost models linking articles to price indices.

## Development

### Project Structure

```
cost-model-service/
├── alembic/              # Database migrations
├── app/
│   ├── api/
│   │   └── routes/      # API endpoints
│   ├── core/
│   │   └── config.py    # Settings
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── scripts/         # Utility scripts
│   └── main.py          # FastAPI app
├── requirements.txt
└── Dockerfile
```

### Adding New Endpoint

1. Create route in `app/api/routes/`
2. Register in `app/api/routes/__init__.py`
3. Test at http://localhost:8000/docs

### Adding New Model

1. Create model in `app/models/`
2. Import in `app/db/base.py`
3. Create Pydantic schema in `app/schemas/`
4. Generate migration: `alembic revision --autogenerate -m "message"`
5. Apply: `alembic upgrade head`

### Configuration

Settings are managed via Pydantic in `app/core/config.py`. All settings use `CMS_` prefix for environment variables.

### Loading Data

```bash
# Load price indices
docker-compose exec cost-model-service \
  python -m app.scripts.load_indices_from_csv --file /app/data/indices.csv

# Load orders
docker-compose exec cost-model-service \
  python -m app.scripts.load_orders_from_csv --file /app/data/synthetic_orders.csv
```

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Manual API testing
curl -X POST http://localhost:8000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product"}'
```

## Production

```dockerfile
# Use Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

**Environment:**
- Use secrets management (not .env files)
- Set `CMS_ENV=production`
- Use managed PostgreSQL
- Implement monitoring and logging

## Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/
- **OpenAI API**: https://platform.openai.com/docs/

---

See [main README](../../README.md) for full project documentation.
