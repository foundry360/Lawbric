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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="case", cascade="all, delete-orphan")


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
    
    # Metadata
    bates_number = Column(String, nullable=True, index=True)
    custodian = Column(String, nullable=True)
    author = Column(String, nullable=True)
    document_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, nullable=True)
    
    # Processing status
    status = Column(String, default="pending")  # pending, processing, processed, error
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
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
    metadata = Column(Text, nullable=True)  # JSON string with additional metadata
    
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



