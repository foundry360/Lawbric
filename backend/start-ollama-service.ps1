# PowerShell script to start the Ollama service
# Usage: .\start-ollama-service.ps1

Write-Host "Starting Ollama Service..." -ForegroundColor Green
Write-Host ""

# Check if Ollama is running
Write-Host "Checking Ollama connection..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -ErrorAction Stop
    Write-Host "✓ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot connect to Ollama at http://localhost:11434" -ForegroundColor Red
    Write-Host "  Make sure Ollama is installed and running." -ForegroundColor Yellow
    Write-Host "  Install: https://ollama.ai/download" -ForegroundColor Yellow
    Write-Host "  Then run: ollama pull llama3:8b" -ForegroundColor Yellow
    exit 1
}

# Check if model is available
Write-Host "Checking for llama3:8b model..." -ForegroundColor Yellow
$models = $ollamaCheck.models | Where-Object { $_.name -like "llama3:8b*" }
if ($models) {
    Write-Host "✓ llama3:8b model found" -ForegroundColor Green
} else {
    Write-Host "✗ llama3:8b model not found" -ForegroundColor Red
    Write-Host "  Run: ollama pull llama3:8b" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting Ollama Service on http://localhost:8001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Set environment variables (optional - defaults are already set in the script)
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3:8b"
$env:OLLAMA_SERVICE_PORT = "8001"

# Start the service
python ollama_service.py

