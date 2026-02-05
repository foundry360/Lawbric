# Troubleshooting Query Issues

## Quick Checks

### 1. Verify Services Are Running

```powershell
# Check Ollama container
docker ps | findstr ollama

# Check if service is running
Invoke-WebRequest -Uri http://localhost:8001/ -UseBasicParsing
```

### 2. Test Direct Connection

```powershell
# Test query directly
$body = '{"prompt":"What is 2+2?"}'
Invoke-RestMethod -Uri http://localhost:8001/query -Method POST -Body $body -ContentType "application/json"
```

### 3. Common Issues in Postman

#### Issue: "Connection refused" or "Could not get any response"
**Solution:**
- Make sure the service is running: `python backend/ollama_service.py`
- Check port 8001 is not blocked by firewall
- Verify URL is correct: `http://localhost:8001/query`

#### Issue: "Timeout" or Request takes too long
**Solution:**
- First request loads model into memory (can take 10-30 seconds)
- Increase timeout in Postman: Settings → General → Request timeout (set to 120 seconds)
- Try a shorter prompt first

#### Issue: "Cannot connect to Ollama"
**Solution:**
```powershell
# Check Ollama is running
docker ps | findstr ollama

# Restart Ollama if needed
docker restart legalai-ollama

# Verify Ollama API
docker exec legalai-ollama ollama list
```

#### Issue: "Model not found"
**Solution:**
```powershell
# Pull the model again
docker exec legalai-ollama ollama pull llama3:8b

# Verify it's there
docker exec legalai-ollama ollama list
```

#### Issue: CORS Error
**Solution:**
- The service already has CORS enabled
- Make sure you're using `http://localhost:8001/query` (not `https://`)
- Check browser console for specific CORS errors

#### Issue: Empty Response or 500 Error
**Solution:**
- Check service logs for errors
- Try a simpler prompt
- Verify Ollama is responding: `docker exec legalai-ollama ollama run llama3:8b "test"`

### 4. Check Service Logs

If the service is running in a terminal, check for error messages there.

### 5. Test with Different Prompts

Try these in Postman to isolate the issue:

**Simple:**
```json
{
  "prompt": "Hello"
}
```

**Medium:**
```json
{
  "prompt": "What is 2+2?"
}
```

**Longer:**
```json
{
  "prompt": "Explain artificial intelligence in one sentence"
}
```

### 6. Verify Postman Settings

1. **Method:** Must be `POST`
2. **URL:** `http://localhost:8001/query`
3. **Headers:**
   - `Content-Type: application/json`
4. **Body:**
   - Select "raw"
   - Select "JSON" from dropdown
   - Enter: `{"prompt": "your question here"}`
5. **Timeout:** Set to at least 120 seconds

### 7. Restart Everything

If nothing works, restart services:

```powershell
# Stop service (Ctrl+C in terminal where it's running)

# Restart Ollama
docker restart legalai-ollama

# Restart service
cd backend
python ollama_service.py
```

## Still Not Working?

Please provide:
1. **Exact error message** from Postman
2. **Status code** (if any)
3. **Response body** (if any)
4. **What happens** - does it timeout, error immediately, etc.?




