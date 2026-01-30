# Testing Ollama Service with Postman

This guide shows you how to test the Ollama service using Postman.

## Prerequisites

1. **Ollama must be running** with the llama3:8b model
   ```powershell
   ollama pull llama3:8b
   ollama run llama3:8b "test"
   ```

2. **Ollama service must be running**
   ```powershell
   cd backend
   python ollama_service.py
   ```
   
   You should see: `Uvicorn running on http://0.0.0.0:8001`

---

## Test 1: Health Check (GET Request)

### Request Setup
- **Method:** `GET`
- **URL:** `http://localhost:8001/`
- **Headers:** None required

### Expected Response
```json
{
  "service": "Ollama Query Service",
  "status": "running",
  "ollama_url": "http://localhost:11434",
  "model": "llama3:8b"
}
```

### Steps in Postman
1. Open Postman
2. Create a new request
3. Set method to **GET**
4. Enter URL: `http://localhost:8001/`
5. Click **Send**

---

## Test 2: Query Endpoint (POST Request)

### Request Setup
- **Method:** `POST`
- **URL:** `http://localhost:8001/query`
- **Headers:**
  - `Content-Type: application/json`
- **Body:** (raw JSON)
  ```json
  {
    "prompt": "What is artificial intelligence?"
  }
  ```

### Expected Response
```json
{
  "response": "Artificial intelligence (AI) is a branch of computer science..."
}
```

### Steps in Postman

1. **Create New Request**
   - Click "New" → "HTTP Request"
   - Or use the "+" button

2. **Set Method**
   - Select **POST** from the dropdown

3. **Enter URL**
   - `http://localhost:8001/query`

4. **Set Headers**
   - Go to the **Headers** tab
   - Add header:
     - Key: `Content-Type`
     - Value: `application/json`

5. **Set Body**
   - Go to the **Body** tab
   - Select **raw**
   - Select **JSON** from the dropdown (on the right)
   - Enter this JSON:
     ```json
     {
       "prompt": "What is artificial intelligence?"
     }
     ```

6. **Send Request**
   - Click the blue **Send** button

7. **View Response**
   - The response will appear in the bottom panel
   - You should see a JSON object with a `response` field containing the model's answer

---

## Test 3: More Example Queries

Try these prompts in the body:

### Simple Question
```json
{
  "prompt": "Explain quantum computing in simple terms"
}
```

### Legal Question (for your use case)
```json
{
  "prompt": "What are the key elements of a contract?"
}
```

### Short Question
```json
{
  "prompt": "What is 2+2?"
}
```

### Longer Question
```json
{
  "prompt": "Write a brief summary of the history of artificial intelligence, including key milestones and important figures."
}
```

---

## Troubleshooting in Postman

### Error: "Could not get any response"
**Problem:** Service is not running
**Solution:**
1. Check if service is running: `python ollama_service.py`
2. Verify it's on port 8001
3. Check for error messages in the terminal

### Error: "Connection refused"
**Problem:** Service not accessible
**Solution:**
- Make sure the service started successfully
- Check firewall settings
- Verify URL is correct: `http://localhost:8001/query`

### Error: 503 "Cannot connect to Ollama"
**Problem:** Ollama is not running
**Solution:**
```powershell
# Check if Ollama is running
ollama list

# If not, start Ollama (it should run as a service)
# Then verify:
curl http://localhost:11434/api/tags
```

### Error: 400 "Prompt cannot be empty"
**Problem:** Empty or missing prompt in body
**Solution:**
- Make sure body is set to "raw" and "JSON"
- Verify the JSON has a `prompt` field with a non-empty string

### Error: 504 "Request timed out"
**Problem:** Model is taking too long to respond
**Solution:**
- Try a shorter prompt
- Check system resources (RAM, CPU)
- The timeout is 120 seconds

### Response is empty or malformed
**Problem:** Ollama returned unexpected format
**Solution:**
- Check Ollama logs
- Verify model is loaded: `ollama list`
- Try pulling the model again: `ollama pull llama3:8b`

---

## Postman Collection (Quick Import)

**🎉 Ready-to-use collection included!**

1. **Import the Collection**
   - Open Postman
   - Click **Import** button (top left)
   - Select **File** tab
   - Choose: `backend/Ollama_Service.postman_collection.json`
   - Click **Import**

2. **Use the Pre-configured Requests**
   - You'll see a collection called "Ollama Service"
   - It includes:
     - ✅ Health Check (GET)
     - ✅ Query - Simple Question
     - ✅ Query - Legal Question
     - ✅ Query - Short Question
     - ✅ Query - Long Question

3. **Just Click Send!**
   - All requests are pre-configured
   - Make sure the service is running first
   - Click **Send** on any request to test

---

## Quick Test Checklist

- [ ] Ollama is running (`ollama list` works)
- [ ] Service is running (`http://localhost:8001/` returns status)
- [ ] Health check works (GET `/`)
- [ ] Query endpoint works (POST `/query`)
- [ ] Response contains model answer
- [ ] Error handling works (test with empty prompt)

---

## Example Postman Screenshot Description

When set up correctly, you should see:

**Request Section:**
- Method: POST
- URL: http://localhost:8001/query
- Headers: Content-Type: application/json
- Body (raw JSON): `{ "prompt": "..." }`

**Response Section:**
- Status: 200 OK
- Time: ~2-10 seconds (depending on prompt)
- Body: `{ "response": "..." }` with the model's answer

---

## Next Steps

Once Postman tests work:
1. ✅ Service is working correctly
2. ✅ You can integrate it into your frontend
3. ✅ See `frontend/examples/ollama-integration-example.tsx` for UI integration

