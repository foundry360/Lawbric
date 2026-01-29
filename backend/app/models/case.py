"""
Case and matter models for organizing legal documents
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Case(Base):
    """Case/Matter model"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    case_number = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Multi-tenant: Case belongs to a tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="case", cascade="all, delete-orphan")
    case_notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    """Document model for uploaded files"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt, etc.
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)  # Path to thumbnail image
    
    # Metadata
    bates_number = Column(String, nullable=True, index=True)
    custodian = Column(String, nullable=True)
    author = Column(String, nullable=True)
    document_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, nullable=True)
    
    # Processing status
    status = Column(String, default="pending")  # pending, processing, processed, error
    error_message = Column(Text, nullable=True)  # Error details if processing failed
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # View tracking
    view_count = Column(Integer, default=0, nullable=False)  # Number of times document has been viewed
    
    # Archiving (soft delete, immutable for blockchain)
    is_archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # OCR and text extraction
    requires_ocr = Column(Boolean, default=False)
    ocr_completed = Column(Boolean, default=False)
    extracted_text = Column(Text, nullable=True)
    
    # Security
    is_privileged = Column(Boolean, default=False)
    is_redacted = Column(Boolean, default=False)
    
    # Timestamps
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Chunks of documents for vector search"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)  # Character offset in original text
    end_char = Column(Integer, nullable=True)
    
    # Vector embedding
    embedding_id = Column(String, nullable=True, index=True)  # ID in vector DB
    
    # Metadata for retrieval
    chunk_metadata = Column(Text, nullable=True)  # JSON string with additional metadata
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class Query(Base):
    """User queries and AI responses"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Query
    question = Column(Text, nullable=False)
    query_type = Column(String, nullable=True)  # qa, summary, timeline, etc.
    
    # Response
    answer = Column(Text, nullable=True)
    confidence_score = Column(String, nullable=True)  # JSON with scores
    
    # Citations
    citations = Column(Text, nullable=True)  # JSON array of citations
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    case = relationship("Case", back_populates="queries")


class CaseNote(Base):
    """Case notes for storing attorney notes and AI-generated insights"""
    __tablename__ = "case_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Note content
    title = Column(String, nullable=False)  # Required title
    content = Column(Text, nullable=False)  # The AI answer/note content
    source_query_id = Column(Integer, ForeignKey("queries.id"), nullable=True)  # Link to original query if converted from AI
    
    # Metadata
    note_type = Column(String, default="ai_generated")  # ai_generated, manual, etc.
    privilege_tag = Column(String, nullable=True)  # Public, Confidential, Attorney-Client
    is_non_authoritative = Column(Boolean, default=False)  # Flagged as working notes, not evidence
    source_document_links = Column(Text, nullable=True)  # JSON string with document links and page ranges
    is_archived = Column(Boolean, default=False, nullable=False)  # Archived notes (soft delete, immutable for blockchain)
    archived_at = Column(DateTime(timezone=True), nullable=True)  # When the note was archived
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    case = relationship("Case", back_populates="case_notes")
    user = relationship("User")
    source_query = relationship("Query")
    versions = relationship("CaseNoteVersion", back_populates="note", cascade="all, delete-orphan", order_by="CaseNoteVersion.version_number.desc()")


class CaseNoteVersion(Base):
    """Version history for case notes"""
    __tablename__ = "case_note_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("case_notes.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # Incremental version number
    
    # Snapshot of note at this version
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    privilege_tag = Column(String, nullable=True)
    is_non_authoritative = Column(Boolean, default=False)
    
    # Version metadata
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_summary = Column(Text, nullable=True)  # Optional description of what changed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    note = relationship("CaseNote", back_populates="versions")
    editor = relationship("User")



