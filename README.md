# Legal Discovery AI Platform

A secure AI-powered platform for legal document discovery, analysis, and case management inspired by NotebookLM, purpose-built for litigation workflows.

## Features

- **Document Ingestion**: Upload PDFs, DOCX, TXT, CSV, emails, and scanned documents with OCR
- **AI-Powered Analysis**: Source-grounded Q&A, summaries, timelines, and issue-spotting
- **Strict Grounding**: Never hallucinates - all answers cite exact source passages
- **Legal-Specific**: Deposition analysis, contract extraction, discovery mapping
- **Secure**: Case-level isolation, encryption, audit logs, no training on user data

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (React) with TypeScript
- **Vector DB**: ChromaDB (default), Pinecone, or Weaviate
- **LLM**: OpenAI or Anthropic (configurable)
- **OCR**: Tesseract (default) or Cloud OCR
- **Database**: SQLite (dev) or PostgreSQL (production)

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Tesseract OCR (for OCR functionality)
- OpenAI API key or Anthropic API key (for LLM)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

The backend will run on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your backend URL (default: http://localhost:8000)
npm run dev
```

The frontend will run on `http://localhost:3000`

### First Login

For MVP, you can use any email/password combination. The system will create a new account automatically.

## Project Structure

```
LegalAI/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration, database, security
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic (RAG, document processing)
│   │   └── utils/        # Utilities (encryption, audit)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # API client, auth
│   └── package.json
├── README.md
├── PROMPTS.md            # Example prompts for attorneys
└── .gitignore
```

## Core Components

### Document Processing Pipeline

1. **Upload**: Files are uploaded and stored securely
2. **Text Extraction**: PDFs, DOCX, and TXT files are processed
3. **OCR**: Scanned documents undergo OCR if needed
4. **Chunking**: Documents are split into searchable chunks
5. **Embedding**: Chunks are converted to vector embeddings
6. **Storage**: Embeddings stored in vector database

### RAG (Retrieval-Augmented Generation) Pipeline

1. **Query**: User asks a question
2. **Embedding**: Question is converted to embedding vector
3. **Retrieval**: Similar document chunks are retrieved
4. **Context Building**: Retrieved chunks form context
5. **Generation**: LLM generates answer using only retrieved context
6. **Citation**: Sources are cited with page/paragraph references

### Security Features

- **Encryption**: Files can be encrypted at rest (configurable)
- **Case Isolation**: Documents are isolated by case
- **Audit Logging**: All actions are logged for compliance
- **Authentication**: JWT-based authentication
- **Role-Based Access**: Support for Attorney, Paralegal, Admin roles

## Example Prompts

See [PROMPTS.md](./PROMPTS.md) for comprehensive examples of prompts attorneys can use.

Quick examples:
- "What did the witness say about the incident on March 15th?"
- "Create a timeline of all communications between Company A and Company B"
- "Identify all privileged documents in the production"
- "What are the key facts supporting the negligence claim?"
- "Compare the terms in Contract A vs Contract B regarding termination clauses"

## Configuration

### Backend Configuration (.env)

Key settings:
- `LLM_PROVIDER`: `openai` or `anthropic`
- `VECTOR_DB_TYPE`: `chroma`, `pinecone`, or `weaviate`
- `ENCRYPT_FILES`: `true` or `false`
- `CASE_ISOLATION_ENABLED`: `true` or `false`

### Frontend Configuration (.env.local)

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## Development

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable file encryption (`ENCRYPT_FILES=true`)
- [ ] Set up proper CORS origins
- [ ] Use HTTPS
- [ ] Configure proper backup strategy
- [ ] Set up monitoring and logging
- [ ] Review and configure audit logging

### Scaling Considerations

- Use managed vector database (Pinecone, Weaviate Cloud)
- Implement background task queue for document processing
- Use object storage (S3) for document files
- Implement caching layer
- Use CDN for frontend assets

## Limitations (MVP)

- Single case focus (multi-case support in roadmap)
- Basic OCR (advanced OCR features in roadmap)
- Synchronous document processing (async processing in roadmap)
- Limited document preview (full viewer in roadmap)
- Basic search (advanced search in roadmap)

## Roadmap

- [ ] Multi-case support
- [ ] Advanced OCR with better accuracy
- [ ] Asynchronous document processing
- [ ] Full document viewer with annotations
- [ ] Advanced search and filtering
- [ ] Export capabilities (PDF reports, timelines)
- [ ] Collaboration features
- [ ] Mobile app
- [ ] Integration with legal case management systems

## Security & Compliance

- **Encryption**: Files encrypted at rest (optional)
- **Case Isolation**: Strict data isolation between cases
- **No Training**: User data is never used to train models
- **Audit Logs**: Comprehensive logging of all actions
- **Legal Holds**: Support for preserving data (roadmap)

## License

Proprietary - Legal Use Only

## Support

For issues and questions, please contact your system administrator.
