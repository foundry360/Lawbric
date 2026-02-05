# Ollama Docker Setup

Ollama is now configured to run in Docker alongside your other services!

## Quick Start

### 1. Start Ollama Service

```powershell
# Start just Ollama (if other services are already running)
docker-compose up -d ollama

# Or start all services including Ollama
docker-compose up -d
```

### 2. Pull the LLaMA 3 Model

Once Ollama container is running, pull the model:

```powershell
# Pull the model into the Docker container
docker exec legalai-ollama ollama pull llama3:8b
```

This will download the model (~4.7 GB) into the Docker volume. First time may take 5-15 minutes.

### 3. Verify Ollama is Working

```powershell
# Check if Ollama is running
docker ps | findstr ollama

# Test the model
docker exec legalai-ollama ollama run llama3:8b "Hello, how are you?"

# Check available models
docker exec legalai-ollama ollama list
```

### 4. Update Your Ollama Service Configuration

If your `ollama_service.py` is running **outside Docker** (locally), it should already work because Ollama is exposed on `localhost:11434`.

If your `ollama_service.py` is running **inside Docker**, update the environment variable:

```yaml
# In docker-compose.yml, add to backend service:
environment:
  - OLLAMA_HOST=ollama  # Use service name instead of localhost
```

Or set it when running:
```powershell
$env:OLLAMA_HOST="ollama"
python ollama_service.py
```

### 5. Test in Postman

Your Postman requests should now work! The service connects to `http://localhost:11434` which is forwarded from the Docker container.

---

## Docker Compose Commands

### Start Services
```powershell
# Start all services (including Ollama)
docker-compose up -d

# Start just Ollama
docker-compose up -d ollama

# Start with logs visible
docker-compose up ollama
```

### Stop Services
```powershell
# Stop all services
docker-compose down

# Stop just Ollama (keeps data)
docker-compose stop ollama
```

### View Logs
```powershell
# View Ollama logs
docker-compose logs ollama

# Follow logs in real-time
docker-compose logs -f ollama
```

### Manage Models
```powershell
# List installed models
docker exec legalai-ollama ollama list

# Pull a new model
docker exec legalai-ollama ollama pull llama3:8b

# Remove a model
docker exec legalai-ollama ollama rm llama3:8b

# Test a model
docker exec legalai-ollama ollama run llama3:8b "Your prompt here"
```

---

## Configuration

### Port Mapping
- **Host:** `localhost:11434`
- **Container:** `11434`
- Your service connects to `http://localhost:11434` (same as before)

### Data Persistence
- Models are stored in Docker volume: `ollama_data`
- Data persists even if container is stopped
- To remove all models: `docker volume rm legalai_ollama_data`

### Resource Requirements
- **RAM:** ~8GB recommended for llama3:8b
- **Disk:** ~5GB for the model
- **CPU:** Multi-core recommended

### GPU Support (Optional)

If you have an NVIDIA GPU, uncomment the GPU section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Then install NVIDIA Container Toolkit:
- Windows: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
- Linux: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

---

## Troubleshooting

### Container Won't Start
```powershell
# Check logs
docker-compose logs ollama

# Check if port is in use
netstat -ano | findstr :11434
```

### Model Not Found
```powershell
# Pull the model again
docker exec legalai-ollama ollama pull llama3:8b

# Verify it's there
docker exec legalai-ollama ollama list
```

### Service Can't Connect to Ollama
- Make sure Ollama container is running: `docker ps | findstr ollama`
- Check Ollama is accessible: `curl http://localhost:11434/api/tags`
- Verify port mapping in `docker-compose.yml`

### Out of Memory
- The model needs ~8GB RAM
- Close other applications
- Consider using a smaller model: `llama3:8b-instruct-q4_0` (quantized, smaller)

### Slow Responses
- First request loads model into memory (slower)
- Subsequent requests are faster
- Consider GPU support for better performance

---

## Development vs Production

### Development (`docker-compose.dev.yml`)
- Ollama runs as `legalai-ollama-dev`
- Same configuration, different container name

### Production (`docker-compose.yml`)
- Ollama runs as `legalai-ollama`
- Use this for production deployments

---

## Quick Checklist

- [ ] Ollama container is running: `docker ps | findstr ollama`
- [ ] Model is pulled: `docker exec legalai-ollama ollama list`
- [ ] Ollama API accessible: http://localhost:11434/api/tags
- [ ] Service can connect (test in Postman)
- [ ] Test query works

---

## Next Steps

1. ✅ Ollama is running in Docker
2. ✅ Model is downloaded
3. ✅ Test in Postman
4. ✅ Integrate with frontend

See `OLLAMA_SETUP.md` for frontend integration instructions.




