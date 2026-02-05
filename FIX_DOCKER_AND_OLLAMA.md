# Fix Docker and Ollama Connection

## THE PROBLEM:
1. **Docker Desktop Service is stopped** - Docker commands can't connect
2. **Local Python process is running** ollama_service.py instead of Docker container
3. That's why it's using `localhost:11434` instead of `ollama:11434`

## SOLUTION - Follow These Steps:

### Step 1: Stop Local Python Process
```powershell
# Find and stop any local Python processes running ollama_service
Get-Process python | Where-Object {$_.Path -notlike "*venv*"} | Stop-Process -Force
```

### Step 2: Fully Restart Docker Desktop
1. **Right-click Docker Desktop icon in system tray** (bottom right)
2. Click **"Quit Docker Desktop"**
3. Wait 10 seconds
4. **Start Docker Desktop** from Start Menu
5. **Wait for it to fully start** (whale icon stops animating)

### Step 3: Verify Docker is Working
```powershell
docker ps
```
Should show your containers (or empty list, but NO errors)

### Step 4: Start All Containers
```powershell
cd C:\LegalAI
docker-compose up -d
```

### Step 5: Verify Ollama Service is in Docker
```powershell
docker ps --filter "name=ollama-service"
```

Should show the container running.

### Step 6: Check Environment Variable
```powershell
docker exec legalai-ollama-service env | findstr OLLAMA_BASE_URL
```

Should show: `OLLAMA_BASE_URL=http://ollama:11434`

### Step 7: Test the Service
```powershell
curl http://localhost:8002/
```

Should show: `"ollama_url":"http://ollama:11434"` (NOT localhost!)

### Step 8: Test a Query
```powershell
$body = @{prompt = "What is 2+2?"} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8002/query -Method POST -Body $body -ContentType "application/json"
```

## If Docker Still Won't Start:

1. **Check Windows Services:**
   ```powershell
   Get-Service | Where-Object {$_.DisplayName -like "*Docker*"}
   ```

2. **Try restarting Docker Desktop Service manually:**
   - Open Services (Win+R → `services.msc`)
   - Find "Docker Desktop Service"
   - Right-click → Restart

3. **If that doesn't work, restart your computer**

## Key Point:
The service MUST run in Docker to use `ollama:11434`. If it's running locally (Python process), it will use `localhost:11434` and won't be able to connect to the Ollama container.




