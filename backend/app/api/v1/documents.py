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
import json

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# #region agent log
LOG_PATH = r"c:\LegalAI\.cursor\debug.log"
def agent_log(session_id, run_id, hypothesis_id, location, message, data=None):
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
# #endregion

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
    # #region agent log
    agent_log("debug-session", "run1", "B", "documents.py:44", "Background task function ENTERED", {
        "document_id": document_id,
        "file_path": file_path,
        "file_ext": file_ext,
        "case_id": case_id,
        "thread_name": threading.current_thread().name
    })
    # #endregion
    logger.info(f"=== BACKGROUND TASK STARTED for document {document_id} ===")
    logger.info(f"Parameters: file_path={file_path}, file_ext={file_ext}, case_id={case_id}")
    
    # Create a new database session for the background task
    db = None
    try:
        # #region agent log
        agent_log("debug-session", "run1", "C", "documents.py:56", "Before SessionLocal()", {"document_id": document_id})
        # #endregion
        db = SessionLocal()
        # #region agent log
        agent_log("debug-session", "run1", "C", "documents.py:58", "After SessionLocal()", {
            "document_id": document_id,
            "db_is_none": db is None
        })
        # #endregion
        logger.info(f"Database session created for document {document_id}")
        
        # Get the document
        # #region agent log
        agent_log("debug-session", "run1", "D", "documents.py:63", "Before document query", {"document_id": document_id})
        # #endregion
        document = db.query(Document).filter(Document.id == document_id).first()
        # #region agent log
        agent_log("debug-session", "run1", "D", "documents.py:65", "After document query", {
            "document_id": document_id,
            "document_found": document is not None,
            "document_status": document.status if document else None
        })
        # #endregion
        if not document:
            logger.error(f"Document {document_id} not found for processing")
            # #region agent log
            agent_log("debug-session", "run1", "D", "documents.py:70", "Document not found, RETURNING", {"document_id": document_id})
            # #endregion
            return
        
        logger.info(f"Document {document_id} retrieved, current status: {document.status}")
        
        # Explicitly set status to processing at start of background task
        document.status = "processing"
        db.commit()
        logger.info(f"Document {document_id} status set to 'processing', starting background processing")
        
        # Step 0: Generate thumbnail
        logger.info(f"Generating thumbnail for document {document_id}")
        thumbnail_path = None
        try:
            # Ensure thumbnail directory exists
            os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
            
            thumbnail_filename = f"thumb_{document_id}.jpg"
            thumbnail_output_path = os.path.join(settings.THUMBNAIL_DIR, thumbnail_filename)
            # Convert to absolute path for reliable storage
            thumbnail_output_path = os.path.abspath(thumbnail_output_path)
            
            logger.info(f"Attempting to generate thumbnail: {file_path} -> {thumbnail_output_path}")
            if processor.generate_thumbnail(file_path, file_ext, thumbnail_output_path):
                # Verify thumbnail was actually created
                if os.path.exists(thumbnail_output_path):
                    thumbnail_path = thumbnail_output_path
                    # Save thumbnail path immediately so it's available even if processing fails later
                    document.thumbnail_path = thumbnail_path
                    db.commit()
                    logger.info(f"Thumbnail generated and saved for document {document_id}: {thumbnail_path}")
                else:
                    logger.error(f"Thumbnail generation reported success but file not found: {thumbnail_output_path}")
            else:
                logger.warning(f"Thumbnail generation returned False for document {document_id} (file_type: {file_ext})")
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail for document {document_id}: {e}", exc_info=True)
        
        # Step 1: Extract text
        logger.info(f"Extracting text from document {document_id} (file: {file_path})")
        
        # Verify file exists before processing
        # #region agent log
        agent_log("debug-session", "run1", "E", "documents.py:104", "Checking file existence", {
            "document_id": document_id,
            "file_path": file_path
        })
        # #endregion
        if not os.path.exists(file_path):
            # #region agent log
            agent_log("debug-session", "run1", "E", "documents.py:107", "File NOT found", {
                "document_id": document_id,
                "file_path": file_path
            })
            # #endregion
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        # #region agent log
        agent_log("debug-session", "run1", "E", "documents.py:113", "File exists, before processor.process_document()", {
            "document_id": document_id,
            "file_path": file_path,
            "file_ext": file_ext
        })
        # #endregion
        logger.info(f"File exists, calling processor.process_document()")
        processed = processor.process_document(file_path, file_ext)
        # #region agent log
        agent_log("debug-session", "run1", "F", "documents.py:118", "After processor.process_document()", {
            "document_id": document_id,
            "page_count": processed.get("page_count"),
            "requires_ocr": processed.get("requires_ocr"),
            "text_length": len(processed.get("text", "")),
            "has_pages": "pages" in processed
        })
        # #endregion
        logger.info(f"Processor returned: page_count={processed.get('page_count')}, requires_ocr={processed.get('requires_ocr')}")
        
        # Update document with extraction results
        document.extracted_text = processed["text"]
        document.page_count = processed["page_count"]
        document.word_count = len(processed["text"].split())
        document.requires_ocr = processed["requires_ocr"]
        document.ocr_completed = not processed["requires_ocr"] or all(
            page.get("method") == "ocr" for page in processed["pages"]
        )
        # #region agent log
        agent_log("debug-session", "run1", "F", "documents.py:126", "Before commit after text extraction", {
            "document_id": document_id,
            "page_count": document.page_count,
            "word_count": document.word_count,
            "extracted_text_length": len(document.extracted_text) if document.extracted_text else 0
        })
        # #endregion
        db.commit()
        # #region agent log
        agent_log("debug-session", "run1", "F", "documents.py:132", "After commit after text extraction", {
            "document_id": document_id
        })
        # #endregion
        logger.info(f"Text extraction completed for document {document_id}: {document.page_count} pages, {document.word_count} words")
        
        # Step 2: Chunk text with page mapping
        logger.info(f"Chunking text for document {document_id}")
        # Build page mapping from processed pages for better page number tracking
        page_mapping = []
        if processed.get("pages"):
            current_char = 0
            for page_info in processed["pages"]:
                page_num = page_info.get("page_number", 1)
                page_text = page_info.get("text", "")
                page_start = current_char
                page_end = current_char + len(page_text)
                page_mapping.append({
                    "page": page_num,
                    "start": page_start,
                    "end": page_end
                })
                current_char = page_end + 2  # +2 for \n\n separator
        
        chunks = processor.chunk_text(
            processed["text"],
            page_mapping=page_mapping if page_mapping else None
        )
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        
        # Step 3: Generate embeddings
        logger.info(f"Generating embeddings for document {document_id}")
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")
        
        # Step 4: Save chunks to database and prepare vector store data
        logger.info(f"Saving chunks to database for document {document_id}")
        chunk_metadata_list = []
        chunk_ids_list = []  # Store (chunk_id, embedding_id) pairs for updating embedding_id
        
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
            
            # Generate embedding_id (format matches vector store)
            embedding_id = f"chunk_{db_chunk.id}"
            chunk_ids_list.append((db_chunk.id, embedding_id))
            
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
        
        # Step 5: Add to vector store
        logger.info(f"Storing embeddings in vector store for document {document_id}")
        chunk_docs = [{"content": chunk["content"]} for chunk in chunks]
        vector_store.add_documents(chunk_docs, embeddings, chunk_metadata_list)
        
        # Step 6: Update embedding_id in DocumentChunk records
        logger.info(f"Updating embedding_id references for document {document_id}")
        for chunk_id, embedding_id in chunk_ids_list:
            db_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
            if db_chunk:
                db_chunk.embedding_id = embedding_id
        db.commit()
        
        # Step 7: Update document status
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        document.error_message = None  # Clear any previous error
        # thumbnail_path was already saved in Step 0, so no need to set it again
        db.commit()
        
        logger.info(f"Document {document_id} processed successfully")
        
    except Exception as e:
        # #region agent log
        agent_log("debug-session", "run1", "G", "documents.py:215", "EXCEPTION caught in background task", {
            "document_id": document_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "db_is_none": db is None
        })
        # #endregion
        logger.error(f"=== ERROR processing document {document_id} ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}, Error message: {str(e)}")
        # Update document status to error with error message
        try:
            if db is None:
                # #region agent log
                agent_log("debug-session", "run1", "G", "documents.py:222", "Creating new DB session in exception handler", {"document_id": document_id})
                # #endregion
                db = SessionLocal()
            # #region agent log
            agent_log("debug-session", "run1", "G", "documents.py:225", "Querying document in exception handler", {"document_id": document_id})
            # #endregion
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                # Store error message (truncate if too long)
                error_msg = str(e)
                document.error_message = error_msg[:1000] if len(error_msg) > 1000 else error_msg
                db.commit()
                logger.error(f"Document {document_id} status updated to error: {error_msg[:200]}")
            else:
                logger.error(f"Could not find document {document_id} to update error status")
        except Exception as db_error:
            logger.error(f"Error updating document status to error: {db_error}", exc_info=True)
    finally:
        # #region agent log
        agent_log("debug-session", "run1", "H", "documents.py:236", "In finally block, before closing DB", {
            "document_id": document_id,
            "db_is_none": db is None
        })
        # #endregion
        if db:
            db.close()
        # #region agent log
        agent_log("debug-session", "run1", "H", "documents.py:240", "Background task EXITING", {"document_id": document_id})
        # #endregion
        logger.info(f"=== BACKGROUND TASK FINISHED for document {document_id} ===")


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
    
    # Verify status was saved - re-query to ensure we have the latest data
    db.refresh(document)
    if document.status != "processing":
        logger.warning(f"Document {document.id} status is '{document.status}', expected 'processing'. Fixing...")
        document.status = "processing"
        db.commit()
        db.refresh(document)
    
    logger.info(f"Document {document.id} created with status: {document.status}")
    
    # Process document asynchronously in background using threading
    # Using threading instead of BackgroundTasks for more reliable execution
    # FastAPI BackgroundTasks may not execute in all setups
    import threading
    
    # Run in a daemon thread to ensure it executes reliably
    # #region agent log
    agent_log("debug-session", "run1", "A", "documents.py:315", "Creating background thread", {
        "document_id": document.id,
        "file_path": file_path,
        "file_ext": file_ext,
        "case_id": case_id
    })
    # #endregion
    thread = threading.Thread(
        target=process_document_background,
        args=(document.id, file_path, file_ext, case_id),
        daemon=True,
        name=f"doc-processor-{document.id}"
    )
    # #region agent log
    agent_log("debug-session", "run1", "A", "documents.py:321", "Thread created, about to start", {
        "thread_name": thread.name,
        "thread_is_alive": thread.is_alive()
    })
    # #endregion
    thread.start()
    # #region agent log
    agent_log("debug-session", "run1", "A", "documents.py:324", "Thread started", {
        "thread_name": thread.name,
        "thread_is_alive": thread.is_alive(),
        "thread_ident": thread.ident
    })
    # #endregion
    logger.info(f"Document {document.id} background processing started in thread {thread.name}")
    
    logger.info(f"Document {document.id} queued for background processing")
    return document


