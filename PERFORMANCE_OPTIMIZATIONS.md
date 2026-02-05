# Performance Optimization Options for LLM Queries

## Current Performance Issues
- Queries taking 5-10 minutes
- Model: llama3.1:8b (4.9 GB, running on CPU)
- Sending up to 3 documents with 5000 chars each
- Max response: 1024 tokens
- Context window: 2048 tokens

## Quick Wins (Immediate Improvements)

### Option 1: Reduce Document Context (EASIEST - Do This First!)
**Impact:** 50-70% faster, minimal quality loss
- Currently: 5000 chars per document
- Change to: 2000 chars per document
- **File:** `backend/app/api/v1/queries.py` line 145

### Option 2: Use Smaller Model (BIGGEST IMPACT)
**Impact:** 3-5x faster, slight quality reduction
- Current: `llama3.1:8b` (4.9 GB)
- Switch to: `llama3.1:3b` (2.0 GB) - Much faster on CPU
- Or: `llama3.2:1b` (700 MB) - Very fast, good for simple queries
- **File:** `docker-compose.dev.yml` line 132

### Option 3: Reduce Response Length
**Impact:** 20-30% faster
- Currently: 1024 tokens max
- Change to: 512 tokens (still plenty for most answers)
- **File:** `backend/ollama_service.py` line 975

### Option 4: Limit Documents Sent
**Impact:** 30-40% faster per document
- Currently: Up to 3 documents
- Change to: 1-2 documents max
- **File:** `backend/app/api/v1/queries.py` line 140

### Option 5: Enable GPU (If Available)
**Impact:** 5-10x faster
- Uncomment GPU section in `docker-compose.dev.yml`
- Requires NVIDIA GPU with Docker support

## Recommended Quick Fix (Do All of These):

1. **Reduce document text:** 5000 → 2000 chars
2. **Switch to smaller model:** llama3.1:8b → llama3.1:3b
3. **Reduce response tokens:** 1024 → 512
4. **Limit documents:** 3 → 1 document

**Expected Result:** Queries should complete in 30-60 seconds instead of 5-10 minutes!

## Implementation Steps:

### Step 1: Pull Smaller Model
```powershell
docker exec legalai-ollama-dev ollama pull llama3.1:3b
```

### Step 2: Update docker-compose.dev.yml
Change line 132:
```yaml
- OLLAMA_MODEL=llama3.1:3b  # Changed from llama3.1:8b
```

### Step 3: Update Code (see fixes below)

### Step 4: Restart Services
```powershell
docker-compose -f docker-compose.dev.yml restart ollama-service backend
```




