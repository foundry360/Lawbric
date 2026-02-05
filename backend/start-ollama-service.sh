#!/bin/bash
# Bash script to start the Ollama service
# Usage: ./start-ollama-service.sh

echo "Starting Ollama Service..."
echo ""

# Check if Ollama is running
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "✗ Cannot connect to Ollama at http://localhost:11434"
    echo "  Make sure Ollama is installed and running."
    echo "  Install: https://ollama.ai/download"
    echo "  Then run: ollama pull llama3:8b"
    exit 1
fi

# Check if model is available
echo "Checking for llama3:8b model..."
if ollama list | grep -q "llama3:8b"; then
    echo "✓ llama3:8b model found"
else
    echo "✗ llama3:8b model not found"
    echo "  Run: ollama pull llama3:8b"
    exit 1
fi

echo ""
echo "Starting Ollama Service on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""

# Set environment variables (optional - defaults are already set in the script)
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3:8b"
export OLLAMA_SERVICE_PORT="8001"

# Start the service
python ollama_service.py




