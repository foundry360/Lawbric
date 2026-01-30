# Ollama Integration - Quick Start

## 🚀 Quick Setup (3 Steps)

### 1. Start Ollama in Docker
```powershell
# Start Ollama service
docker-compose up -d ollama

# Pull the model (first time only, ~5-15 min)
docker exec legalai-ollama ollama pull llama3:8b

# Verify it works:
docker exec legalai-ollama ollama run llama3:8b "Hello"
```

**Note:** If you prefer to run Ollama locally instead of Docker, see `OLLAMA_INSTALL_WINDOWS.md`

### 2. Start the Ollama Service
```powershell
cd backend
pip install -r ollama_requirements.txt
python ollama_service.py
```

Or use the helper script:
```powershell
cd backend
.\start-ollama-service.ps1
```

### 3. Test It

**Option A: FastAPI Docs (Browser)**
- Visit: http://localhost:8001/docs
- Click `/query` → Try it out → Enter:
  ```json
  {
    "prompt": "What is artificial intelligence?"
  }
  ```

**Option B: Postman (Recommended)**
- Import: `backend/Ollama_Service.postman_collection.json`
- See: `OLLAMA_POSTMAN_TEST.md` for detailed instructions
- Just click **Send** on any pre-configured request!

---

## 📝 Connect to Your UI

Add this to your `ChatInterface.tsx` or create a test function:

```typescript
const queryOllama = async (prompt: string) => {
  const response = await fetch('http://localhost:8001/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  const data = await response.json();
  return data.response;
};
```

See `frontend/examples/ollama-integration-example.tsx` for complete examples.

---

## 📚 Full Documentation

See `OLLAMA_SETUP.md` for detailed instructions, troubleshooting, and next steps.

---

## ✅ Checklist

- [ ] Ollama installed
- [ ] `ollama pull llama3:8b` completed
- [ ] `ollama run llama3:8b "test"` works
- [ ] Service running on http://localhost:8001
- [ ] Test query works in browser
- [ ] Frontend connected

---

## 🔧 Troubleshooting

**Can't connect to Ollama?**
- Make sure Ollama is running: `ollama list`
- Check http://localhost:11434/api/tags

**Service won't start?**
- Install dependencies: `pip install -r ollama_requirements.txt`
- Check port 8001 is free

**Model not found?**
- Run: `ollama pull llama3:8b`

