# Ollama LLaMA 3 Integration Guide

This guide shows you how to set up a local LLaMA 3 model using Ollama and connect it to your LegalAI application's query panel.

## Overview

The integration consists of:
1. **Ollama** - Runs the LLaMA 3 model locally
2. **Ollama Service** - A minimal Python backend that connects to Ollama
3. **Frontend** - Your existing query panel UI

---

## Step 1: Install and Run Ollama

### Windows

1. **Download Ollama:**
   - Visit https://ollama.ai/download
   - Download the Windows installer
   - Run the installer

2. **Verify Installation:**
   ```powershell
   ollama --version
   ```

3. **Pull the llama3:8b model:**
   ```powershell
   ollama pull llama3:8b
   ```
   
   This will download the model (approximately 4.7 GB). The first time may take a while.

4. **Test the model:**
   ```powershell
   ollama run llama3:8b "Hello, how are you?"
   ```

5. **Keep Ollama running:**
   - Ollama runs as a service on Windows
   - It will be available at `http://localhost:11434` by default
   - You can verify it's running by visiting: http://localhost:11434/api/tags

### macOS / Linux

1. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull the model:**
   ```bash
   ollama pull llama3:8b
   ```

3. **Test the model:**
   ```bash
   ollama run llama3:8b "Hello, how are you?"
   ```

---

## Step 2: Set Up the Ollama Service

The Ollama service is a minimal Python backend that acts as a bridge between your frontend and Ollama.

### Install Dependencies

Navigate to the `backend` directory and install the minimal requirements:

```powershell
cd backend
pip install -r ollama_requirements.txt
```

Or if you prefer to install only what's needed:
```powershell
pip install fastapi uvicorn pydantic httpx
```

### Run the Service

```powershell
python ollama_service.py
```

The service will start on **http://localhost:8001** by default.

You can verify it's running by visiting:
- http://localhost:8001/ - Should show service status
- http://localhost:8001/docs - FastAPI interactive docs

### Configuration (Optional)

You can customize the service using environment variables:

```powershell
# Windows PowerShell
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama3:8b"
$env:OLLAMA_SERVICE_PORT="8001"
python ollama_service.py
```

```bash
# Linux/macOS
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3:8b"
export OLLAMA_SERVICE_PORT="8001"
python ollama_service.py
```

---

## Step 3: Test the Service

### Using curl (PowerShell)

```powershell
$body = @{
    prompt = "What is artificial intelligence?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/query" -Method POST -Body $body -ContentType "application/json"
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8001/query",
    json={"prompt": "What is artificial intelligence?"}
)

print(response.json()["response"])
```

### Using the FastAPI Docs

1. Visit http://localhost:8001/docs
2. Click on `/query` endpoint
3. Click "Try it out"
4. Enter:
   ```json
   {
     "prompt": "What is artificial intelligence?"
   }
   ```
5. Click "Execute"

---

## Step 4: Connect Your Frontend Query Panel

### Option A: Direct API Call (Simplest)

Modify your `ChatInterface.tsx` or wherever you handle queries to call the Ollama service:

```typescript
// Example: Add this function to test the Ollama service
const testOllamaQuery = async (prompt: string) => {
  try {
    const response = await fetch('http://localhost:8001/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.response; // The model's response text
  } catch (error) {
    console.error('Error calling Ollama service:', error);
    throw error;
  }
};

// Usage in your component:
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!question.trim() || loading) return;

  setLoading(true);
  try {
    const answer = await testOllamaQuery(question.trim());
    // Display the answer in your UI
    console.log('Model response:', answer);
    // TODO: Update your UI state with the answer
  } catch (error: any) {
    console.error('Failed to get response:', error);
    alert(`Error: ${error.message}`);
  } finally {
    setLoading(false);
  }
};
```

### Option B: Add to API Client

Add a function to `frontend/lib/api.ts`:

```typescript
// Add to your api.ts file
export const ollamaApi = {
  query: async (prompt: string): Promise<string> => {
    const response = await fetch('http://localhost:8001/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to query Ollama');
    }

    const data = await response.json();
    return data.response;
  },
};
```

Then use it in your component:

```typescript
import { ollamaApi } from '@/lib/api';

// In your component:
const answer = await ollamaApi.query(question.trim());
```

---

## Troubleshooting

### Ollama Service Can't Connect to Ollama

**Error:** `Cannot connect to Ollama at http://localhost:11434`

**Solution:**
1. Make sure Ollama is running: `ollama list`
2. Check if Ollama is on a different port
3. Verify Ollama is accessible: Visit http://localhost:11434/api/tags

### Model Not Found

**Error:** `model 'llama3:8b' not found`

**Solution:**
```powershell
ollama pull llama3:8b
```

### CORS Errors in Browser

**Error:** CORS policy blocking requests

**Solution:**
The service already has CORS enabled for all origins. If you still see errors:
1. Check that the service is running
2. Verify the URL in your frontend code matches the service URL
3. Check browser console for specific error messages

### Timeout Errors

**Error:** Request timed out

**Solution:**
- The model may be processing a large prompt
- Try a shorter prompt first
- Check your system resources (RAM, CPU)
- The timeout is set to 120 seconds by default

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
Change the port:
```powershell
$env:OLLAMA_SERVICE_PORT="8002"
python ollama_service.py
```

---

## System Instruction

The service automatically wraps every user query with a fixed system instruction for legal document analysis. This instruction:

- **Cannot be modified by users** - It's hardcoded in the service
- **Is prepended to every query** - Automatically added before the user's prompt
- **Enforces strict rules:**
  - Use ONLY the text explicitly provided
  - Extract only the factual statements or answers made by the witness
  - Output ONLY the statements exactly as they appear in the text
  - Format each statement as: "- Page X: \"[text]\""
  - Do NOT include questions, commentary, summaries, advice, or conversational phrases
  - Do NOT infer, interpret, conclude, or speculate
  - If no factual statements are present, respond exactly: "Not found in the provided text."

The system instruction is defined in `backend/ollama_service.py` as the `SYSTEM_INSTRUCTION` constant. Users don't need to include it in their queries - it's automatically added.

## Next Steps

Once you've verified the basic connection works, you can expand this service to:

1. **Add Document Context:** Pass relevant document text with queries
2. **Add Conversation History:** Maintain context across multiple queries
3. **Add Streaming:** Stream responses in real-time for better UX
4. **Add Authentication:** Secure the endpoint
5. **Integrate with Existing Backend:** Merge this into your main FastAPI backend

---

## File Structure

```
LegalAI/
├── backend/
│   ├── ollama_service.py          # The minimal Ollama service
│   └── ollama_requirements.txt    # Minimal dependencies
└── OLLAMA_SETUP.md                # This file
```

---

## Quick Start Checklist

- [ ] Install Ollama
- [ ] Pull llama3:8b model: `ollama pull llama3:8b`
- [ ] Test Ollama: `ollama run llama3:8b "Hello"`
- [ ] Install Python dependencies: `pip install -r ollama_requirements.txt`
- [ ] Run the service: `python ollama_service.py`
- [ ] Test the service: Visit http://localhost:8001/docs
- [ ] Update frontend to call the service
- [ ] Test end-to-end from your UI

---

## Notes

- The service runs on port **8001** by default to avoid conflicts with your main backend (port 8000)
- Ollama runs on port **11434** by default
- The model requires approximately **8GB RAM** to run smoothly
- First response may be slower as the model loads into memory
- This is a minimal implementation - no authentication, no database, no document processing

