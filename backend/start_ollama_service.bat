@echo off
echo Starting Ollama Service on port 8002...
echo.
cd /d %~dp0
set OLLAMA_SERVICE_PORT=8002
python ollama_service.py
pause

