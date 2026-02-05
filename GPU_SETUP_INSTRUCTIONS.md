# GPU Setup Instructions for WSL2

## Quick Setup (Run these commands in WSL2)

**Step 1: Open WSL2 Terminal**
- Press `Windows Key` and type "Ubuntu" or "WSL"
- Click on "Ubuntu-22.04" (or your WSL2 distribution)
- This opens a Linux terminal window

**Step 2: Navigate to your project**
```bash
cd /mnt/c/LegalAI
```

**Step 3: Run the setup script**
```bash
sudo ./setup_gpu_wsl2.sh
```
(Enter your WSL2 password when prompted)

**Step 4: After the script completes, restart Docker Desktop**
- Right-click Docker Desktop icon in system tray
- Click "Restart"

**Step 5: Recreate the ollama-service container**
In PowerShell (back in Windows):
```powershell
docker-compose -f docker-compose.dev.yml up -d --force-recreate ollama-service
```

**Step 6: Check GPU status**
```powershell
docker logs legalai-ollama-service-dev --tail 50
```

Or visit: http://localhost:8002/health

---

## Alternative: Manual Installation (if script fails)

If the script doesn't work, run these commands one by one in WSL2:

```bash
# 1. Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Update and install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 4. Verify
nvidia-container-toolkit --version
```

---

## Troubleshooting

**If you get "systemctl: command not found"**
- This is normal in WSL2. Docker Desktop manages the Docker daemon.
- Skip the `systemctl restart docker` command.
- Just restart Docker Desktop from Windows instead.

**If GPU test fails**
- This is OK! The Ollama service will fall back to CPU.
- GPU will work if you have NVIDIA drivers installed in Windows and Docker Desktop is using WSL2 backend.