@router.get("/{document_id}/thumbnail")
async def get_document_thumbnail(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get thumbnail image for a document"""
    from fastapi.responses import FileResponse
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if thumbnail exists
    if not document.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    # Handle both absolute and relative paths
    thumbnail_path = document.thumbnail_path
    if not os.path.isabs(thumbnail_path):
        # If relative, try to resolve it relative to thumbnail directory
        thumbnail_path = os.path.join(settings.THUMBNAIL_DIR, os.path.basename(thumbnail_path))
    
    # Convert to absolute path for FileResponse
    thumbnail_path = os.path.abspath(thumbnail_path)
    
    if not os.path.exists(thumbnail_path):
        logger.warning(f"Thumbnail file not found at path: {thumbnail_path} (stored path: {document.thumbnail_path})")
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")
    
    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg",
        filename=f"thumb_{document_id}.jpg"
    )


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
    
    # Delete thumbnail if it exists
    if document.thumbnail_path and os.path.exists(document.thumbnail_path):
        try:
            os.remove(document.thumbnail_path)
        except Exception as e:
            logger.warning(f"Error deleting thumbnail {document.thumbnail_path}: {e}")
    
    # Delete chunks from vector store
    chunk_ids = [f"chunk_{chunk.id}" for chunk in document.chunks]
    if chunk_ids:
        vector_store.delete_documents(chunk_ids)
    
    # Delete from database (cascade will handle chunks)
    db.delete(document)
    db.commit()
    
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Reprocess a failed or existing document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify user has access to the case
    case = db.query(Case).filter(Case.id == document.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    
    # Delete existing chunks if reprocessing
    if document.chunks:
        # Delete chunks from vector store
        chunk_ids = [f"chunk_{chunk.id}" for chunk in document.chunks]
        if chunk_ids:
            try:
                vector_store.delete_documents(chunk_ids)
            except Exception as e:
                logger.warning(f"Error deleting old chunks from vector store: {e}")
        
        # Delete chunks from database (cascade should handle this, but explicit is better)
        for chunk in document.chunks:
            db.delete(chunk)
    
    # Delete old thumbnail if it exists
    if document.thumbnail_path and os.path.exists(document.thumbnail_path):
        try:
            os.remove(document.thumbnail_path)
        except Exception as e:
            logger.warning(f"Error deleting old thumbnail: {e}")
        document.thumbnail_path = None
    
    # Reset status and clear error
    document.status = "processing"
    document.error_message = None
    document.processed_at = None
    db.commit()
    db.refresh(document)
    
    logger.info(f"Reprocessing document {document_id}")
    
    # Queue for reprocessing
    background_tasks.add_task(
        process_document_background,
        document_id=document.id,
        file_path=document.file_path,
        file_ext=document.file_type,
        case_id=document.case_id
    )
    
    return document

