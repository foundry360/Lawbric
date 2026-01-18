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
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    requires_ocr: bool
    ocr_completed: bool
    is_privileged: bool
    is_redacted: bool
    uploaded_by: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Citation(BaseModel):
    """Citation schema for source references"""
    document_id: int
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


