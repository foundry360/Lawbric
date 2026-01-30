# Fixing "Sending..." Timeout in Postman

## The Problem

Postman shows "Sending..." and never completes. This happens because:
1. **First request is slow** - Model loads into memory (10-30 seconds)
2. **Postman default timeout** - Usually 0 (no timeout) but can be set too low
3. **Service timeout** - May need adjustment

## Solutions

### Solution 1: Increase Postman Timeout (Recommended)

1. **Open Postman Settings:**
   - Click the gear icon (⚙️) in top right
   - Or: File → Settings

2. **Set Request Timeout:**
   - Go to "General" tab
   - Find "Request timeout"
   - Set to **300 seconds** (5 minutes) or **0** (no timeout)
   - Click "Save"

3. **Try the request again**

### Solution 2: Use a Simpler Test First

Try this minimal request to verify it works:

```json
{
  "prompt": "Hi"
}
```

This should respond faster than longer prompts.

### Solution 3: Check Service is Processing

The service timeout has been increased to 300 seconds. If you see "Sending..." for more than 5 minutes, there might be another issue.

### Solution 4: Verify Ollama is Responding

Test Ollama directly:
```powershell
docker exec legalai-ollama ollama run llama3:8b "Hello"
```

If this works, the issue is likely just Postman timeout settings.

### Solution 5: Check Service Logs

If the service is running in a terminal window, check for error messages there.

## Quick Test

1. **Set Postman timeout to 300 seconds** (or 0 for no timeout)
2. **Use a simple prompt:**
   ```json
   {
     "prompt": "Hello"
   }
   ```
3. **Wait up to 30 seconds** for first response
4. **Subsequent requests should be faster** (2-5 seconds)

## Expected Behavior

- **First request:** 10-30 seconds (model loading)
- **Subsequent requests:** 2-5 seconds
- **Long prompts:** 5-15 seconds

If it takes longer than 5 minutes, there's likely an issue.

