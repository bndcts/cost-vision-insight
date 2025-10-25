# Article Data Flow - Final Implementation

## Overview

After polling completes successfully, the frontend now fetches the full article data including the extracted weight and displays it prominently.

## Complete Flow

### 1. Submit Article

```typescript
POST /api/v1/analyze
FormData: { articleName, productSpecification, drawing?, description? }
↓
Response: { id: 123, processing_status: "processing", ... }
```

### 2. Polling Phase

```typescript
// Every 2 seconds
GET /api/v1/articles/123/status
↓
Response: { processing_status: "processing" | "completed" | "failed" }
```

### 3. On Success - Fetch Full Data

```typescript
// When status === "completed"
const handleAnalysisComplete = async () => {
  // Fetch complete article with extracted weight
  const response = await fetch(`/api/v1/articles/${articleId}`);
  const fullArticle = await response.json();

  // fullArticle contains:
  // {
  //   id: 123,
  //   article_name: "Steel Widget",
  //   unit_weight: 2.5,  // ← Extracted by OpenAI!
  //   description: "...",
  //   processing_status: "completed",
  //   processing_started_at: "...",
  //   processing_completed_at: "...",
  //   created_at: "..."
  // }

  setCreatedArticleResponse(fullArticle);
  setShowResults(true);
};
```

### 4. Display Results

```tsx
{
  showResults && createdArticleResponse && (
    <Card className="bg-primary/5 border-primary/20">
      <h3>Extracted Product Information</h3>

      <div className="grid grid-cols-3 gap-4">
        {/* Article Name */}
        <div>
          <p className="text-sm text-muted-foreground">Article Name</p>
          <p className="text-lg font-semibold">
            {createdArticleResponse.article_name}
          </p>
        </div>

        {/* Product Weight - EXTRACTED BY AI! */}
        <div>
          <p className="text-sm text-muted-foreground">Product Weight</p>
          <p className="text-lg font-semibold">
            {createdArticleResponse.unit_weight ? (
              <>
                {createdArticleResponse.unit_weight.toFixed(2)} kg
                <span className="text-muted-foreground ml-2">
                  ({(createdArticleResponse.unit_weight * 1000).toFixed(0)}g)
                </span>
              </>
            ) : (
              <span className="text-muted-foreground">Not found</span>
            )}
          </p>
        </div>

        {/* Processing Time */}
        <div>
          <p className="text-sm text-muted-foreground">Processing Time</p>
          <p className="text-lg font-semibold">
            {Math.round(
              (new Date(
                createdArticleResponse.processing_completed_at
              ).getTime() -
                new Date(
                  createdArticleResponse.processing_started_at
                ).getTime()) /
                1000
            )}
            s
          </p>
        </div>
      </div>

      {/* Description if available */}
      {createdArticleResponse.description && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-muted-foreground">Description</p>
          <p className="text-sm">{createdArticleResponse.description}</p>
        </div>
      )}
    </Card>
  );
}
```

## Example User Experience

### Scenario: Upload product spec with "Weight: 2.5 kg"

**Step 1: Upload**

```
User uploads file → Backend creates article (ID: 123)
```

**Step 2: Loading (10-15 seconds)**

```
┌─────────────────────────────────────┐
│   Processing Analysis               │
│                                     │
│   Extracting product weight from    │
│   specification...                  │
│                                     │
│   [=======>     ] 65% | 10s elapsed │
│                                     │
│   • • •                             │
└─────────────────────────────────────┘
```

**Step 3: Backend Processing**

```
OpenAI API Call:
  Input: "Product specification content... Weight: 2.5 kg ..."
  ↓
  OpenAI Response: {"unit_weight_grams": 2500}
  ↓
  Database Update: article.unit_weight = 2.5 (converted to kg)
  ↓
  Status Update: processing_status = "completed"
```

**Step 4: Frontend Fetches Data**

```
GET /api/v1/articles/123
↓
Response: {
  "id": 123,
  "article_name": "Steel Widget",
  "unit_weight": 2.5,
  "processing_status": "completed",
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:17Z"
}
```

**Step 5: Display Results**

```
┌──────────────────────────────────────────────────────┐
│  📊 Extracted Product Information                    │
│                                                      │
│  Article Name       Product Weight    Processing    │
│  Steel Widget       2.50 kg (2500g)   12s          │
│                                                      │
└──────────────────────────────────────────────────────┘

[Rest of analysis results...]
```

