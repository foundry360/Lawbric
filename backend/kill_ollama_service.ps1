# Kill all Python processes running ollama_service.py
Write-Host "Finding and killing ollama_service processes..." -ForegroundColor Yellow

$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    $cmdLine -like "*ollama_service*"
}

if ($processes) {
    foreach ($proc in $processes) {
        Write-Host "Killing PID $($proc.Id)..." -ForegroundColor Red
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Done. Waiting 2 seconds..." -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "No ollama_service processes found." -ForegroundColor Green
}

# Check if port 8001 is free
$portCheck = netstat -ano | findstr ":8001"
if ($portCheck) {
    Write-Host "`nWARNING: Port 8001 is still in use:" -ForegroundColor Red
    $portCheck
} else {
    Write-Host "`nPort 8001 is now free!" -ForegroundColor Green
}




