# OpenAI Integration Guide

## Quick Start

### 1. Setup Environment Variables

Create a `.env` file:

```bash
cp env.example .env
```

Edit `.env` and add your OpenAI API key:

```bash
CMS_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
CMS_OPENAI_MODEL=gpt-4o-mini
```

**Get your API key:** https://platform.openai.com/api-keys

### 2. How It Works

When you upload a product specification file through the `/analyze` endpoint:

1. **File Upload** → Backend receives the file
2. **Background Task Starts** → Returns article ID immediately
3. **OpenAI API Call** → Extracts weight in grams
4. **Database Update** → Saves extracted weight
5. **Status: Completed** → Frontend can fetch results

## The OpenAI Prompt

The actual prompt sent to OpenAI:

```
Extract the product weight in grams from the following product specification document.

Document filename: my_product.txt

Content:
[Your file content - up to 8000 characters]

Instructions:
- Find the product weight/mass in the document
- Convert it to grams (g) if it's in a different unit (kg, mg, lb, oz, etc.)
- Return ONLY a JSON object with this exact format:
{"unit_weight_grams": <weight as number in grams, or null if not found>}

Examples:
- If weight is "2.5 kg", return: {"unit_weight_grams": 2500}
- If weight is "500 g", return: {"unit_weight_grams": 500}
- If weight is "1.2 lb", return: {"unit_weight_grams": 544.31}
- If no weight found, return: {"unit_weight_grams": null}

Return ONLY the JSON object, no explanations or additional text.
```

## OpenAI Response

**Example response from OpenAI:**

```json
{ "unit_weight_grams": 2500 }
```

**What the backend does:**

1. Parses the JSON response
2. Converts grams to kilograms: `2500g ÷ 1000 = 2.5kg`
3. Stores in database: `article.unit_weight = 2.5`

## API Configuration

```python
# In app/services/openai_client.py

response = client.chat.completions.create(
    model="gpt-4o-mini",        # Fast, cheap, good quality
    temperature=0.0,             # Most deterministic (no randomness)
    max_tokens=100,              # Small response (JSON only)
    messages=[...]
)
```

## Supported Weight Units

OpenAI automatically converts from:

- ✅ **Grams** (g, gm, gram, grams)
- ✅ **Kilograms** (kg, kilogram, kilograms)
- ✅ **Milligrams** (mg, milligram, milligrams)
- ✅ **Pounds** (lb, lbs, pound, pounds)
- ✅ **Ounces** (oz, ounce, ounces)
- ✅ **Tons** (t, ton, tons, tonne, tonnes)

**Examples:**

- "Weight: 2.5 kg" → `2500 grams`
- "Mass: 500g" → `500 grams`
- "Product weighs 1.2 lbs" → `544.31 grams`
- "Net weight 3 oz" → `85.05 grams`

## Example Test File

Create `test_spec.txt`:

```
PRODUCT SPECIFICATION
=====================

Product Name: Steel Widget
Material: Carbon Steel
Weight: 2.5 kg
Dimensions: 100mm x 50mm x 25mm
Color: Silver
Finish: Polished
```

## Testing

### 1. Upload File

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "articleName=Steel Widget" \
  -F "description=Test product" \
  -F "productSpecification=@test_spec.txt"
