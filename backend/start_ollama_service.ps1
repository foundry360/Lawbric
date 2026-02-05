Write-Host "Starting Ollama Service on port 8002..." -ForegroundColor Cyan
Write-Host ""
Set-Location $PSScriptRoot
$env:OLLAMA_SERVICE_PORT = "8002"
python ollama_service.py

