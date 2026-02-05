#!/bin/bash
# GPU Setup Script for WSL2
# Run this script in WSL2 (Ubuntu-22.04) terminal, not PowerShell

set -e

echo "=========================================="
echo "GPU Setup for Docker on WSL2"
echo "=========================================="

# Check if running in WSL2
if [ ! -f /proc/version ] || ! grep -q "microsoft" /proc/version; then
    echo "WARNING: This script is designed for WSL2. Continuing anyway..."
fi

# Step 1: Add NVIDIA package repositories
echo ""
echo "Step 1: Adding NVIDIA package repositories..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Step 2: Update package list
echo ""
echo "Step 2: Updating package list..."
sudo apt-get update

# Step 3: Install NVIDIA Container Toolkit
echo ""
echo "Step 3: Installing NVIDIA Container Toolkit..."
sudo apt-get install -y nvidia-container-toolkit

# Step 4: Configure Docker to use NVIDIA runtime
echo ""
echo "Step 4: Configuring Docker..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Step 5: Verify installation
echo ""
echo "Step 5: Verifying installation..."
if command -v nvidia-container-toolkit &> /dev/null; then
    echo "✓ NVIDIA Container Toolkit installed"
    nvidia-container-toolkit --version
else
    echo "✗ NVIDIA Container Toolkit not found"
    exit 1
fi

# Step 6: Test GPU access
echo ""
echo "Step 6: Testing GPU access in Docker..."
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "✓ GPU access working in Docker"
    docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
else
    echo "⚠ GPU access test failed. This might be normal if:"
    echo "  - NVIDIA drivers aren't installed in Windows"
    echo "  - Docker Desktop isn't using WSL2 backend"
    echo "  - GPU isn't accessible from WSL2"
    echo ""
    echo "You can still proceed - the Ollama service will use CPU if GPU isn't available."
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart Docker Desktop (if needed)"
echo "2. Recreate containers:"
echo "   docker-compose -f docker-compose.dev.yml up -d --force-recreate ollama-service"
echo "3. Check GPU status:"
echo "   docker logs legalai-ollama-service-dev | grep -A 10 'GPU Status'"
echo "   or visit: http://localhost:8002/health"




