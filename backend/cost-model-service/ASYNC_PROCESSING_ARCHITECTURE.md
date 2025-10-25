# Async Processing Architecture

## Overview

This document describes the async processing architecture for article analysis with OpenAI integration.

## Architecture Flow

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       │ 1. POST /analyze (article + files)
       ▼
┌─────────────────────────────────────────┐
│           Backend API                    │
│  ┌────────────────────────────────┐    │
│  │  Analyze Endpoint              │    │
│  │  1. Create Article (status:    │    │
│  │     "processing")              │    │
│  │  2. Return 201 with article ID │    │
│  │  3. Start Background Task      │    │
│  └────────────────────────────────┘    │
└───────────┬────────────┬────────────────┘
            │            │
   Response │            │ Background
       (ID) │            │ Processing
            │            │
            ▼            ▼
    ┌──────────┐   ┌──────────────────────────┐
    │ Frontend │   │ Background Task          │
    │          │   │ ┌──────────────────────┐ │
    │ Polling  │   │ │ 1. Extract Metadata  │ │
    │  Loop    │   │ │    from File (OpenAI)│ │
    │          │   │ │ 2. Update unit_weight│ │
    │ GET      │   │ │ 3. Generate Cost     │ │
    │ /articles│   │ │    Models (OpenAI)   │ │
    │ /{id}/   │   │ │ 4. Save to DB        │ │
    │ status   │   │ │ 5. Set status:       │ │
    │          │   │ │    "completed"       │ │
    │ Every    │   │ └──────────────────────┘ │
    │ 2-3 sec  │   └──────────────────────────┘
    └──────────┘
         │
         │ When status == "completed"
         ▼
    ┌──────────────────────┐
    │ GET /articles/{id}   │
    │ Fetch full data with │
    │ cost models          │
    └──────────────────────┘
```

## Components

### 1. Database Model Changes

**File:** `app/models/article.py`

Added processing status tracking fields:

- `processing_status`: Status of background processing (pending/processing/completed/failed)
- `processing_error`: Error message if processing failed
- `processing_started_at`: Timestamp when processing started
- `processing_completed_at`: Timestamp when processing finished

**Migration:** `alembic/versions/0005_add_processing_status.py`

Run migration with:

```bash
cd backend/cost-model-service
alembic upgrade head
```

### 2. OpenAI Service Functions

**File:** `app/services/openai_client.py`

#### `extract_metadata_from_file(file_content, filename)`

- Extracts product weight from specification files using OpenAI
- Specifically asks for weight in grams
- Returns: `{"unit_weight_grams": <float or null>}`
- Example: `{"unit_weight_grams": 2500.0}` for a 2.5kg product
- Automatically converts from any unit (kg, lb, oz, etc.) to grams

#### `generate_cost_models(article_name, article_description, unit_weight, available_indices)`

- Generates cost model breakdown for an article
- Returns: `[{index_id, part}, ...]`
- Uses GPT to determine percentage contribution of each cost index

### 3. Background Processing Service

**File:** `app/services/article_processor.py`

#### `process_article_async(article_id, db)`

Background task that performs:

1. **Weight Extraction**: Calls OpenAI to extract product weight from specification file
   - Sends file content to OpenAI with specific prompt
   - OpenAI returns weight in grams as JSON: `{"unit_weight_grams": 2500}`
   - Handles any weight unit (kg, g, lb, oz) and converts to grams
2. **Article Update**: Updates `unit_weight` field (converts grams to kg for storage)
3. **Cost Model Generation**: Calls OpenAI to generate cost model breakdown
4. **Database Persistence**: Saves generated cost models to database
5. **Status Updates**: Updates processing status throughout the flow

Error handling:

- Catches all exceptions and marks article as "failed"
- Stores error message in `processing_error` field
- Continues processing even if metadata extraction fails

### 4. API Endpoints

#### POST `/analyze` - Create and Start Processing

**File:** `app/api/routes/analyze.py`

**Request:**

- Form data: `articleName`, `description` (optional)
- Files: `productSpecification` (required), `drawing` (optional)

**Response:** `201 Created`

```json
{
  "id": 123,
  "article_name": "Widget A",
  "description": null,
  "unit_weight": null,
  "processing_status": "processing",
  "processing_error": null,
  "processing_started_at": null,
  "processing_completed_at": null,
  "created_at": "2025-10-25T10:00:00Z",
  ...
}
```

**Behavior:**

1. Creates article with status "processing"
2. Returns immediately with article ID
3. Starts background task using FastAPI BackgroundTasks

#### GET `/articles/{id}/status` - Poll Processing Status

**File:** `app/api/routes/articles.py`

**Response:** `200 OK`

```json
{
  "id": 123,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:00Z",
  "processing_completed_at": "2025-10-25T10:00:30Z"
}
```

**Status Values:**

- `pending`: Not yet started
- `processing`: Currently processing
- `completed`: Successfully completed
- `failed`: Processing failed (check `processing_error`)

**Usage:**

- Lightweight endpoint designed for polling
- Frontend should poll every 2-3 seconds
- Stop polling when status is "completed" or "failed"

#### GET `/articles/{id}` - Get Full Article Data

**File:** `app/api/routes/articles.py`

**Response:** `200 OK`

```json
{
  "id": 123,
  "article_name": "Widget A",
  "description": "Metal widget",
  "unit_weight": 2.5,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:00Z",
  "processing_completed_at": "2025-10-25T10:00:30Z",
  "created_at": "2025-10-25T10:00:00Z",
  ...
}
```

**Usage:**

- Call this after polling confirms status is "completed"
- Use separate endpoints to fetch cost models if needed

## Frontend Integration

### Recommended Flow

```typescript
// 1. Submit article for analysis
const formData = new FormData();
formData.append("articleName", "Widget A");
formData.append("productSpecification", file);

