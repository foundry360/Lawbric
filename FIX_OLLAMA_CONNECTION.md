# Fix Ollama Connection Issue

## The Problem
The ollama-service is trying to connect to `localhost:11434` instead of `ollama:11434` (the Docker service name).

## Quick Fix - Run These Commands:

### 1. Check if containers are running:
```powershell
docker ps
```

### 2. Check the ollama-service environment:
```powershell
docker exec legalai-ollama-service env | findstr OLLAMA
```

You should see:
```
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_SERVICE_PORT=8002
OLLAMA_MODEL=llama3.1:8b
```

### 3. If OLLAMA_BASE_URL is NOT set or is wrong, restart the service:
```powershell
docker-compose restart ollama-service
```

### 4. Verify the service is using the correct URL:
```powershell
curl http://localhost:8002/
```

Should show: `"ollama_url":"http://ollama:11434"` (NOT localhost)

### 5. Check if Ollama container is running and has the model:
```powershell
docker exec legalai-ollama ollama list
```

Should show `llama3.1:8b` in the list.

### 6. If the model is missing, pull it:
```powershell
docker exec legalai-ollama ollama pull llama3.1:8b
```

### 7. Test the connection:
```powershell
$body = @{prompt = "What is 2+2?"} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8002/query -Method POST -Body $body -ContentType "application/json"
```

## If Still Not Working:

### Rebuild the ollama-service container:
```powershell
docker-compose up -d --build ollama-service
```

### Check logs:
```powershell
docker logs legalai-ollama-service --tail 50
docker logs legalai-ollama --tail 50
```

## The Fix Applied
The code in `backend/ollama_service.py` now properly uses the `OLLAMA_BASE_URL` environment variable when set in docker-compose.yml. After restarting the container, it should connect to `ollama:11434` instead of `localhost:11434`.




