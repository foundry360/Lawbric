@echo off
echo Starting Legal Discovery AI Frontend...
echo.

cd frontend

REM Check if node_modules exists
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

REM Start the dev server
call npm run dev

if errorlevel 1 (
    echo.
    echo ERROR: Frontend failed to start
    echo.
    echo Make sure:
    echo 1. Node.js is installed
    echo 2. Dependencies are installed: npm install
    echo 3. Check the error messages above
    pause
)


