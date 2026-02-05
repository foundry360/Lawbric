# GPU Setup for Ollama Service on Windows WSL2

This guide explains how to enable GPU access for the Ollama service running in Docker on Windows with WSL2.

## Prerequisites

1. **NVIDIA GPU** with compatible drivers
2. **WSL2** installed and configured
3. **NVIDIA Container Toolkit** installed in WSL2
4. **Docker Desktop** with WSL2 backend enabled

## Setup Steps

### 1. Install NVIDIA Container Toolkit in WSL2

**IMPORTANT**: These commands must be run in WSL2 (Ubuntu-22.04), NOT in PowerShell!

**Option A: Use the setup script (Recommended)**

1. Open WSL2 terminal (Ubuntu-22.04) - you can do this by:
   - Opening Ubuntu-22.04 from Start Menu, OR
   - Running `wsl -d Ubuntu-22.04` in PowerShell

2. Navigate to the project directory:
   ```bash
   cd /mnt/c/LegalAI
   ```

3. Run the setup script:
   ```bash
   chmod +x setup_gpu_wsl2.sh
   ./setup_gpu_wsl2.sh
   ```

**Option B: Manual installation**

Open WSL2 terminal (Ubuntu-22.04) and run:

```bash
# Add NVIDIA package repositories (updated method)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 2. Verify GPU Access

Test GPU access in Docker:

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

You should see your GPU information. If not, check:
- NVIDIA drivers are installed in Windows
- WSL2 can see the GPU: `nvidia-smi` (if installed in WSL2)
- Docker Desktop is using WSL2 backend

### 3. Configure Docker Compose

The `docker-compose.dev.yml` file is already configured with:

- `deploy.resources.reservations.devices` with `driver: nvidia` and `capabilities: [gpu]`
- Environment variables: `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility`
- Volume mount for WSL2 NVIDIA libraries: `/usr/lib/wsl/lib:/usr/lib/wsl/lib:ro`

### 4. Start Services

```bash
docker-compose -f docker-compose.dev.yml up -d ollama-service
```

### 5. Verify GPU Status

Check the logs for GPU status:

```bash
docker logs legalai-ollama-service-dev | grep -A 10 "GPU Status"
```

Or check the health endpoint:

```bash
curl http://localhost:8002/health
```

## GPU Status Logging

The service automatically logs GPU status on startup:

```
============================================================
GPU Status Check
============================================================
PyTorch available: True
CUDA available: True
Device count: 1
Device name: NVIDIA GeForce RTX 4090
VRAM Total: 24.00 GB
VRAM Used: 0.50 GB
VRAM Free: 23.50 GB
============================================================
```

## Fail-Fast Mode

To require GPU and exit if not available, set:

```bash
export REQUIRE_GPU=true
```

Or in `docker-compose.dev.yml`:

```yaml
environment:
  - REQUIRE_GPU=true
```

## Troubleshooting

### Issue: "libnvidia-ml.so: cannot open shared object file"

**Solution**: The NVIDIA libraries are mounted from WSL2. Ensure:
1. WSL2 has NVIDIA drivers accessible
2. The volume mount `/usr/lib/wsl/lib:/usr/lib/wsl/lib:ro` is correct
3. Libraries exist: `ls /usr/lib/wsl/lib/libnvidia*`

### Issue: "No GPU detected"

**Solution**:
1. Verify NVIDIA Container Toolkit is installed: `nvidia-container-toolkit --version`
2. Test GPU access: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
3. Check Docker Desktop settings: Use WSL2 backend
4. Restart Docker Desktop

### Issue: "torch.cuda.is_available() returns False"

**Solution**:
1. PyTorch may need CUDA-specific build: The current setup uses CPU PyTorch by default
2. For GPU PyTorch, update `ollama_requirements.txt`:
   ```
   torch>=2.0.0+cu118 --index-url https://download.pytorch.org/whl/cu118
   ```
3. Rebuild the container: `docker-compose -f docker-compose.dev.yml build ollama-service`

## Notes

- The Ollama service itself (the LLM runtime) uses GPU automatically if available
- The `ollama-service` wrapper only detects and logs GPU status - it doesn't directly use GPU
- GPU detection uses PyTorch and pynvml libraries (gracefully degrades if not available)
- For production, consider using GPU-specific PyTorch builds