```

**Response:**

```json
{
  "id": 1,
  "article_name": "Steel Widget",
  "processing_status": "processing",
  "unit_weight": null
}
```

### 2. Poll for Status (wait 5-10 seconds)

```bash
curl http://localhost:8000/api/articles/1/status
```

**Response when completed:**

```json
{
  "id": 1,
  "processing_status": "completed",
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:12Z"
}
```

### 3. Get Full Article

```bash
curl http://localhost:8000/api/articles/1
```

**Response:**

```json
{
  "id": 1,
  "article_name": "Steel Widget",
  "unit_weight": 2.5, // ← Extracted weight in kg!
  "processing_status": "completed"
}
```

## Cost Breakdown

Using `gpt-4o-mini` (recommended):

**Per request:**

- Input tokens: ~1,500 (for 8KB text file)
- Output tokens: ~20 (JSON response)
- **Cost: ~$0.0002 per article** (less than a cent!)

**Monthly estimates:**

- 100 articles: ~$0.02 (2 cents)
- 1,000 articles: ~$0.20 (20 cents)
- 10,000 articles: ~$2.00 (2 dollars)

Very affordable! 💰

## Error Handling

### If OpenAI Returns Null

```json
{ "unit_weight_grams": null }
```

**Reasons:**

- No weight information in the document
- Weight in unusual format
- File is corrupted or illegible

**Solution:** Add weight information in standard format

### If API Call Fails

The article will be marked as `"failed"`:

```json
{
  "processing_status": "failed",
  "processing_error": "OpenAI API error: Rate limit exceeded"
}
```

**Common errors:**

- **Rate limit**: Wait and retry
- **Invalid API key**: Check your `.env` file
- **Insufficient credits**: Add billing on OpenAI platform

## Logging

The system logs all OpenAI interactions:

```
INFO: Calling OpenAI to extract weight from product_spec.txt
INFO: OpenAI response: {"unit_weight_grams": 2500}
INFO: Successfully extracted weight: 2500g from product_spec.txt
INFO: Updated article 1 with unit_weight: 2.5 kg (2500g)
```

Check logs:

```bash
docker-compose logs -f cost-model-service | grep OpenAI
```

## Security Best Practices

1. ✅ **Never commit `.env` file** - Already in `.gitignore`
2. ✅ **Use environment variables** - Already implemented
3. ✅ **Rotate API keys regularly** - On OpenAI platform
4. ✅ **Set spending limits** - On OpenAI billing page
5. ✅ **Monitor usage** - Check OpenAI dashboard

## Model Comparison

| Model         | Speed            | Quality       | Cost (per 1M tokens) | Recommended For   |
| ------------- | ---------------- | ------------- | -------------------- | ----------------- |
| gpt-4o-mini   | ⚡⚡⚡ Fast      | ⭐⭐⭐ Good   | $0.15                | **Production** ✅ |
| gpt-3.5-turbo | ⚡⚡⚡⚡ Fastest | ⭐⭐ OK       | $0.50                | Testing           |
| gpt-4         | ⚡ Slower        | ⭐⭐⭐⭐ Best | $30.00               | Critical accuracy |

**Recommendation:** Use `gpt-4o-mini` for production - it's fast, accurate, and costs almost nothing.

## Troubleshooting

### "OpenAI API key not configured"

```bash
# Check if key is loaded
python3 -c "from app.core.config import get_settings; print(get_settings().openai_api_key)"
```

**Fix:**

1. Create `.env` file from `env.example`
2. Add `CMS_OPENAI_API_KEY=sk-...` (note the `CMS_` prefix!)
3. Restart the application

### Weight extraction returns null

**Check your test file format:**

```
✅ Good: "Weight: 2.5 kg"
✅ Good: "Mass: 500 grams"
✅ Good: "Product weight 1.2 lbs"

❌ Bad: "Very light" (no number)
❌ Bad: "২.৫ কেজি" (non-Latin characters)
```

### Processing takes too long

- Expected: 5-15 seconds
- If > 30 seconds: Check OpenAI API status
- If timeout: OpenAI might be experiencing issues

## Next Steps

1. ✅ Set up `.env` with your OpenAI API key
2. ✅ Test with the example file
3. ✅ Verify weight extraction works
4. ✅ Integrate frontend polling
5. ⬜ Add more file types (PDF, images, etc.)
6. ⬜ Deploy to production

## Resources

- **OpenAI Platform:** https://platform.openai.com/
- **API Keys:** https://platform.openai.com/api-keys
- **API Docs:** https://platform.openai.com/docs
- **Pricing:** https://openai.com/pricing
- **Usage Dashboard:** https://platform.openai.com/usage

Happy integrating! 🚀
