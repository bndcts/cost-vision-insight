# Setup Guide

## Environment Configuration

### 1. Create .env File

Copy the example environment file and configure it:

```bash
cp env.example .env
```

### 2. Configure Environment Variables

Edit the `.env` file with your values:

```bash
# Cost Model Service Configuration

# Environment
CMS_ENVIRONMENT=development

# Database Connection
CMS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cost_model

# OpenAI Configuration
CMS_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx  # Your OpenAI API key
CMS_OPENAI_MODEL=gpt-4o-mini                      # or gpt-4, gpt-3.5-turbo

# API Configuration
CMS_API_V1_PREFIX=/api/v1
CMS_PROJECT_NAME=cost-model-service
```

### 3. Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and paste it into your `.env` file as `CMS_OPENAI_API_KEY`

**Important:** Keep your API key secret! Never commit it to version control.

### 4. Choose an OpenAI Model

**Recommended models:**

- **gpt-4o-mini** (Recommended) - Fast, cheap, good quality
  - Cost: ~$0.15 per 1M input tokens
  - Best for production use
- **gpt-3.5-turbo** - Fastest, cheapest
  - Cost: ~$0.50 per 1M input tokens
  - Good for testing
- **gpt-4** - Highest quality
  - Cost: ~$30 per 1M input tokens
  - Use only if needed

For weight extraction, `gpt-4o-mini` is perfect and costs pennies per request.

## Database Setup

### 1. Run Migrations

```bash
cd backend/cost-model-service
alembic upgrade head
```

This will create the necessary database tables including the new processing status fields.

### 2. Verify Database Connection

Start the service and check logs:

```bash
./start.sh
```

You should see:

```
INFO: Database connection successful
INFO: Application startup complete
```

## Testing the OpenAI Integration

### 1. Create a Test File

Create a simple product specification file `test_spec.txt`:

```
Product Specification
====================

Product Name: Steel Widget
Material: Carbon Steel
Weight: 2.5 kg
Dimensions: 100mm x 50mm x 25mm
```

### 2. Test the Analyze Endpoint

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "articleName=Test Widget" \
  -F "description=Test product" \
  -F "productSpecification=@test_spec.txt"
```

**Response:**

```json
{
  "id": 1,
  "article_name": "Test Widget",
  "description": "Test product",
  "unit_weight": null,
  "processing_status": "processing",
  "created_at": "2025-10-25T10:00:00Z",
  ...
}
```

### 3. Check Processing Status

```bash
curl http://localhost:8000/api/articles/1/status
```

**While processing:**

```json
{
  "id": 1,
  "processing_status": "processing",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": null
}
```

**After completion (~5-10 seconds):**

```json
{
  "id": 1,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:12Z"
}
```

### 4. Get Full Article with Extracted Weight

```bash
curl http://localhost:8000/api/articles/1
```

**Response:**

```json
{
  "id": 1,
  "article_name": "Test Widget",
  "description": "Test product",
  "unit_weight": 2.5,  // <-- Extracted and converted to kg!
  "processing_status": "completed",
  "created_at": "2025-10-25T10:00:00Z",
  ...
}
```

## How It Works

### Weight Extraction Process

1. **File Upload**: Product specification file is uploaded with the article
2. **Background Task**: FastAPI starts async processing
3. **OpenAI Call**: File content is sent to OpenAI with specific prompt:
   - "Extract the product weight in grams from this document"
   - OpenAI identifies weight and converts to grams
   - Returns JSON: `{"unit_weight_grams": 2500}`
4. **Database Update**:
   - Weight is converted from grams to kilograms
   - Stored in `article.unit_weight` field
5. **Status Update**: Article marked as "completed"

### Example OpenAI Prompt

```
Extract the product weight in grams from the following document.

Content:
Product Weight: 2.5 kg
...

Return ONLY JSON: {"unit_weight_grams": <number>}
```

**OpenAI Response:**

```json
{ "unit_weight_grams": 2500 }
```

**Stored in DB:** `unit_weight = 2.5` (kg)

## Troubleshooting

### "OpenAI API key not configured"

**Problem:** The API key is not being loaded

**Solutions:**

1. Check `.env` file exists in the correct location
2. Verify the key name is `CMS_OPENAI_API_KEY` (with prefix!)
3. Restart the application after changing .env
4. Check file permissions on `.env`

```bash
# Verify environment variable is loaded
python3 -c "from app.core.config import get_settings; print(get_settings().openai_api_key)"
```

### "OpenAI API returned an error"

**Problem:** API request failed

**Common causes:**

1. **Invalid API key** - Check your key on OpenAI platform
2. **Insufficient credits** - Add billing info on OpenAI platform
3. **Rate limit** - You're sending too many requests (wait and retry)
4. **Model not available** - Check if the model exists

**Check OpenAI API status:**

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $CMS_OPENAI_API_KEY"
```

### Processing Stays at "processing" Forever

**Problem:** Background task failed silently

**Debug steps:**

1. Check backend logs:

```bash
docker-compose logs -f cost-model-service
```

2. Look for errors in the logs:

```
ERROR: Error calling OpenAI API: ...
ERROR: Error processing article 1: ...
```

3. Common issues:
   - OpenAI API timeout (usually resolves on retry)
   - Database connection lost
   - File encoding issues

### Weight Not Extracted

**Problem:** OpenAI returns `null` for weight

**Reasons:**

1. **No weight in document** - Document doesn't contain weight information
2. **Unusual format** - Weight is in an unusual format or unit
3. **Poor quality text** - Document is corrupted or illegible

**Solutions:**

- Add weight information to the specification file
- Use standard formats: "Weight: 2.5 kg" or "Mass: 500g"
- Check file encoding (should be UTF-8 or Latin-1)

## Cost Estimation

### OpenAI API Costs

Using `gpt-4o-mini` (recommended):

**Per request costs:**

- Input: ~1,000 tokens (8KB of text) = $0.00015
- Output: ~50 tokens (JSON response) = $0.000008
- **Total: ~$0.00016 per article**

**For 1,000 articles per month:**

- Cost: ~$0.16 (16 cents!)

**For 10,000 articles per month:**

- Cost: ~$1.60

Very affordable! 💰

## Production Considerations

### Security

1. **Never expose API key:**

   - Keep `.env` in `.gitignore`
   - Use secrets management in production (AWS Secrets Manager, etc.)

2. **Rate limiting:**

   - Implement rate limiting on the `/analyze` endpoint
   - Prevent abuse

3. **Input validation:**
   - Limit file size (e.g., max 10MB)
   - Validate file types

### Monitoring

1. **Track OpenAI usage:**

   - Log all API calls
   - Monitor costs on OpenAI dashboard
   - Set up billing alerts

2. **Monitor processing times:**

   - Alert if processing takes > 60 seconds
   - Track success/failure rates

3. **Database monitoring:**
   - Check processing_status distribution
   - Alert on failed articles

### Scaling

Current setup handles:

- ✅ Up to ~100 concurrent requests
- ✅ Files up to ~8KB (can be increased)
- ✅ Local background tasks

For larger scale:

- Use Celery + Redis for distributed task queue
- Increase file size limits with streaming
- Add caching for repeated API calls

## Next Steps

1. ✅ Set up `.env` file with OpenAI API key
2. ✅ Run database migrations
3. ✅ Test with a sample product specification
4. ✅ Integrate frontend polling
5. ⬜ Add error handling in frontend
6. ⬜ Deploy to production
7. ⬜ Set up monitoring and alerts

## Support

Need help? Check:

- OpenAI API docs: https://platform.openai.com/docs
- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- This project's README.md

Happy coding! 🚀
