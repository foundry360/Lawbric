# PowerShell script to set up environment variables
# Run this script to create .env files with your Supabase credentials

$frontendEnv = @"
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
"@

$backendEnv = @"
# Server Configuration
ENVIRONMENT=development
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=sqlite:///./legalai.db

# Supabase Configuration
SUPABASE_URL=https://erzumnwlvokamhuwcfyf.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NzA5ODAsImV4cCI6MjA4NDM0Njk4MH0.nxgtb_xsbwamZ2OIGvHA6xyXoKnsnAIDi6mGAVNi8jA
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyenVtbndsdm9rYW1odXdjZnlmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODc3MDk4MCwiZXhwIjoyMDg0MzQ2OTgwfQ.u7ktKuVZ3Q3mGWzxUPZ1ehRSnIsJobDV9ZvF4OSG65A

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

