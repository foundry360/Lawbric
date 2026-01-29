# PowerShell script to set up environment variables
# Run this script to create .env files

$frontendEnv = @"
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:9001
"@

$backendEnv = @"
# Server Configuration
ENVIRONMENT=development
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql://legalai:legalai123@localhost:5432/legalai

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-opus-20240229

# Vector Database
VECTOR_DB_TYPE=chroma
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=legalai-documents

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=100
"@

# Create frontend .env.local
$frontendPath = Join-Path $PSScriptRoot "frontend\.env.local"
$frontendEnv | Out-File -FilePath $frontendPath -Encoding utf8 -NoNewline
Write-Host "Created $frontendPath" -ForegroundColor Green

# Create backend .env
$backendPath = Join-Path $PSScriptRoot "backend\.env"
$backendEnv | Out-File -FilePath $backendPath -Encoding utf8 -NoNewline
Write-Host "Created $backendPath" -ForegroundColor Green

Write-Host "`nEnvironment files created successfully!" -ForegroundColor Cyan
Write-Host "Please restart your dev servers for the changes to take effect." -ForegroundColor Yellow