## API Endpoints Used

### 1. Create & Start Processing

```http
POST /api/v1/analyze/
Content-Type: multipart/form-data

Response: 201 Created
{
  "id": 123,
  "article_name": "Steel Widget",
  "processing_status": "processing"
}
```

### 2. Poll Status (Every 2 seconds)

```http
GET /api/v1/articles/123/status

Response: 200 OK
{
  "id": 123,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:17Z"
}
```

### 3. Fetch Full Article Data (On completion)

```http
GET /api/v1/articles/123

Response: 200 OK
{
  "id": 123,
  "article_name": "Steel Widget",
  "description": null,
  "unit_weight": 2.5,  // ← THE EXTRACTED WEIGHT!
  "product_specification_filename": "spec.txt",
  "drawing_filename": null,
  "comment": null,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:17Z",
  "created_at": "2025-10-25T10:00:00Z"
}
```

## Key Features

✅ **Automatic Data Fetch**: After polling confirms completion, full article data is fetched automatically

✅ **Weight Display**: Shows weight in both kg and grams for clarity

- "2.50 kg (2500g)"

✅ **Processing Stats**: Shows how long OpenAI processing took

- "Processing Time: 12s"

✅ **Error Handling**: If weight not found, shows "Not found" gracefully

✅ **Clean UI**: Beautiful card with extracted information prominently displayed

## Code Changes

### handleAnalysisComplete Function

**Before:**

```typescript
const handleAnalysisComplete = () => {
  setIsAnalyzing(false);
  setShowResults(true);
};
```

**After:**

```typescript
const handleAnalysisComplete = async () => {
  if (!createdArticleId) return;

  try {
    // Fetch complete article with extracted weight
    const response = await fetch(
      `http://localhost:8000/api/v1/articles/${createdArticleId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch article: ${response.status}`);
    }

    const fullArticle: ArticleResponse = await response.json();
    console.log("Full article data:", fullArticle);

    // Store complete article data
    setCreatedArticleResponse(fullArticle);

    // Show results
    setIsAnalyzing(false);
    setShowResults(true);
    setProcessingError(null);
  } catch (error) {
    console.error("Error fetching article data:", error);
    setIsAnalyzing(false);
    setProcessingError(
      error instanceof Error ? error.message : "Failed to fetch article data"
    );
  }
};
```

### ArticleResponse Interface

**Updated to include all fields:**

```typescript
interface ArticleResponse {
  id: number;
  article_name: string;
  description?: string;
  unit_weight?: number; // ← NEW: Extracted weight in kg
  product_specification_filename?: string;
  drawing_filename?: string;
  comment?: string;
  processing_status: string; // ← NEW
  processing_error?: string | null; // ← NEW
  processing_started_at?: string | null; // ← NEW
  processing_completed_at?: string | null; // ← NEW
  created_at: string;
}
```

## Testing

### Test Case 1: Weight Found

**Input file (test_spec.txt):**

```
Product Specification
Weight: 2.5 kg
Material: Steel
```

**Expected Result:**

```
Article Name: Test Product
Product Weight: 2.50 kg (2500g)  ✅
Processing Time: 10s
```

### Test Case 2: Weight Not Found

**Input file (no_weight.txt):**

```
Product Specification
Material: Steel
Color: Blue
```

**Expected Result:**

```
Article Name: Test Product
Product Weight: Not found  ✅
Processing Time: 8s
```

### Test Case 3: Different Units

**Input file (lbs.txt):**

```
Product Weight: 5.5 lbs
```

**Expected Result:**

```
Product Weight: 2.49 kg (2495g)  ✅
(OpenAI converts lbs to grams automatically)
```

## Benefits

1. **User sees actual extracted data** - Not mock data
2. **Weight is prominently displayed** - Easy to verify extraction worked
3. **Shows processing time** - Transparency about how long it took
4. **Graceful failure** - "Not found" if weight not in document
5. **Dual units** - Shows both kg and grams for convenience

## Next Steps

With this implementation:

- ✅ Backend extracts weight with OpenAI
- ✅ Frontend polls for completion
- ✅ Frontend fetches full article data
- ✅ Frontend displays extracted weight
- ✅ Error handling for all cases

Ready to test end-to-end! 🚀
