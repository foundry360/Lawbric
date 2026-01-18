# Setup Guide

This guide will help you set up the Legal Discovery AI Platform from scratch.

## Prerequisites

### Required Software

1. **Python 3.9+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Node.js 18+**
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version`

3. **Tesseract OCR** (for OCR functionality)
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

### Required API Keys

1. **OpenAI API Key** (recommended for MVP)
   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Create an API key

2. **OR Anthropic API Key**
   - Sign up at [console.anthropic.com](https://console.anthropic.com/)
   - Create an API key

## Step-by-Step Setup

### 1. Clone/Download the Project

```bash
# If using git
git clone <repository-url>
cd LegalAI

# Or extract the project files to C:\LegalAI
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your API keys
# At minimum, set:
# - OPENAI_API_KEY=your-key-here
# - Or ANTHROPIC_API_KEY=your-key-here
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local (usually no changes needed if backend is on localhost:8000)
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start the Application

#### Terminal 1 - Backend

```bash
cd backend
# Activate venv if not already activated
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Start backend server
uvicorn app.main:app --reload
```

Backend should be running on `http://localhost:8000`

#### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Frontend should be running on `http://localhost:3000`

### 5. First Login

1. Open browser to `http://localhost:3000`
2. Use any email/password (e.g., `attorney@lawfirm.com` / `password123`)
3. The system will create your account automatically

## Configuration Options

### Backend (.env)

Key configuration options:

```env
# LLM Provider
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Vector Database (default: chroma works out of the box)
VECTOR_DB_TYPE=chroma  # or pinecone, weaviate

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=100

# Security
ENCRYPT_FILES=false  # Set to true for production
CASE_ISOLATION_ENABLED=true
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing the Setup

1. **Create a Case**
   - Click "New Case" on the dashboard
   - Enter a case name (e.g., "Test Case")

2. **Upload a Document**
   - Open the case
   - Click "Upload Document"
   - Upload a PDF or DOCX file
   - Wait for processing (may take a minute)

3. **Ask a Question**
   - In the chat interface, ask: "What is this document about?"
   - The AI should respond with citations

## Troubleshooting

### Backend Issues

**Import Errors**
```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database Errors**
```bash
# Delete existing database (if corrupted)
rm legalai.db  # or delete the file manually
# Restart backend - it will recreate the database
```

**OCR Not Working**
- Verify Tesseract is installed: `tesseract --version`
- Update `TESSERACT_CMD` in `.env` with full path to tesseract executable

### Frontend Issues

**Cannot Connect to Backend**
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

### API Key Issues

**OpenAI API Errors**
- Verify API key is correct
- Check you have credits in your OpenAI account
- Verify the key has proper permissions

**No LLM Response**
- Check backend logs for errors
- Verify API key is set correctly
- System will fall back to chunk retrieval if LLM fails

## Next Steps

1. **Upload Documents**: Start uploading your legal documents
2. **Explore Features**: Try different types of queries
3. **Review Citations**: Always verify AI responses against source documents
4. **See PROMPTS.md**: For example queries to try

## Production Deployment

For production deployment, see the Production Deployment section in README.md.

Key considerations:
- Use PostgreSQL instead of SQLite
- Enable file encryption
- Set up proper authentication
- Configure HTTPS
- Set up monitoring and backups


