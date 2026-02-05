# Installing Ollama on Windows

## Quick Installation Steps

### Step 1: Download Ollama

1. **Visit the Ollama website:**
   - Go to: https://ollama.ai/download
   - Or direct link: https://ollama.ai/download/windows

2. **Download the Windows installer:**
   - Click "Download for Windows"
   - Save the installer file (e.g., `OllamaSetup.exe`)

### Step 2: Install Ollama

1. **Run the installer:**
   - Double-click the downloaded `OllamaSetup.exe`
   - Follow the installation wizard
   - Ollama will install and start automatically as a Windows service

2. **Verify installation:**
   - Open a **new** PowerShell or Command Prompt window
   - Run: `ollama --version`
   - You should see a version number

### Step 3: Pull the LLaMA 3 Model

1. **Open PowerShell or Command Prompt**

2. **Pull the model:**
   ```powershell
   ollama pull llama3:8b
   ```
   
   This will download the model (approximately 4.7 GB). 
   - First time may take 5-15 minutes depending on your internet speed
   - You'll see progress as it downloads

3. **Verify the model is installed:**
   ```powershell
   ollama list
   ```
   
   You should see `llama3:8b` in the list

### Step 4: Test Ollama

1. **Test the model:**
   ```powershell
   ollama run llama3:8b "Hello, how are you?"
   ```
   
   You should get a response from the model

2. **Verify Ollama API is accessible:**
   - Open your browser
   - Visit: http://localhost:11434/api/tags
   - You should see JSON with your installed models

### Step 5: Test Your Service Again

Once Ollama is running:

1. **Make sure your Ollama service is running:**
   ```powershell
   cd backend
   python ollama_service.py
   ```

2. **Test in Postman:**
   - Try the "Health Check" request again
   - Then try a "Query" request
   - Should work now!

---

## Troubleshooting

### "ollama is not recognized"
**Problem:** Ollama is not in your PATH or you need to restart your terminal

**Solution:**
1. Close and reopen your PowerShell/Command Prompt
2. If still not working, add Ollama to PATH:
   - Usually installed at: `C:\Users\<YourUsername>\AppData\Local\Programs\Ollama`
   - Add to PATH in Windows Settings → System → Advanced → Environment Variables

### Ollama service not starting
**Problem:** Ollama service didn't start automatically

**Solution:**
1. Open Services (Win + R → `services.msc`)
2. Find "Ollama" service
3. Right-click → Start
4. Set to "Automatic" startup if needed

### Port 11434 already in use
**Problem:** Another service is using port 11434

**Solution:**
1. Check what's using the port:
   ```powershell
   netstat -ano | findstr :11434
   ```
2. Stop the conflicting service or change Ollama's port

### Model download is slow
**Problem:** Large file (4.7 GB) takes time to download

**Solution:**
- This is normal! Be patient
- Check your internet connection
- The download will resume if interrupted

### "Model not found" after installation
**Problem:** Model wasn't fully downloaded

**Solution:**
```powershell
ollama pull llama3:8b
```
Wait for it to complete (you'll see "success" message)

---

## Quick Checklist

- [ ] Downloaded Ollama installer
- [ ] Installed Ollama
- [ ] Opened new terminal window
- [ ] Verified: `ollama --version` works
- [ ] Pulled model: `ollama pull llama3:8b`
- [ ] Verified model: `ollama list` shows llama3:8b
- [ ] Tested model: `ollama run llama3:8b "test"`
- [ ] Verified API: http://localhost:11434/api/tags works
- [ ] Tested service in Postman

---

## Alternative: Check if Ollama is Already Installed

Sometimes Ollama is installed but not in PATH. Try:

1. **Check common installation locations:**
   ```powershell
   # Try these paths:
   & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
   & "C:\Program Files\Ollama\ollama.exe" --version
   ```

2. **If found, add to PATH or use full path:**
   ```powershell
   $env:PATH += ";$env:LOCALAPPDATA\Programs\Ollama"
   ollama --version
   ```

---

## Next Steps After Installation

Once Ollama is installed and running:

1. ✅ Your Postman requests should work
2. ✅ The service at http://localhost:8001 should connect to Ollama
3. ✅ You can integrate it into your frontend

See `OLLAMA_SETUP.md` for integration instructions.




