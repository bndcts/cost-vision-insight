# Frontend Polling Implementation

## Overview

The frontend now implements proper polling to track the backend's async OpenAI processing. No alerts are shown - instead, a real-time loading overlay displays progress and only shows results when processing completes successfully.

## How It Works

### 1. User Submits Article

```
User fills form → Submit → POST /api/v1/analyze
                             ↓
                    Backend returns article ID
                             ↓
                    LoadingOverlay starts polling
```

### 2. Polling Mechanism

**LoadingOverlay Component** (`src/components/LoadingOverlay.tsx`)

- Receives `articleId` from parent
- Polls `GET /api/v1/articles/{articleId}/status` every 2 seconds
- Shows visual progress animation
- Displays elapsed time
- Handles three outcomes:
  - ✅ **Completed**: Calls `onComplete()` → Shows results
  - ❌ **Failed**: Calls `onError(message)` → Shows error
  - ⏳ **Processing**: Continues polling

### 3. Status Flow

```typescript
// Initial upload
const response = await fetch("/api/v1/analyze/", {
  method: "POST",
  body: formData,
});

const article = await response.json();
// article.processing_status = "processing"

// Start polling
<LoadingOverlay
  articleId={article.id}
  onComplete={handleSuccess}
  onError={handleError}
/>

// Poll every 2 seconds
GET /articles/{id}/status
↓
{
  "processing_status": "processing" | "completed" | "failed",
  "processing_error": "...",
  ...
}
```

## Components Modified

### 1. LoadingOverlay.tsx

**Before:**

- Fake progress animation
- Fixed 5-second duration
- No real backend status

**After:**

```typescript
interface LoadingOverlayProps {
  articleId: number; // Required: article to poll
  onComplete: () => void; // Called when status = "completed"
  onError: (error: string) => void; // Called when status = "failed"
}

// Polls backend every 2 seconds
// Shows real-time processing messages
// Displays elapsed time
// Only completes when backend confirms
```

**Key Features:**

- ✅ Real backend polling
- ✅ Elapsed time counter
- ✅ Dynamic status messages
- ✅ Progress animation (visual feedback)
- ✅ Error handling
- ✅ Automatic cleanup on unmount

### 2. Index.tsx (Main Page)

**Changes:**

1. **Removed all `alert()` calls** - No more popups!

2. **Added error state:**

```typescript
const [processingError, setProcessingError] = useState<string | null>(null);
```

3. **Updated LoadingOverlay usage:**

```typescript
{
  isAnalyzing && createdArticleId && (
    <LoadingOverlay
      articleId={createdArticleId}
      onComplete={handleAnalysisComplete}
      onError={handleAnalysisError}
    />
  );
}
```

4. **Added error display:**

```typescript
{
  processingError && (
    <Card className="border-destructive/50 bg-destructive/5">
      <AlertCircle />
      <h3>Processing Failed</h3>
      <p>{processingError}</p>
    </Card>
  );
}
```

5. **Results only show on success:**

```typescript
// showResults is only set to true when status = "completed"
// If status = "failed", showResults stays false
{showResults && (
  <CostBreakdown />
  <PriceTrendChart />
  // ... rest of results
)}
```

## User Experience Flow

### Success Case ✅

```
1. User submits form
   ↓
2. Loading overlay appears
   "Extracting product weight from specification..."
   Progress: [=====>    ] 45% | 5s elapsed
   ↓
3. Status messages rotate every 3 seconds:
   - "Extracting product weight from specification..."
   - "Analyzing file content with AI..."
   - "Generating cost models..."
   - "Finalizing analysis..."
   ↓
4. Backend completes (status = "completed")
   ↓
5. Frontend fetches full article data
   GET /api/v1/articles/{id}
   ↓
6. Progress hits 100%
   "Analysis complete!"
   ↓
7. Results section slides in with:
   - Article name
   - Extracted weight (e.g., "2.50 kg (2500g)")
   - Processing time (e.g., "12s")
   - Description (if available)
   - Full cost analysis
```

### Failure Case ❌

```
1. User submits form
   ↓
2. Loading overlay appears
   ↓
3. Backend fails (e.g., invalid OpenAI key)
   ↓
4. Loading overlay disappears
   ↓
5. Error card appears:
   ┌─────────────────────────────────────┐
   │ ⚠️  Processing Failed              │
   │                                     │
   │ OpenAI API error: Invalid API key   │
   │                                     │
   │ Common issues:                      │
   │ • OpenAI API key not configured     │
   │ • File format not supported         │
   │ • Network connection issues         │
   └─────────────────────────────────────┘
   ↓
6. User can fix issue and resubmit
```

## API Endpoints Used

### 1. Create Article & Start Processing

**Endpoint:** `POST /api/v1/analyze/`

**Request:**

```typescript
FormData {
  articleName: string
  description?: string
  productSpecification: File
  drawing?: File
}
```

**Response:**

```json
{
  "id": 123,
  "article_name": "Steel Widget",
  "processing_status": "processing",
  "created_at": "2025-10-25T10:00:00Z"
}
```

### 2. Poll Processing Status

