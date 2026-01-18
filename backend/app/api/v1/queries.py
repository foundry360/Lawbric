"""
Query endpoints for AI-powered legal analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.database import get_db
from app.core.security import verify_token
from app.models.case import Case, Query
from app.schemas.case import QueryRequest, QueryResponse, Citation
from app.services.rag_service import RAGService
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

rag_service = RAGService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Get current user ID from token"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))


@router.post("", response_model=QueryResponse)
async def create_query(
    query_data: QueryRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Ask a question about case documents"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == query_data.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Query RAG service
    result = rag_service.query(
        question=query_data.question,
        case_id=query_data.case_id,
        top_k=10,
        max_citations=query_data.max_citations
    )
    
    # Convert citations to proper format
    citations = [
        Citation(**citation) for citation in result["citations"]
    ]
    
    # Save query to database
    query = Query(
        case_id=query_data.case_id,
        user_id=user_id,
        question=query_data.question,
        query_type=query_data.query_type,
        answer=result["answer"],
        confidence_score=json.dumps(result["confidence_score"]) if result["confidence_score"] else None,
        citations=json.dumps([c.dict() for c in citations])
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    
    logger.info(f"Query created: {query.id} for case {query_data.case_id}")
    
    return QueryResponse(
        id=query.id,
        question=query.question,
        answer=query.answer,
        citations=citations,
        confidence_score=result["confidence_score"],
        query_type=query.query_type,
        created_at=query.created_at
    )


@router.get("", response_model=List[QueryResponse])
async def list_queries(
    case_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 50
):
    """List queries for a case"""
    queries = db.query(Query).filter(
        Query.case_id == case_id
    ).order_by(Query.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    results = []
    for query in queries:
        citations = []
        if query.citations:
            citations = [Citation(**c) for c in json.loads(query.citations)]
        
        results.append(QueryResponse(
            id=query.id,
            question=query.question,
            answer=query.answer,
            citations=citations,
            confidence_score=json.loads(query.confidence_score) if query.confidence_score else None,
            query_type=query.query_type,
            created_at=query.created_at
        ))
    
    return results


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get a specific query"""
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    citations = []
    if query.citations:
        citations = [Citation(**c) for c in json.loads(query.citations)]
    
    return QueryResponse(
        id=query.id,
        question=query.question,
        answer=query.answer,
        citations=citations,
        confidence_score=json.loads(query.confidence_score) if query.confidence_score else None,
        query_type=query.query_type,
        created_at=query.created_at
    )

