@echo off
echo Starting Legal Discovery AI Backend...
echo.

cd backend

REM Try Python launcher first (most reliable on Windows)
py run.py

if errorlevel 1 (
    echo.
    echo ERROR: Backend failed to start
    echo.
    echo Make sure:
    echo 1. Python is installed
    echo 2. Dependencies are installed: py -m pip install -r requirements.txt
    echo 3. Check the error messages above
    pause
)


