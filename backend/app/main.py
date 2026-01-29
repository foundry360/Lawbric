"""
Legal Discovery AI Platform - Main FastAPI Application

This is the entry point for the backend API server.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.core.security import verify_token
from app.models.user import User
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "development" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Legal Discovery AI Platform...")
    # #region agent log
    import json
    from datetime import datetime
    log_path = r"c:\LegalAI\.cursor\debug.log"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:35","message":"Lifespan startup beginning","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
        
        # Migration: Add title column if it doesn't exist and set default for existing users
        from app.core.database import SessionLocal
        from app.models.user import User
        from sqlalchemy import inspect, text
        db = SessionLocal()
        try:
            # Check if title column exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'title' not in columns:
                # Add title column with default value
                logger.info("Adding title column to users table...")
                with engine.connect() as conn:
                    # For PostgreSQL
                    if 'postgresql' in str(engine.url):
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS title VARCHAR(50) DEFAULT 'attorney' NOT NULL"))
                    # For SQLite
                    else:
                        conn.execute(text("ALTER TABLE users ADD COLUMN title VARCHAR(50) DEFAULT 'attorney' NOT NULL"))
                    conn.commit()
                logger.info("Title column added successfully")
            
            # Update any users without title (shouldn't happen with NOT NULL, but just in case)
            from sqlalchemy import or_
            users_without_title = db.query(User).filter(
                or_(User.title == None, User.title == '')
            ).all()
            if users_without_title:
                logger.info(f"Updating {len(users_without_title)} users without title to default 'attorney'")
                for user in users_without_title:
                    user.title = 'attorney'
                db.commit()
                logger.info("Migration complete: All users now have a title")
            
            # Migration: Add view_count column to documents table if it doesn't exist
            columns = [col['name'] for col in inspector.get_columns('documents')]
            if 'view_count' not in columns:
                logger.info("Adding view_count column to documents table...")
                with engine.connect() as conn:
                    # For PostgreSQL
                    if 'postgresql' in str(engine.url):
                        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0 NOT NULL"))
                    # For SQLite
                    else:
                        conn.execute(text("ALTER TABLE documents ADD COLUMN view_count INTEGER DEFAULT 0 NOT NULL"))
                    conn.commit()
                logger.info("view_count column added successfully")
                
                # Set default value for existing documents
                from app.models.case import Document
                documents_without_view_count = db.query(Document).filter(
                    Document.view_count == None
                ).all()
                if documents_without_view_count:
                    logger.info(f"Setting view_count to 0 for {len(documents_without_view_count)} existing documents")
                    for doc in documents_without_view_count:
                        doc.view_count = 0
                    db.commit()
                    logger.info("Migration complete: All documents now have view_count")
            
            # Migration: Create case_notes table if it doesn't exist
            try:
                tables = inspector.get_table_names()
                if 'case_notes' not in tables:
                    logger.info("Creating case_notes table...")
                    from app.models.case import CaseNote
                    CaseNote.__table__.create(bind=engine, checkfirst=True)
                    logger.info("case_notes table created successfully")
                else:
                    # Migration: Update case_notes table to make title NOT NULL
                    columns = [col['name'] for col in inspector.get_columns('case_notes')]
                    if 'title' in columns:
                        # Check if title column is nullable
                        title_col = next((col for col in inspector.get_columns('case_notes') if col['name'] == 'title'), None)
                        if title_col and title_col.get('nullable', True):
                            logger.info("Updating case_notes table to make title NOT NULL...")
                            from app.models.case import CaseNote
                            # Set default title for existing notes with NULL titles
                            notes_without_title = db.query(CaseNote).filter(
                                CaseNote.title == None
                            ).all()
                            if notes_without_title:
                                logger.info(f"Setting default titles for {len(notes_without_title)} notes...")
                                for note in notes_without_title:
                                    note.title = "Untitled Note"
                                db.commit()
                            db.close()  # Close the session before using engine.connect()
                            
                            # Alter column to NOT NULL
                            with engine.connect() as conn:
                                conn.execute(text("ALTER TABLE case_notes ALTER COLUMN title SET NOT NULL"))
                                conn.commit()
                            logger.info("case_notes.title column updated to NOT NULL")
                    
                    # Migration: Add metadata columns to case_notes table
                    columns = [col['name'] for col in inspector.get_columns('case_notes')]
                    with engine.connect() as conn:
                        if 'privilege_tag' not in columns:
                            logger.info("Adding privilege_tag column to case_notes table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN IF NOT EXISTS privilege_tag VARCHAR"))
                            else:
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN privilege_tag VARCHAR"))
                            conn.commit()
                            logger.info("privilege_tag column added successfully")
                        
                        if 'is_non_authoritative' not in columns:
                            logger.info("Adding is_non_authoritative column to case_notes table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN IF NOT EXISTS is_non_authoritative BOOLEAN DEFAULT FALSE"))
                            else:
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN is_non_authoritative BOOLEAN DEFAULT 0"))
                            conn.commit()
                            logger.info("is_non_authoritative column added successfully")
                        
                        if 'source_document_links' not in columns:
                            logger.info("Adding source_document_links column to case_notes table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN IF NOT EXISTS source_document_links TEXT"))
                            else:
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN source_document_links TEXT"))
                            conn.commit()
                            logger.info("source_document_links column added successfully")
                        
                        if 'is_archived' not in columns:
                            logger.info("Adding is_archived column to case_notes table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE NOT NULL"))
                            else:
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                            conn.commit()
                            logger.info("is_archived column added successfully")
                        
                        if 'archived_at' not in columns:
                            logger.info("Adding archived_at column to case_notes table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE"))
                            else:
                                conn.execute(text("ALTER TABLE case_notes ADD COLUMN archived_at TIMESTAMP"))
                            conn.commit()
                            logger.info("archived_at column added successfully")
                    
                    # Migration: Create case_note_versions table if it doesn't exist
                    if 'case_note_versions' not in inspector.get_table_names():
                        logger.info("Creating case_note_versions table...")
                        with engine.connect() as conn:
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("""
                                    CREATE TABLE IF NOT EXISTS case_note_versions (
                                        id SERIAL PRIMARY KEY,
                                        note_id INTEGER NOT NULL REFERENCES case_notes(id) ON DELETE CASCADE,
                                        version_number INTEGER NOT NULL,
                                        title VARCHAR NOT NULL,
                                        content TEXT NOT NULL,
                                        privilege_tag VARCHAR,
                                        is_non_authoritative BOOLEAN DEFAULT FALSE,
                                        edited_by INTEGER NOT NULL REFERENCES users(id),
                                        change_summary TEXT,
                                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                                    )
                                """))
                                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_case_note_versions_note_id ON case_note_versions(note_id)"))
                            else:
                                conn.execute(text("""
                                    CREATE TABLE IF NOT EXISTS case_note_versions (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        note_id INTEGER NOT NULL REFERENCES case_notes(id) ON DELETE CASCADE,
                                        version_number INTEGER NOT NULL,
                                        title VARCHAR NOT NULL,
                                        content TEXT NOT NULL,
                                        privilege_tag VARCHAR,
                                        is_non_authoritative BOOLEAN DEFAULT 0,
                                        edited_by INTEGER NOT NULL REFERENCES users(id),
                                        change_summary TEXT,
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                """))
                                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_case_note_versions_note_id ON case_note_versions(note_id)"))
                            conn.commit()
                        logger.info("case_note_versions table created successfully")
            except Exception as e:
                logger.warning(f"Error creating/updating case_notes table: {e}", exc_info=True)
            
            # Migration: Add is_archived and archived_at columns to documents table
            try:
                tables = inspector.get_table_names()
                if 'documents' in tables:
                    columns = [col['name'] for col in inspector.get_columns('documents')]
                    with engine.connect() as conn:
                        if 'is_archived' not in columns:
                            logger.info("Adding is_archived column to documents table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE NOT NULL"))
                            else:
                                conn.execute(text("ALTER TABLE documents ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                            conn.commit()
                            logger.info("is_archived column added successfully")
                        
                        if 'archived_at' not in columns:
                            logger.info("Adding archived_at column to documents table...")
                            if 'postgresql' in str(engine.url):
                                conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE"))
                            else:
                                conn.execute(text("ALTER TABLE documents ADD COLUMN archived_at TIMESTAMP"))
                            conn.commit()
                            logger.info("archived_at column added successfully")
            except Exception as e:
                logger.warning(f"Error adding archive columns to documents table: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Error during migration: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:42","message":"Database metadata created","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:47","message":"Database creation failed","data":{"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        raise

    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:50","message":"Lifespan startup complete, yielding","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal Discovery AI Platform...")
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"shutdown","hypothesisId":"E","location":"main.py:58","message":"Lifespan shutdown","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion


# Create FastAPI app
app = FastAPI(
    title="Legal Discovery AI Platform",
    description="AI-powered legal document discovery and analysis platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS middleware - must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



# Dependency for authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify JWT token and return current user"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    # In production, fetch user from database
    # For MVP, we'll use a simplified approach
    return User(id=user_id, email=payload.get("email", "user@example.com"))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - verifies database connectivity"""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        # Check database connectivity
        db = SessionLocal()
        try:
            # Simple query to verify database is accessible
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as db_error:
            logger.warning(f"Database health check failed: {db_error}")
            db_status = "disconnected"
        finally:
            db.close()
        
        if db_status == "connected":
            return {
                "status": "healthy",
                "service": "Legal Discovery AI Platform",
                "database": "connected"
            }
        else:
            return {
                "status": "degraded",
                "service": "Legal Discovery AI Platform",
                "database": "disconnected"
            }
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9001,
        reload=settings.ENVIRONMENT == "development",
    )