const response = await fetch("/api/analyze", {
  method: "POST",
  body: formData,
});

const article = await response.json();
const articleId = article.id;

// 2. Show loading state and start polling
setIsLoading(true);

const pollInterval = setInterval(async () => {
  const statusResponse = await fetch(`/api/articles/${articleId}/status`);
  const status = await statusResponse.json();

  if (status.processing_status === "completed") {
    clearInterval(pollInterval);
    setIsLoading(false);

    // 3. Fetch full article data
    const fullDataResponse = await fetch(`/api/articles/${articleId}`);
    const fullArticle = await fullDataResponse.json();

    // Display results
    showResults(fullArticle);
  } else if (status.processing_status === "failed") {
    clearInterval(pollInterval);
    setIsLoading(false);

    // Show error
    showError(status.processing_error);
  }
}, 2500); // Poll every 2.5 seconds
```

### Loading State UI

Show a loading screen with:

- Spinner or progress indicator
- Message: "Analyzing product specification..."
- Optional: Show current status messages
- Estimated time: 10-30 seconds for typical processing

## Configuration

### Environment Variables Setup

**IMPORTANT:** All environment variables use the `CMS_` prefix!

1. **Create your `.env` file:**

```bash
cd backend/cost-model-service
cp env.example .env
```

2. **Edit `.env` with your values:**

```bash
# OpenAI Configuration (REQUIRED)
CMS_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx  # Get from https://platform.openai.com/api-keys
CMS_OPENAI_MODEL=gpt-4o-mini                      # Recommended: fast and cheap

# Database Configuration
CMS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model

# API Configuration
CMS_ENVIRONMENT=development
CMS_API_V1_PREFIX=/api/v1
CMS_PROJECT_NAME=cost-model-service
```

3. **Get your OpenAI API key:**

   - Go to https://platform.openai.com/api-keys
   - Sign in or create an account
   - Create a new secret key
   - Copy and paste into `.env` as `CMS_OPENAI_API_KEY`

4. **Choose a model:**
   - `gpt-4o-mini` - **Recommended** (fast, cheap, good quality) ~$0.15/1M tokens
   - `gpt-3.5-turbo` - Fastest/cheapest ~$0.50/1M tokens
   - `gpt-4` - Highest quality ~$30/1M tokens

For detailed setup instructions, see [SETUP.md](SETUP.md)

## Performance Considerations

### Processing Time

- Metadata extraction: ~5-15 seconds
- Cost model generation: ~5-15 seconds
- **Total: ~10-30 seconds** depending on file size and OpenAI response time

### Polling Strategy

- **Interval**: 2-3 seconds (recommended)
- **Timeout**: Set a maximum timeout (e.g., 2 minutes)
- **Retry**: Consider exponential backoff for production

### Scalability

- Current implementation uses FastAPI BackgroundTasks (in-process)
- For high-volume production:
  - Consider using **Celery + Redis** for distributed task queue
  - Or **AWS Lambda** / **Google Cloud Functions** for serverless
  - Current approach works well for <100 concurrent requests

## Error Handling

### Common Errors

1. **OpenAI API Errors**

   - Rate limits: Implement retry with exponential backoff
   - Invalid API key: Check environment configuration
   - Timeout: OpenAI calls may take 10-20 seconds

2. **File Processing Errors**

   - Binary files: System attempts UTF-8 decode, falls back gracefully
   - Large files: Consider file size limits (current: 4000 chars sent to OpenAI)

3. **Database Errors**
   - Connection issues: Background task will fail and mark article as "failed"
   - Constraint violations: Logged but processing continues

### Monitoring

Add logging to track:

- Processing duration per article
- OpenAI API success/failure rates
- Background task failures

```python
logger.info(f"Article {article_id} processing completed in {duration}s")
logger.error(f"OpenAI API error: {error}")
```

## Testing

### Manual Testing

1. **Start the backend:**

```bash
cd backend/cost-model-service
./start.sh
```

2. **Test the analyze endpoint:**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "articleName=Test Widget" \
  -F "description=Test description" \
  -F "productSpecification=@/path/to/spec.txt"
```

3. **Poll for status:**

```bash
curl http://localhost:8000/api/articles/1/status
```

4. **Get full article:**

```bash
curl http://localhost:8000/api/articles/1
```

### Automated Testing

Consider adding tests for:

- Background task execution
- Status transitions
- Error handling
- OpenAI mock responses

## Future Enhancements

1. **WebSocket Support**: Push updates instead of polling
2. **Progress Updates**: More granular status (e.g., "extracting_metadata", "generating_models")
3. **Batch Processing**: Process multiple articles at once
4. **Retry Logic**: Automatic retry on OpenAI failures
5. **Caching**: Cache OpenAI responses for similar files
6. **File Type Support**: Add support for PDF, images with OCR

## Troubleshooting

### Background task doesn't start

- Check logs for errors in `article_processor.py`
- Verify OpenAI API key is set
- Check database connection

### Processing stays in "processing" status

- Check background task logs for errors
- Verify OpenAI API is accessible
- Check for database deadlocks

### Frontend never receives "completed" status

- Increase polling timeout
- Check backend logs for exceptions
- Verify article was created successfully

## Summary

This architecture provides:
✅ **Non-blocking API**: Immediate response to frontend
✅ **Async Processing**: OpenAI calls don't block requests
✅ **Status Tracking**: Real-time progress updates
✅ **Error Handling**: Graceful failure with error messages
✅ **Scalable**: Can be extended to distributed queue if needed

The system is production-ready for moderate loads and can be scaled as needed.
