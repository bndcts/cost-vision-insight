# Cost Vision Insight

Cost modeling and estimation platform with AI-powered analysis.

**Stack:** FastAPI + PostgreSQL + React + TypeScript + Tailwind + shadcn/ui

## Quick Start

```bash
# Start everything
docker-compose up

# View logs
docker-compose logs -f

# Stop everything
docker-compose down -v
```

**Access:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Running Services Separately

```bash
# Start individual services
docker-compose up cost-model-db          # Database only
docker-compose up cost-model-service     # Backend + DB
docker-compose up frontend               # Frontend only

# Restart one service (doesn't affect others!)
docker-compose restart frontend
docker-compose restart cost-model-service

# Rebuild and restart
docker-compose up -d --build frontend
```

## Development Workflows

### Frontend Development (Recommended)

```bash
# Backend in Docker
docker-compose up -d cost-model-db cost-model-service

# Frontend local (instant hot-reload)
cd frontend
npm install
npm run dev
```

### Backend Development (Recommended)

```bash
# Database in Docker
docker-compose up -d cost-model-db

# Backend local (auto-reload)
cd backend/cost-model-service
uv pip install -r requirements.txt
export CMS_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model"
uvicorn app.main:app --reload
```

### Full Local (Best for Active Development)

```bash
# Terminal 1: Database
docker-compose up cost-model-db

# Terminal 2: Backend
cd backend/cost-model-service
uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend
npm run dev
```

## Common Commands

```bash
# Docker
docker-compose ps                           # Check status
docker-compose logs -f cost-model-service   # View logs
docker-compose build cost-model-service     # Rebuild service
docker-compose down -v                      # Clean reset

# Backend
cd backend/cost-model-service
alembic upgrade head                        # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
uvicorn app.main:app --reload               # Run with hot-reload

# Frontend
cd frontend
npm run dev                                 # Development server
npm run build                               # Production build

# Database
docker-compose exec cost-model-db psql -U postgres -d cost_model
docker-compose exec cost-model-db psql -U postgres -d cost_model -c "\dt"
```

## Environment Variables

Create `.env` in project root (optional):

```bash
CMS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model
CMS_OPENAI_API_KEY=your-key-here
CMS_OPENAI_MODEL=gpt-4o-mini
```

## Troubleshooting

```bash
# Database not connecting
docker-compose down -v && docker-compose up -d

# Port already in use
lsof -i :8000  # Find process using port

# Clean rebuild
docker-compose build --no-cache
docker-compose up
```

## Project Structure

```
├── backend/cost-model-service/
│   ├── alembic/                # Migrations
│   ├── app/
│   │   ├── api/routes/         # Endpoints
│   │   ├── models/             # SQLAlchemy models
│   │   └── schemas/            # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/         # React components
│       └── pages/              # Page components
└── docker-compose.yml
```

## API Documentation

Interactive docs: http://localhost:8000/docs

Main endpoints:

- `/api/v1/articles` - Article management
- `/api/v1/indices` - Price indices
- `/api/v1/cost-models` - Cost models
- `/api/v1/orders` - Order history
- `/api/v1/estimates` - AI cost estimation
