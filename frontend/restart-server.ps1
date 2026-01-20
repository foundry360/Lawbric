# Restart Next.js dev server cleanly
Write-Host "Restarting Next.js dev server..." -ForegroundColor Cyan

# Step 1: Kill all Node.js processes
Write-Host "`nStopping all Node.js processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "✅ All Node processes stopped" -ForegroundColor Green

# Step 2: Clear Next.js cache
Write-Host "`nClearing Next.js cache..." -ForegroundColor Yellow
if (Test-Path .next) {
    Remove-Item -Recurse -Force .next
    Write-Host "✅ Cache cleared" -ForegroundColor Green
} else {
    Write-Host "No cache to clear" -ForegroundColor Yellow
}

# Step 3: Verify port 3000 is free
Write-Host "`nChecking port 3000..." -ForegroundColor Yellow
$portCheck = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($portCheck) {
    Write-Host "⚠️ Port 3000 is still in use. Waiting 3 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} else {
    Write-Host "✅ Port 3000 is free" -ForegroundColor Green
}

# Step 4: Start the server
Write-Host "`nStarting Next.js dev server..." -ForegroundColor Cyan
Write-Host "Run: npm run dev" -ForegroundColor Yellow