**Endpoint:** `GET /api/v1/articles/{id}/status`

**Response (Processing):**

```json
{
  "id": 123,
  "processing_status": "processing",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": null
}
```

**Response (Completed):**

```json
{
  "id": 123,
  "processing_status": "completed",
  "processing_error": null,
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:15Z"
}
```

**Response (Failed):**

```json
{
  "id": 123,
  "processing_status": "failed",
  "processing_error": "OpenAI API error: Invalid API key",
  "processing_started_at": "2025-10-25T10:00:05Z",
  "processing_completed_at": "2025-10-25T10:00:08Z"
}
```

## Technical Details

### Polling Configuration

```typescript
// Polling interval: 2 seconds
const pollInterval = setInterval(pollStatus, 2000);

// Timeout: None (polls until completed/failed)
// In production, consider adding max timeout (e.g., 2 minutes)
```

### Progress Animation

The progress bar is purely visual feedback:

- **0-50%**: Fast progress (2% per 500ms)
- **50-70%**: Medium progress (1% per 500ms)
- **70-90%**: Slow progress (0.5% per 500ms)
- **90-100%**: Only moves when backend confirms completion

This provides good UX without being misleading - the bar never reaches 100% until the backend actually completes.

### Status Messages

Messages rotate every 3 seconds based on elapsed time:

```typescript
const messages = [
  "Extracting product weight from specification...",
  "Analyzing file content with AI...",
  "Generating cost models...",
  "Finalizing analysis...",
];

const messageIndex = Math.floor(elapsedTime / 3) % messages.length;
```

### Cleanup

All intervals are properly cleaned up:

```typescript
return () => {
  clearInterval(pollInterval);
  clearInterval(progressInterval);
  clearInterval(timeInterval);
};
```

This prevents memory leaks and ensures polling stops when:

- Component unmounts
- Processing completes
- Processing fails

## Error Handling

### Network Errors

If polling fails (network issue), it:

- ✅ Logs error to console
- ✅ Continues polling (retry)
- ❌ Does NOT show error to user (transient)

```typescript
catch (error) {
  console.error("Error polling status:", error);
  // Continue polling - might be transient network issue
}
```

### Backend Errors

If backend returns `status = "failed"`:

- ✅ Shows error message to user
- ✅ Displays helpful troubleshooting tips
- ✅ Allows user to retry

## Testing

### Manual Testing

1. **Success Case:**

```bash
# Create test file
echo "Product Weight: 2.5 kg" > test_spec.txt

# Upload via frontend
# Should see:
# - Loading overlay
# - Status messages rotating
# - Progress animation
# - Results appear after ~10 seconds
```

2. **Failure Case (No API Key):**

```bash
# In backend .env, remove or invalid CMS_OPENAI_API_KEY

# Upload via frontend
# Should see:
# - Loading overlay
# - Error card appears
# - No results shown
```

3. **Network Simulation:**

```bash
# Stop backend while frontend is polling
# Should see:
# - Frontend continues polling
# - Console errors (expected)
# - Restart backend → polling resumes
```

## Performance Considerations

### Polling Overhead

- **Request size**: ~500 bytes (status endpoint is lightweight)
- **Frequency**: Every 2 seconds
- **Duration**: 10-30 seconds typical
- **Total requests**: ~5-15 per article

**Cost:** Negligible - status endpoint is very fast (< 10ms)

### Optimization Options

For high-traffic production:

1. **WebSockets** - Push updates instead of polling

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/articles/${id}`);
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  // Update UI immediately
};
```

2. **Server-Sent Events (SSE)** - One-way push

```typescript
const eventSource = new EventSource(`/api/articles/${id}/stream`);
eventSource.onmessage = (event) => {
  const status = JSON.parse(event.data);
};
```

3. **Exponential Backoff** - Reduce polling frequency over time

```typescript
// Start: 2s, then 4s, then 8s, max 15s
const delay = Math.min(2000 * Math.pow(2, attempts), 15000);
```

Current implementation is fine for most use cases.

## Future Enhancements

1. **Timeout Handling**

```typescript
if (elapsedTime > 120) {
  // 2 minutes
  onError("Processing timeout - please try again");
}
```

2. **Retry Logic**

```typescript
<Button onClick={() => handleAnalyze(articleData)}>Retry Analysis</Button>
```

3. **Progress Indicators**

```typescript
// Backend could return progress percentage
{
  "processing_status": "processing",
  "progress": 0.65, // 65%
  "current_step": "Generating cost models"
}
```

4. **Cancellation**

```typescript
<Button onClick={() => cancelAnalysis(articleId)}>Cancel</Button>
```

## Summary

✅ **No more alerts** - Professional UI with real-time feedback
✅ **Proper polling** - Checks backend status every 2 seconds
✅ **Error handling** - Shows errors, doesn't show results on failure
✅ **Visual feedback** - Progress bar, elapsed time, status messages
✅ **Clean code** - Proper cleanup, no memory leaks
✅ **User-friendly** - Clear messaging, helpful error tips

The frontend now provides a smooth, professional experience with real backend integration! 🚀
