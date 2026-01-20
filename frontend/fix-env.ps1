# Fix environment variables not loading
Write-Host "Fixing Next.js environment variables..." -ForegroundColor Cyan

# Step 1: Clear Next.js cache
if (Test-Path .next) {
    Write-Host "Removing .next cache..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .next
    Write-Host "✅ Cache cleared" -ForegroundColor Green
} else {
    Write-Host "No .next cache found" -ForegroundColor Yellow
}

# Step 2: Verify .env.local exists
if (Test-Path .env.local) {
    Write-Host "✅ .env.local found" -ForegroundColor Green
    Write-Host "Contents:" -ForegroundColor Cyan
    Get-Content .env.local | Select-String "SUPABASE"
} else {
    Write-Host "❌ .env.local NOT FOUND!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Ready to restart dev server" -ForegroundColor Green
Write-Host "Run: npm run dev" -ForegroundColor Cyan



