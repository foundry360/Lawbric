# Script to restart the backend server
Write-Host "Restarting Legal Discovery AI Backend..." -ForegroundColor Cyan

# Find and kill existing backend processes on port 9001
Write-Host "`nChecking for existing processes on port 9001..." -ForegroundColor Yellow
$processes = Get-NetTCPConnection -LocalPort 9001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    Write-Host "Found processes using port 9001: $($processes -join ', ')" -ForegroundColor Yellow
    foreach ($pid in $processes) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Stopping process $pid ($($proc.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
        } catch {
            Write-Host "Could not stop process $pid: $_" -ForegroundColor Red
        }
    }
    Write-Host "Waiting for port to be released..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
} else {
    Write-Host "No processes found on port 9001" -ForegroundColor Green
}

# Verify port is free
$stillInUse = Get-NetTCPConnection -LocalPort 9001 -ErrorAction SilentlyContinue
if ($stillInUse) {
    Write-Host "`n⚠️  WARNING: Port 9001 is still in use!" -ForegroundColor Red
    Write-Host "You may need to manually stop the process or restart your computer." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ Port 9001 is now free" -ForegroundColor Green
}

# Start the backend
Write-Host "`nStarting backend server..." -ForegroundColor Cyan
& "$PSScriptRoot\start-backend.ps1"


