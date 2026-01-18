"""
Document management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.core.security import verify_token
from app.models.case import Case, Document, DocumentChunk
from app.schemas.case import DocumentResponse, DocumentCreate
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

processor = DocumentProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStore()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Get current user ID from token"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))


def process_document_background(document_id: int, file_path: str, file_ext: str, case_id: int):
    """
    Background task to process a document asynchronously
    This function runs in a separate thread/process after the upload endpoint returns
    """
    # Create a new database session for the background task
    db = SessionLocal()
    
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for processing")
            return
        
        logger.info(f"Starting background processing for document {document_id}")
        
        # Extract text
        processed = processor.process_document(file_path, file_ext)
        
        # Update document
        document.extracted_text = processed["text"]
        document.page_count = processed["page_count"]
        document.word_count = len(processed["text"].split())
        document.requires_ocr = processed["requires_ocr"]
        document.ocr_completed = not processed["requires_ocr"] or all(
            page.get("method") == "ocr" for page in processed["pages"]
        )
        db.commit()
        
        # Chunk text
        chunks = processor.chunk_text(processed["text"])
        
        # Generate embeddings and store
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        
        # Save chunks to database and vector store
        chunk_metadata_list = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Save chunk to database
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                page_number=chunk.get("page_number"),
                start_char=chunk["start_char"],
                end_char=chunk["end_char"]
            )
            db.add(db_chunk)
            db.flush()
            
            # Prepare metadata for vector store
            metadata = {
                "chunk_id": db_chunk.id,
                "document_id": document.id,
                "document_name": document.original_filename,
                "case_id": case_id,
                "page_number": chunk.get("page_number"),
                "paragraph_number": chunk.get("paragraph_number"),
                "chunk_index": chunk["chunk_index"]
            }
            chunk_metadata_list.append(metadata)
        
        db.commit()
        
        # Add to vector store
        chunk_docs = [{"content": chunk["content"]} for chunk in chunks]
        vector_store.add_documents(chunk_docs, embeddings, chunk_metadata_list)
        
        # Update document status
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        # Update document status to error
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating document status to error: {db_error}")
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_id: int = Form(...),
    bates_number: Optional[str] = Form(None),
    custodian: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    document_date: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Upload and process a document"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Validate file type
    file_ext = Path(file.filename).suffix[1:].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{file_ext} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save file
    case_dir = os.path.join(settings.UPLOAD_DIR, f"case_{case_id}")
    os.makedirs(case_dir, exist_ok=True)
    
    file_path = os.path.join(case_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create document record
    document = Document(
        case_id=case_id,
        filename=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file_ext,
        file_size=file_size,
        mime_type=file.content_type,
        bates_number=bates_number,
        custodian=custodian,
        author=author,
        document_date=datetime.fromisoformat(document_date) if document_date else None,
        source=source,
        uploaded_by=user_id,
        status="processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document asynchronously in background
    background_tasks.add_task(
        process_document_background,
        document_id=document.id,
        file_path=file_path,
        file_ext=file_ext,
        case_id=case_id
    )
    
    logger.info(f"Document {document.id} queued for processing")
    return document


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    case_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 100
):
    """List documents for a case"""
    documents = db.query(Document).filter(
        Document.case_id == case_id
    ).offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get a specific document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Delete a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete chunks from vector store
    chunk_ids = [f"chunk_{chunk.id}" for chunk in document.chunks]
    if chunk_ids:
        vector_store.delete_documents(chunk_ids)
    
    # Delete from database (cascade will handle chunks)
    db.delete(document)
    db.commit()
    
    return None

