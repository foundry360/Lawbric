@echo off
echo ========================================
echo Legal Discovery AI - Starting Servers
echo ========================================
echo.
echo Starting backend and frontend in separate windows...
echo.

REM Start backend in new window
start "LegalAI Backend (Port 9000)" cmd /k "cd /d %~dp0backend && py run.py"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "LegalAI Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo Both servers starting in separate windows
echo ========================================
echo.
echo Backend: http://localhost:9000
echo Frontend: http://localhost:3000
echo.
echo Check the windows for any errors.
echo Press any key to close this window...
pause >nul


