"""
Document management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
import threading
import traceback
import time

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.core.auth import get_current_user_and_tenant
from app.models.case import Case, Document, DocumentChunk
from typing import Tuple
from app.schemas.case import DocumentResponse, DocumentCreate
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.risk_engine import RiskEngine
from app.utils.audit import log_immutable_audit
from app.core.config import settings
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

# Note: These are shared instances but the services should be thread-safe or we create per-thread instances
# For better reliability, we'll create new instances in background threads
_processor = None
_embedding_service = None
_vector_store = None

def get_processor():
    """Get or create document processor (thread-safe lazy initialization)"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor

def get_embedding_service():
    """Get or create embedding service (thread-safe lazy initialization)"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

def get_vector_store():
    """Get or create vector store (thread-safe lazy initialization)"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def process_document_background(document_id: int, file_path: str, file_ext: str, case_id: int, tenant_id: int = None):
    """
    Background task to process a document asynchronously
    This function runs in a separate thread/process after the upload endpoint returns
    """
    thread_name = threading.current_thread().name
    # #region agent log
    agent_log("debug-session", "run1", "B", "documents.py:44", "Background task function ENTERED", {
        "document_id": document_id,
        "file_path": file_path,
        "file_ext": file_ext,
        "case_id": case_id,
        "thread_name": thread_name
    })
    # #endregion
    logger.info(f"=== BACKGROUND TASK STARTED for document {document_id} in thread {thread_name} ===")
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
        
        # Get the document and case to retrieve tenant_id
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
        
        # Get tenant_id from case if not provided
        if tenant_id is None:
            case = db.query(Case).filter(Case.id == document.case_id).first()
            if case:
                tenant_id = case.tenant_id
        
        logger.info(f"Document {document_id} retrieved, current status: {document.status}")
        
        # Explicitly set status to processing at start of background task
        document.status = "processing"
        db.commit()
        logger.info(f"Document {document_id} status set to 'processing', starting background processing")
        
        # Verify file exists and is readable before starting processing
        # This handles cases where the file might not be fully written yet
        max_retries = 3
        retry_delay = 0.5  # seconds
        for attempt in range(max_retries):
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    # Try to open the file to ensure it's readable
                    with open(file_path, "rb") as test_file:
                        test_file.read(1)
                    break  # File is readable, proceed
                except (IOError, OSError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"File {file_path} not readable on attempt {attempt + 1}, retrying...")
                        time.sleep(retry_delay)
                    else:
                        raise FileNotFoundError(f"Document file exists but is not readable after {max_retries} attempts: {file_path}")
            else:
                if attempt < max_retries - 1:
                    logger.warning(f"File {file_path} not found on attempt {attempt + 1}, retrying...")
                    time.sleep(retry_delay)
                else:
                    raise FileNotFoundError(f"Document file not found after {max_retries} attempts: {file_path}")
        
        # Create thread-local instances of services to avoid thread-safety issues
        # This ensures each thread gets its own instances
        # Wrap initialization in try-except to handle transient resource failures
        try:
            processor = DocumentProcessor()
        except Exception as e:
            logger.error(f"Failed to initialize DocumentProcessor: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize document processor: {str(e)}")
        
        try:
            embedding_service = EmbeddingService()
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingService: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize embedding service: {str(e)}")
        
        try:
            vector_store = VectorStore()
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize vector store: {str(e)}")
        
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
        # The full text is built by concatenating pages with "\n\n" separators
        # NOTE: The text may have been .strip()'d, so we need to use the actual text structure
        page_mapping = []
        actual_text = processed.get("text", "")
        
        if processed.get("pages"):
            # Reconstruct the text exactly as it was built (with \n\n separators)
            # This matches how chunk_text will process it
            full_text_from_pages = "\n\n".join([p.get("text", "") for p in processed["pages"]])
            
            # The processed text might be stripped, so we need to account for that
            # Use the reconstructed text for mapping, but chunk the actual text
            # However, if they differ significantly, we need to adjust
            text_for_mapping = full_text_from_pages  # Use this for page mapping
            
            # Log if there's a significant mismatch
            if abs(len(full_text_from_pages) - len(actual_text)) > 10:  # Allow small differences from stripping
                logger.warning(f"Text length mismatch for document {document_id}. Reconstructed: {len(full_text_from_pages)}, actual: {len(actual_text)}. Using reconstructed for mapping.")
            
            current_char = 0
            for page_info in processed["pages"]:
                page_num = page_info.get("page_number", 1)
                page_text = page_info.get("text", "")
                page_start = current_char
                page_end = current_char + len(page_text)
                
                # Validate page number doesn't exceed document page count
                if document.page_count and page_num > document.page_count:
                    logger.warning(f"Page number {page_num} exceeds document page count {document.page_count} for document {document_id}. Capping to {document.page_count}.")
                    page_num = document.page_count
                
                page_mapping.append({
                    "page": page_num,
                    "start": page_start,
                    "end": page_end  # End is exclusive, doesn't include separator
                })
                
                # Move to next page: current page text + "\n\n" separator
                current_char = page_end + 2  # +2 for \n\n separator
                
                logger.debug(f"Page {page_num} mapping: start={page_start}, end={page_end}, text_length={len(page_text)}")
            
            logger.info(f"Built page mapping for {len(page_mapping)} pages. Document has {document.page_count} pages. Text length: {len(actual_text)}")
            
            # Validate page mapping makes sense
            if page_mapping:
                max_mapped_page = max(p["page"] for p in page_mapping)
                if max_mapped_page > document.page_count:
                    logger.error(f"Page mapping has page {max_mapped_page} but document only has {document.page_count} pages!")
        
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
            # Validate and cap page number at document page count
            chunk_page_num = chunk.get("page_number")
            if chunk_page_num is not None and document.page_count:
                if chunk_page_num > document.page_count:
                    logger.warning(f"Chunk {chunk['chunk_index']} has page number {chunk_page_num} but document only has {document.page_count} pages. Capping to {document.page_count}.")
                    chunk_page_num = document.page_count
                elif chunk_page_num < 1:
                    logger.warning(f"Chunk {chunk['chunk_index']} has invalid page number {chunk_page_num}. Setting to 1.")
                    chunk_page_num = 1
            
            # Save chunk to database
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                page_number=chunk_page_num,
                start_char=chunk["start_char"],
                end_char=chunk["end_char"]
            )
            db.add(db_chunk)
            db.flush()
            
            # Generate embedding_id (format matches vector store)
            embedding_id = f"chunk_{db_chunk.id}"
            chunk_ids_list.append((db_chunk.id, embedding_id))
            
            # Prepare metadata for vector store (with tenant isolation)
            # Filter out None values as vector stores don't accept them
            metadata = {
                "chunk_id": db_chunk.id,
                "document_id": document.id,
                "document_name": document.original_filename,
                "case_id": case_id,
                "chunk_index": chunk["chunk_index"]
            }
            # Only add optional fields if they are not None (use validated page_number)
            if chunk_page_num is not None:
                metadata["page_number"] = chunk_page_num
            if chunk.get("paragraph_number") is not None:
                metadata["paragraph_number"] = chunk.get("paragraph_number")
            # Add tenant_id for multi-tenant isolation
            if tenant_id is not None:
                metadata["tenant_id"] = tenant_id
            chunk_metadata_list.append(metadata)
        
        db.commit()
        
        # Step 5: Add to vector store
        logger.info(f"Storing embeddings in vector store for document {document_id}")
        chunk_docs = [{"content": chunk["content"]} for chunk in chunks]
        vector_store.add_documents(chunk_docs, embeddings, chunk_metadata_list)
        
        # Verify chunks were actually added to vector store
        logger.info(f"Verifying chunks were added to vector store for document {document_id}")
        verification_filter = {"document_id": document.id}
        if tenant_id is not None:
            verification_filter["tenant_id"] = tenant_id
        
        # Use a test query to verify chunks exist
        test_embedding = embeddings[0] if embeddings else None
        if test_embedding:
            verification_results = vector_store.search(
                query_embedding=test_embedding,
                top_k=1,
                filter_metadata=verification_filter
            )
            if not verification_results:
                # Try without document_id filter to see if chunks exist at all
                logger.warning(f"No chunks found in vector store for document {document_id} with filter {verification_filter}")
                all_results = vector_store.search(
                    query_embedding=test_embedding,
                    top_k=5,
                    filter_metadata=None
                )
                logger.warning(f"Total chunks in vector store: {len(all_results)}")
                if all_results:
                    logger.warning(f"Sample chunk metadata: {all_results[0].get('metadata', {})}")
                raise RuntimeError(f"Chunks were not successfully added to vector store for document {document_id}")
            else:
                logger.info(f"Verified {len(verification_results)} chunk(s) in vector store for document {document_id}")
        else:
            logger.warning(f"No embeddings generated for document {document_id}, skipping verification")
        
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
        
        logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks")
        
    except Exception as e:
        # #region agent log
        agent_log("debug-session", "run1", "G", "documents.py:215", "EXCEPTION caught in background task", {
            "document_id": document_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "db_is_none": db is None,
            "traceback": traceback.format_exc()
        })
        # #endregion
        logger.error(f"=== ERROR processing document {document_id} ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}, Error message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
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
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Upload and process a document (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    # Verify case exists, belongs to tenant, and was created by the current user
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
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
    # Ensure file is fully written and flushed to disk before processing
    with open(file_path, "wb") as f:
        f.write(file_content)
        f.flush()
        os.fsync(f.fileno())  # Force write to disk
    
    # Verify file was written correctly before proceeding
    if not os.path.exists(file_path) or os.path.getsize(file_path) != file_size:
        raise HTTPException(
            status_code=500,
            detail="File upload verification failed. File may not have been saved correctly."
        )
    
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
        uploaded_by=user_id if isinstance(user_id, int) else int(user_id) if user_id.isdigit() else None,
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
    
    # Run in a non-daemon thread to ensure it completes (daemon threads can be killed)
    # #region agent log
    agent_log("debug-session", "run1", "A", "documents.py:315", "Creating background thread", {
        "document_id": document.id,
        "file_path": file_path,
        "file_ext": file_ext,
        "case_id": case_id
    })
    # #endregion
    # Wrap the background function to ensure exceptions are logged
    def wrapped_process():
        try:
            process_document_background(document.id, file_path, file_ext, case_id, tenant_id)
        except Exception as e:
            logger.error(f"CRITICAL: Background thread for document {document.id} failed with uncaught exception: {e}", exc_info=True)
            # Try to update status to error
            try:
                error_db = SessionLocal()
                error_doc = error_db.query(Document).filter(Document.id == document.id).first()
                if error_doc:
                    error_doc.status = "error"
                    error_doc.error_message = f"Critical error: {str(e)[:500]}"
                    error_db.commit()
                error_db.close()
            except Exception as db_error:
                logger.error(f"Failed to update error status: {db_error}", exc_info=True)
    
    thread = threading.Thread(
        target=wrapped_process,
        daemon=False,  # Non-daemon so it completes
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
    document_id: str,  # Can be UUID string or integer
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get thumbnail image for a document (tenant-isolated)"""
    from fastapi.responses import FileResponse
    
    user_id, tenant_id = user_tenant
    
    # Convert document_id to integer
    try:
        doc_id_int = int(document_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid document_id format")
    
    # Get document with tenant isolation
    document = db.query(Document).filter(Document.id == doc_id_int).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document was uploaded by the current user
    if document.uploaded_by != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    thumbnail_path = document.thumbnail_path
    
    if not thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    # Handle both absolute and relative paths
    if not os.path.isabs(thumbnail_path):
        # If relative, try to resolve it relative to thumbnail directory
        thumbnail_path = os.path.join(settings.THUMBNAIL_DIR, os.path.basename(thumbnail_path))
    
    # Convert to absolute path for FileResponse
    thumbnail_path = os.path.abspath(thumbnail_path)
    
    if not os.path.exists(thumbnail_path):
        logger.warning(f"Thumbnail file not found at path: {thumbnail_path}")
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")
    
    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg",
        filename=f"thumb_{document_id}.jpg"
    )


@router.get("")
async def list_documents(
    case_id: str = Query(..., description="Case ID (integer)"),
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List documents for a case (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    # Convert case_id to integer
    try:
        case_id_int = int(case_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid case_id format")
    
    # Verify case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == case_id_int,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    
    # Query documents for this case that were uploaded by the current user
    # Users only see documents they uploaded
    # Filter out archived documents
    documents = db.query(Document).filter(
        Document.case_id == case_id_int,
        Document.uploaded_by == user_id,
        Document.is_archived == False
    ).order_by(Document.id.desc()).offset(skip).limit(limit).all()
    
    return documents


@router.get("/{document_id}")
async def get_document(
    document_id: str,  # Integer ID as string
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get a specific document (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    # Convert document_id to integer
    try:
        doc_id_int = int(document_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid document_id format")
    
    # Get document
    document = db.query(Document).filter(Document.id == doc_id_int).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant - this ensures tenant isolation
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


async def get_document_from_db(document_id, tenant_id: int = None, db: Session = None):
    """Get document from PostgreSQL database (with tenant isolation)
    
    Returns a dict with document fields, or None if not found
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        # Convert document_id to int if it's a string
        doc_id = int(document_id) if isinstance(document_id, str) else document_id
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            # Verify document's case belongs to tenant
            if tenant_id is not None:
                case = db.query(Case).filter(
                    Case.id == document.case_id,
                    Case.tenant_id == tenant_id
                ).first()
                if not case:
                    return None
            
            # Convert SQLAlchemy model to dict
            return {
                'id': document.id,
                'file_path': document.file_path,
                'original_filename': document.original_filename,
                'file_type': document.file_type,
                'extracted_text': document.extracted_text,
                'status': document.status,
                'thumbnail_path': document.thumbnail_path,
                'case_id': document.case_id
            }
    except ValueError:
        logger.error(f"Invalid document_id format: {document_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching document from database: {e}")
        return None
    finally:
        if should_close:
            db.close()
    return None


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,  # Can be UUID string or integer
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get document content including extracted text (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    # Convert document_id to integer
    try:
        doc_id_int = int(document_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid document_id format")
    
    # Get document with tenant isolation
    document = db.query(Document).filter(Document.id == doc_id_int).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document was uploaded by the current user
    if document.uploaded_by != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Risk assessment
    if settings.RISK_ENABLED:
        try:
            risk_engine = RiskEngine(
                profile_a_max=settings.RISK_PROFILE_A_MAX,
                profile_b_max=settings.RISK_PROFILE_B_MAX,
                profile_c_max=settings.RISK_PROFILE_C_MAX
            )
            
            extracted_text = document.extracted_text or ""
            risk_score = risk_engine.assess_risk(
                text=extracted_text,
                action="GET /api/v1/documents/{id}/content",
                document_metadata={"file_type": document.file_type}
            )
            
            # Immutable logging for Profile C only
            if risk_score.requires_logging:
                case_id = document.case_id
                log_immutable_audit(
                    db=db,
                    user_id=user_id,
                    action="document_content_access",
                    document_id=str(document_id),
                    risk_score={
                        "total_score": risk_score.total_score,
                        "profile": risk_score.governance_profile.value,
                        "pii_detected": risk_score.pii_detected,
                        "legal_signals": risk_score.legal_signals,
                        "intent_risk": risk_score.intent_risk,
                        "data_sensitivity_score": risk_score.data_sensitivity_score
                    },
                    case_id=str(case_id) if case_id else None
                )
        except Exception as e:
            logger.warning(f"Risk assessment failed for document {document_id}: {e}", exc_info=True)
            # Continue with request even if risk assessment fails
    
    # Increment view count
    try:
        document.view_count = (document.view_count or 0) + 1
        db.commit()
        logger.info(f"Incremented view count for document {doc_id_int} to {document.view_count}")
    except Exception as e:
        logger.warning(f"Failed to increment view count for document {doc_id_int}: {e}")
        db.rollback()
        # Continue even if view count increment fails
    
    return {
        "id": document.id,
        "extracted_text": document.extracted_text or "",
        "status": document.status or 'pending',
        "file_type": document.file_type or 'pdf'
    }


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,  # Can be UUID string or integer
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Serve the actual document file (tenant-isolated)"""
    from fastapi.responses import FileResponse
    
    user_id, tenant_id = user_tenant
    
    # Convert document_id to integer
    try:
        doc_id_int = int(document_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid document_id format")
    
    # Get document with tenant isolation
    document = db.query(Document).filter(Document.id == doc_id_int).first()
    if not document:
        logger.warning(f"Document {doc_id_int} not found in database (get_document_file)")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document was uploaded by the current user
    if document.uploaded_by != user_id:
        logger.warning(f"Document {doc_id_int} access denied: uploaded_by={document.uploaded_by}, current_user={user_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        logger.warning(f"Document {doc_id_int} access denied: case {document.case_id} not found or not created by user {user_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Risk assessment
    if settings.RISK_ENABLED:
        try:
            risk_engine = RiskEngine(
                profile_a_max=settings.RISK_PROFILE_A_MAX,
                profile_b_max=settings.RISK_PROFILE_B_MAX,
                profile_c_max=settings.RISK_PROFILE_C_MAX
            )
            
            extracted_text = document.extracted_text or ""
            risk_score = risk_engine.assess_risk(
                text=extracted_text,
                action="GET /api/v1/documents/{id}/file",
                document_metadata={"file_type": document.file_type}
            )
            
            # Immutable logging for Profile C only
            if risk_score.requires_logging:
                log_immutable_audit(
                    db=db,
                    user_id=user_id,
                    action="document_file_access",
                    document_id=str(document_id),
                    risk_score={
                        "total_score": risk_score.total_score,
                        "profile": risk_score.governance_profile.value,
                        "pii_detected": risk_score.pii_detected,
                        "legal_signals": risk_score.legal_signals,
                        "intent_risk": risk_score.intent_risk,
                        "data_sensitivity_score": risk_score.data_sensitivity_score
                    },
                    case_id=str(document.case_id)
                )
        except Exception as e:
            logger.warning(f"Risk assessment failed for document {document_id}: {e}", exc_info=True)
            # Continue with request even if risk assessment fails
    
    file_path = document.file_path
    if not file_path:
        raise HTTPException(status_code=404, detail="Document file path not found")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document file not found on disk: {file_path}")
    
    # Determine media type
    media_type_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "txt": "text/plain"
    }
    
    file_type = (document.file_type or 'pdf').lower()
    media_type = media_type_map.get(file_type, "application/octet-stream")
    original_filename = document.original_filename or f'document.{file_type}'
    
    # Increment view count
    try:
        document.view_count = (document.view_count or 0) + 1
        db.commit()
        logger.info(f"Incremented view count for document {doc_id_int} to {document.view_count}")
    except Exception as e:
        logger.warning(f"Failed to increment view count for document {doc_id_int}: {e}")
        db.rollback()
        # Continue even if view count increment fails
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=original_filename
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Delete a document (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document was uploaded by the current user
    if document.uploaded_by != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Risk assessment before deletion
    if settings.RISK_ENABLED:
        try:
            risk_engine = RiskEngine(
                profile_a_max=settings.RISK_PROFILE_A_MAX,
                profile_b_max=settings.RISK_PROFILE_B_MAX,
                profile_c_max=settings.RISK_PROFILE_C_MAX
            )
            
            extracted_text = document.extracted_text or ""
            risk_score = risk_engine.assess_risk(
                text=extracted_text,
                action="DELETE /api/v1/documents/{id}",
                document_metadata={"file_type": document.file_type}
            )
            
            # Immutable logging for Profile C only (before deletion)
            if risk_score.requires_logging:
                log_immutable_audit(
                    db=db,
                    user_id=user_id,
                    action="document_delete",
                    document_id=str(document_id),
                    risk_score={
                        "total_score": risk_score.total_score,
                        "profile": risk_score.governance_profile.value,
                        "pii_detected": risk_score.pii_detected,
                        "legal_signals": risk_score.legal_signals,
                        "intent_risk": risk_score.intent_risk,
                        "data_sensitivity_score": risk_score.data_sensitivity_score
                    },
                    case_id=str(document.case_id) if document.case_id else None
                )
        except Exception as e:
            logger.warning(f"Risk assessment failed for document {document_id}: {e}", exc_info=True)
            # Continue with deletion even if risk assessment fails
    
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
        try:
            vs = VectorStore()
            vs.delete_documents(chunk_ids)
        except Exception as e:
            logger.warning(f"Error deleting chunks from vector store: {e}")
    
    # Set document_id to NULL in immutable audit logs before deletion
    # This preserves the audit trail while allowing document deletion
    try:
        from app.models.audit import ImmutableAuditLog
        db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.document_id == document_id
        ).update({ImmutableAuditLog.document_id: None})
        db.flush()
    except Exception as e:
        logger.warning(f"Error updating audit logs before document deletion: {e}")
        # Continue with deletion even if audit log update fails
    
    # Delete from database (cascade will handle chunks)
    db.delete(document)
    db.commit()
    
    return None


@router.post("/{document_id}/archive", response_model=DocumentResponse)
async def archive_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Archive a document (soft delete, immutable for blockchain)"""
    from datetime import datetime
    user_id, tenant_id = user_tenant
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document was uploaded by the current user
    if document.uploaded_by != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if already archived
    if document.is_archived:
        raise HTTPException(status_code=400, detail="Document is already archived")
    
    # Risk assessment before archiving
    if settings.RISK_ENABLED:
        try:
            risk_engine = RiskEngine(
                profile_a_max=settings.RISK_PROFILE_A_MAX,
                profile_b_max=settings.RISK_PROFILE_B_MAX,
                profile_c_max=settings.RISK_PROFILE_C_MAX
            )
            
            extracted_text = document.extracted_text or ""
            risk_score = risk_engine.assess_risk(
                text=extracted_text,
                action="ARCHIVE /api/v1/documents/{id}",
                document_metadata={"file_type": document.file_type}
            )
            
            # Immutable logging for Profile C only (before archiving)
            if risk_score.requires_logging:
                log_immutable_audit(
                    db=db,
                    user_id=user_id,
                    action="document_archive",
                    document_id=str(document_id),
                    risk_score={
                        "total_score": risk_score.total_score,
                        "profile": risk_score.governance_profile.value,
                        "pii_detected": risk_score.pii_detected,
                        "legal_signals": risk_score.legal_signals,
                        "intent_risk": risk_score.intent_risk,
                        "data_sensitivity_score": risk_score.data_sensitivity_score
                    },
                    case_id=str(document.case_id) if document.case_id else None
                )
        except Exception as e:
            logger.warning(f"Risk assessment failed for document {document_id}: {e}", exc_info=True)
            # Continue with archiving even if risk assessment fails
    
    # Archive the document (soft delete)
    document.is_archived = True
    document.archived_at = datetime.now()
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Document archived: {document_id} by user {user_id}")
    return document


@router.get("/{document_id}/diagnostics")
async def get_document_diagnostics(
    document_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get diagnostic information about document processing status"""
    user_id, tenant_id = user_tenant
    
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify document's case belongs to tenant
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Count chunks in database
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    
    # Check vector store
    vector_store_chunks = 0
    vector_store_sample_metadata = None
    try:
        from app.services.vector_store import VectorStore
        from app.services.embedding_service import EmbeddingService
        
        vector_store = VectorStore()
        embedding_service = EmbeddingService()
        
        # Count total chunks in vector store
        total_count = vector_store.collection.count() if hasattr(vector_store, 'collection') else 0
        
        # Try to find chunks for this document
        if chunk_count > 0 and total_count > 0:
            # Get a sample chunk to create a test embedding
            sample_chunk = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).first()
            if sample_chunk and document.extracted_text:
                # Use document text to create embedding
                test_text = document.extracted_text[:100] if len(document.extracted_text) > 100 else document.extracted_text
                test_embedding = embedding_service.embed_text(test_text)
                
                # Search for chunks with document_id filter
                filter_metadata = {"document_id": document_id}
                if tenant_id is not None:
                    filter_metadata["tenant_id"] = tenant_id
                
                results = vector_store.search(
                    query_embedding=test_embedding,
                    top_k=10,
                    filter_metadata=filter_metadata
                )
                vector_store_chunks = len(results)
                if results:
                    vector_store_sample_metadata = results[0].get('metadata', {})
    except Exception as e:
        logger.error(f"Error checking vector store: {e}", exc_info=True)
    
    return {
        "document_id": document_id,
        "status": document.status,
        "error_message": document.error_message,
        "processed_at": document.processed_at.isoformat() if document.processed_at else None,
        "chunks_in_database": chunk_count,
        "chunks_in_vector_store": vector_store_chunks,
        "total_chunks_in_vector_store": total_count if 'total_count' in locals() else 0,
        "sample_metadata": vector_store_sample_metadata,
        "file_exists": os.path.exists(document.file_path) if document.file_path else False,
        "has_extracted_text": bool(document.extracted_text),
        "extracted_text_length": len(document.extracted_text) if document.extracted_text else 0
    }


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Reprocess a failed or existing document (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify case belongs to tenant
    case = db.query(Case).filter(
        Case.id == document.case_id,
        Case.tenant_id == tenant_id
    ).first()
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
                vs = VectorStore()
                vs.delete_documents(chunk_ids)
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
    
    # Queue for reprocessing using threading (consistent with upload endpoint)
    import threading
    
    thread = threading.Thread(
        target=process_document_background,
        args=(document.id, document.file_path, document.file_type, document.case_id, tenant_id),
        daemon=True,
        name=f"doc-reprocessor-{document.id}"
    )
    thread.start()
    logger.info(f"Document {document.id} reprocessing started in thread {thread.name}")
    
    return document

