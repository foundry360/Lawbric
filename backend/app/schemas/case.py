"""
Pydantic schemas for Case-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CaseBase(BaseModel):
    """Base case schema"""
    name: str = Field(..., description="Case name")
    case_number: Optional[str] = Field(None, description="Case number")
    description: Optional[str] = Field(None, description="Case description")


class CaseCreate(CaseBase):
    """Schema for creating a case"""
    pass


class CaseUpdate(BaseModel):
    """Schema for updating a case"""
    name: Optional[str] = None
    case_number: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CaseResponse(CaseBase):
    """Schema for case response"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    bates_number: Optional[str] = None
    custodian: Optional[str] = None
    author: Optional[str] = None
    document_date: Optional[datetime] = None
    source: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    case_id: int


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    case_id: int
    status: str
    error_message: Optional[str] = None
    thumbnail_path: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    requires_ocr: bool
    ocr_completed: bool
    is_privileged: bool
    is_redacted: bool
    uploaded_by: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    view_count: int = 0
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Citation(BaseModel):
    """Citation schema for source references"""
    document_id: Optional[int] = None
    document_name: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    chunk_id: Optional[int] = None
    quoted_text: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    confidence: Optional[float] = None


class QueryRequest(BaseModel):
    """Schema for query request"""
    question: str = Field(..., description="The question to ask")
    case_id: int = Field(..., description="Case ID to query")
    query_type: Optional[str] = Field(None, description="Type of query: qa, summary, timeline, etc.")
    max_citations: int = Field(5, description="Maximum number of citations to return")
    document_id: Optional[int] = Field(None, description="Optional document ID to analyze specifically")
    show_sources: bool = Field(False, description="Whether to include sources array in the response")


class QueryResponse(BaseModel):
    """Schema for query response"""
    id: int
    question: str
    answer: str
    citations: List[Citation]
    confidence_score: Optional[dict] = None
    query_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CaseNoteCreate(BaseModel):
    """Schema for creating a case note"""
    title: str = Field(..., description="Note title (required)")
    content: str = Field(..., description="Note content")
    source_query_id: Optional[int] = Field(None, description="Link to original query if converted from AI")
    note_type: Optional[str] = Field("ai_generated", description="Type of note: ai_generated, manual")
    privilege_tag: Optional[str] = Field(None, description="Privilege level: Public, Confidential, Attorney-Client")
    is_non_authoritative: Optional[bool] = Field(False, description="Flagged as working notes, not evidence")
    source_document_links: Optional[str] = Field(None, description="JSON string with document links and page ranges")


class CaseNoteUpdate(BaseModel):
    """Schema for updating a case note"""
    title: Optional[str] = None
    content: Optional[str] = None
    privilege_tag: Optional[str] = None
    is_non_authoritative: Optional[bool] = None
    source_document_links: Optional[str] = None
    change_summary: Optional[str] = Field(None, description="Description of what changed in this version")


class CaseNoteVersionResponse(BaseModel):
    """Schema for case note version history response"""
    id: int
    note_id: int
    version_number: int
    title: str
    content: str
    privilege_tag: Optional[str]
    is_non_authoritative: bool
    edited_by: int
    change_summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CaseNoteResponse(BaseModel):
    """Schema for case note response"""
    id: int
    case_id: int
    user_id: int
    title: str
    content: str
    source_query_id: Optional[int]
    note_type: str
    privilege_tag: Optional[str]
    is_non_authoritative: bool
    source_document_links: Optional[str]
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True




