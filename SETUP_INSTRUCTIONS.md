# Setup Instructions

## Quick Start (Docker - Recommended)

### Step 1: Create .env File with OpenAI API Key

**IMPORTANT:** You need a `.env` file in the **PROJECT ROOT** (same directory as `docker-compose.yml`)

```bash
# From project root
cd /Users/benediktschwankner/Documents/dev/cost-vision-insight

# Create .env file from template
cp ENV_TEMPLATE .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Your `.env` file should look like:
```bash
# OpenAI Configuration (REQUIRED)
CMS_OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE

# Optional settings
CMS_OPENAI_MODEL=gpt-4o-mini
```

**Get your OpenAI API key:** https://platform.openai.com/api-keys

### Step 2: Build and Start Services

```bash
# From project root
docker-compose up --build
```

### Step 3: Verify Everything is Running

**Check services:**
```bash
docker-compose ps
```

You should see:
- ✅ `cost-model-db` - Running (healthy)
- ✅ `cost-model-service` - Running on port 8000
- ✅ `frontend` - Running on port 5173

**Test API:**
```bash
curl http://localhost:8000/api/v1/health
# Should return: {"status":"ok"}
```

**Access frontend:**
Open http://localhost:5173 in your browser

### Step 4: Test OpenAI Integration

1. Create a test file:
```bash
echo "Product Specification
Weight: 2.5 kg
Material: Steel" > test_product.txt
```

2. Open frontend at http://localhost:5173
3. Fill in article name
4. Upload `test_product.txt`
5. Wait ~10-15 seconds
6. See extracted weight: **2.50 kg (2500g)**

## Troubleshooting

### Issue: "OpenAI API key not configured"

**Problem:** The API key is not being loaded

**Solution:**
1. Check `.env` file exists in PROJECT ROOT:
   ```bash
   ls -la .env
   ```

2. Verify it contains your key:
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

3. Restart containers:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

4. Check if environment variable is passed to container:
   ```bash
   docker exec cost-vision-insight-cost-model-service-1 env | grep OPENAI
   ```

### Issue: Services not starting

**Check logs:**
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs cost-model-service
docker-compose logs cost-model-db
docker-compose logs frontend
```

### Issue: "Database not ready"

**Check database health:**
```bash
docker-compose ps
# cost-model-db should show "healthy"
```

**If unhealthy:**
```bash
docker-compose restart cost-model-db
```

### Issue: Port already in use

```bash
# Stop all containers
docker-compose down

# Check what's using the port
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :5432  # Database

# Kill the process or use different ports in docker-compose.yml
```

## File Structure

```
cost-vision-insight/
├── .env                          ← CREATE THIS! (from ENV_TEMPLATE)
├── ENV_TEMPLATE                  ← Template for .env
├── docker-compose.yml            ← Docker configuration
├── backend/
│   ├── indices.csv              ← Cost indices data
│   └── cost-model-service/
│       ├── env.example          ← For local dev (not needed for Docker)
│       ├── app/
│       │   ├── core/
│       │   │   └── config.py    ← Reads CMS_* env vars
│       │   └── services/
│       │       └── openai_client.py  ← OpenAI integration
│       └── start.sh             ← Startup script
└── frontend/
    └── src/
        └── pages/
            └── Index.tsx        ← Main UI
```

## Environment Variables Reference

### Required

- `CMS_OPENAI_API_KEY` - Your OpenAI API key (**REQUIRED**)

### Optional

- `CMS_OPENAI_MODEL` - Model to use (default: `gpt-4o-mini`)
- `CMS_DATABASE_URL` - Database connection string (set by docker-compose)
- `CMS_INDEX_CSV_PATH` - Path to indices CSV (default: `/app/data/indices.csv`)
- `CMS_ENV` - Environment (default: `development`)

## How Environment Variables Flow

```
1. You create .env in project root:
   ┌────────────────────────────────┐
   │ .env (project root)            │
   │ CMS_OPENAI_API_KEY=sk-...      │
   └────────────────────────────────┘
                 ↓
2. docker-compose.yml reads it:
   ┌────────────────────────────────┐
   │ docker-compose.yml             │
   │ environment:                   │
   │   CMS_OPENAI_API_KEY: ${...}   │
   └────────────────────────────────┘
                 ↓
3. Docker passes to container:
   ┌────────────────────────────────┐
   │ Container environment          │
   │ CMS_OPENAI_API_KEY=sk-...      │
   └────────────────────────────────┘
                 ↓
4. Pydantic Settings reads it:
   ┌────────────────────────────────┐
   │ app/core/config.py             │
   │ class Settings(BaseSettings):  │
   │   openai_api_key: str          │
   │   Config:                      │
   │     env_prefix = "CMS_"        │
   └────────────────────────────────┘
                 ↓
5. OpenAI client uses it:
   ┌────────────────────────────────┐
   │ app/services/openai_client.py  │
   │ client = OpenAI(               │
   │   api_key=settings.openai_api  │_key
   │ )                              │
   └────────────────────────────────┘
```

## Development Workflow

### Making Code Changes

**Backend:**
```bash
# Code is mounted as volume - changes reflect immediately
# No need to rebuild for Python code changes

# Edit files in: backend/cost-model-service/app/
# Server auto-reloads on changes
```

**Frontend:**
```bash
# For frontend changes, you may need to restart:
docker-compose restart frontend
```

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f cost-model-service
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart cost-model-service
```

### Stop Everything

```bash
# Stop containers (preserves data)
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## Production Deployment

For production:

1. **Use secrets management** - Don't use .env file
   - AWS Secrets Manager
   - Azure Key Vault
   - Kubernetes Secrets

2. **Update docker-compose.yml** or use Kubernetes/ECS

3. **Set environment directly:**
   ```bash
   export CMS_OPENAI_API_KEY=sk-...
   docker-compose up -d
   ```

## Summary

**For Docker (Recommended):**
1. ✅ Create `.env` in **project root** (where docker-compose.yml is)
2. ✅ Add `CMS_OPENAI_API_KEY=sk-...`
3. ✅ Run `docker-compose up --build`
4. ✅ Done!

**For Local Development (Advanced):**
1. Create `.env` in `backend/cost-model-service/` from `env.example`
2. Install Python dependencies
3. Run PostgreSQL locally
4. Run `./start.sh`

**The key point:** Environment variables are passed FROM `.env` (project root) → THROUGH `docker-compose.yml` → TO the container → READ BY `config.py`

Need help? Check the logs:
```bash
docker-compose logs cost-model-service | grep -i openai
```

