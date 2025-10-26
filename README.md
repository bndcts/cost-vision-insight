# Cost Vision Insight

> AI-powered cost modeling and estimation platform for manufacturing and procurement

## Overview

**Cost Vision Insight** combines historical order data, price indices, and AI-powered analysis to provide accurate product cost estimates. The platform features document processing, semantic search for similar products, and detailed cost breakdowns.

### Key Features

- **Document Processing**: Upload PDF/text specifications for AI analysis
- **AI Cost Estimation**: GPT-4 powered cost breakdowns
- **Semantic Search**: Find similar products using vector embeddings (Weaviate)
- **Price Index Tracking**: Monitor cost trends over time
- **Cost Modeling**: Link articles to price indices with configurable weights

## Tech Stack

**Backend**: FastAPI 0.110.0 • PostgreSQL 15 • SQLAlchemy 2.0 • OpenAI API • Weaviate 4.17.0

**Frontend**: React 18.3 • TypeScript 5.8 • Vite 5.4 • Tailwind CSS • shadcn/ui • React Query

**Infrastructure**: Docker & Docker Compose

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose (recommended)
- OpenAI API key

### 2. Setup

```bash
# Clone repository
git clone <repository-url>
cd cost-vision-insight

# Create .env file
cp ENV_TEMPLATE .env

# Edit .env and add your OpenAI API key:
# CMS_OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
```

### 3. Start Services

```bash
docker-compose up --build
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Verify

```bash
# Check health
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f
```

## Development

### Recommended Setup

```bash
# Backend in Docker
docker-compose up -d cost-model-service

# Frontend local (instant hot-reload)
cd frontend
pnpm install
pnpm dev
```

### Common Commands

```bash
# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Rebuild after changes
docker-compose up --build [service-name]

# Clean reset (removes all data!)
docker-compose down -v

# Database access
docker-compose exec cost-model-db psql -U postgres -d cost_model

# Backend shell
docker-compose exec cost-model-service /bin/bash
```

### Database Migrations

```bash
# Create migration
cd backend/cost-model-service
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

Full documentation: http://localhost:8000/docs

**Core Endpoints:**
- `GET /api/v1/health` - Health check
- `POST/GET /api/v1/articles` - Article management
- `POST /api/v1/estimates` - Generate cost estimates
- `GET /api/v1/indices` - Price indices
- `GET /api/v1/cost-models` - Cost models
- `GET /api/v1/orders` - Historical orders
- `GET /api/v1/articles/{id}/similar` - Find similar articles (RAG)

## Project Structure

```
cost-vision-insight/
├── backend/
│   ├── indices.csv                      # Price index data
│   └── cost-model-service/
│       ├── alembic/                     # Database migrations
│       ├── app/
│       │   ├── api/routes/              # API endpoints
│       │   ├── models/                  # SQLAlchemy models
│       │   ├── schemas/                 # Pydantic schemas
│       │   ├── services/                # Business logic
│       │   └── main.py                  # FastAPI app
│       ├── Dockerfile
│       └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                  # React components
│   │   ├── pages/                       # Page components
│   │   └── lib/api.ts                   # API client
│   ├── Dockerfile
│   └── package.json
├── rag-test/                            # RAG experimentation
├── docker-compose.yml
├── synthetic_orders.csv                 # Sample data
└── ENV_TEMPLATE
```

## Environment Variables

**Required:**
- `CMS_OPENAI_API_KEY` - OpenAI API key

**Optional:**
- `CMS_OPENAI_MODEL` (default: `gpt-4o-mini`)
- `CMS_WEAVIATE_URL` - Weaviate cluster URL
- `CMS_WEAVIATE_API_KEY` - Weaviate API key
- `CMS_WEAVIATE_SIMILARITY_THRESHOLD` (default: `0.7`)
- `CMS_WEAVIATE_TOP_K` (default: `2`)

## Troubleshooting

**Services not starting:**
```bash
docker-compose logs [service-name]
docker-compose down -v && docker-compose up --build
```

**Port already in use:**
```bash
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :5432  # Database
```

**Database issues:**
```bash
docker-compose restart cost-model-db
# Or clean restart:
docker-compose down -v && docker-compose up
```

**Missing OpenAI key:**
```bash
# Verify .env file exists and contains key
cat .env | grep OPENAI_API_KEY

# Restart services
docker-compose down && docker-compose up
```

## Production Deployment

1. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, etc.)
2. **Update CORS** in `backend/cost-model-service/app/main.py`
3. **Use production ASGI server** (Gunicorn with Uvicorn workers)
4. **Set up SSL/TLS** (Nginx/Traefik + Let's Encrypt)
5. **Use managed PostgreSQL** (AWS RDS, Azure Database, etc.)
6. **Implement monitoring** (logs, error tracking, metrics)

## Documentation

- **[Backend README](backend/cost-model-service/README.md)** - API reference and backend details
- **[Frontend README](frontend/README.md)** - Components and frontend development
- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** - Detailed setup guide

## License

[Add your license]

---

**Get OpenAI API key**: https://platform.openai.com/api-keys
