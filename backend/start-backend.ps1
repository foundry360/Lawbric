# Backend startup script with Python detection
Write-Host "Starting Legal Discovery AI Backend..." -ForegroundColor Cyan

# Try to find Python
$pythonCmd = $null

# Check common Python locations (py launcher first for Windows)
$pythonPaths = @(
    "py",
    "python",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
    "C:\Python*\python.exe",
    "$env:PROGRAMFILES\Python*\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        if ($path -like "*\*") {
            # Wildcard path - need to resolve
            $resolved = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($resolved) {
                $testCmd = $resolved.FullName
            } else {
                continue
            }
        } else {
            $testCmd = $path
        }
        
        $version = & $testCmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version -like "Python *") {
            $pythonCmd = $testCmd
            Write-Host "Found Python: $pythonCmd" -ForegroundColor Green
            Write-Host "Version: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "`n❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Or if Python is installed, add it to your PATH environment variable." -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
$venvPath = Join-Path $PSScriptRoot "venv"
if (Test-Path $venvPath) {
    Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
    $pythonCmd = "python"  # Use venv's Python
} else {
    Write-Host "`n⚠️  No virtual environment found. Using system Python." -ForegroundColor Yellow
    Write-Host "Consider creating a venv: python -m venv venv" -ForegroundColor Yellow
}

# Check if dependencies are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow
try {
    $test = & $pythonCmd -c "import uvicorn; import fastapi" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Dependencies not installed!" -ForegroundColor Red
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        & $pythonCmd -m pip install -r requirements.txt
    } else {
        Write-Host "✅ Dependencies OK" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error checking dependencies: $_" -ForegroundColor Red
    exit 1
}

# Start the server
Write-Host "`nStarting backend server on http://localhost:9000..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

& $pythonCmd run.py

