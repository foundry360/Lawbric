"""
Query endpoints - ULTRA SIMPLIFIED VERSION
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime
import json
import logging

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant
from app.core.config import settings
from app.models.case import Case, Query, Document, CaseNote
from app.schemas.case import QueryRequest, QueryResponse, Citation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=QueryResponse)
async def create_query(
    query_data: QueryRequest,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Simple query endpoint - minimal complexity"""
    user_id, tenant_id = user_tenant
    
    # Verify case
    case = db.query(Case).filter(
        Case.id == query_data.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Try RAG service - if it fails, return a simple error
    try:
        from app.services.rag_service import RAGService
        rag_service = RAGService()
        rag_result = rag_service.query(
            question=query_data.question,
            case_id=query_data.case_id,
            tenant_id=tenant_id,
            document_id=query_data.document_id,  # Pass document_id to filter by specific document
            top_k=5,
            max_citations=5
        )
        
        # Build citations
        citations = []
        for cit in rag_result.get("citations", []):
            try:
                citations.append(Citation(
                    document_id=cit.get("document_id"),
                    document_name=cit.get("document_name", "Unknown"),
                    page_number=cit.get("page_number"),
                    quoted_text=cit.get("quoted_text", ""),
                    confidence=cit.get("confidence")
                ))
            except:
                pass
        
        # Save to database
        try:
            query = Query(
                case_id=query_data.case_id,
                user_id=user_id,
                question=query_data.question,
                query_type=query_data.query_type,
                answer=rag_result.get("answer", "No answer generated"),
                confidence_score=json.dumps(rag_result.get("confidence_score")),
                citations=json.dumps([c.dict() for c in citations])
            )
            db.add(query)
            db.commit()
            db.refresh(query)
            
            return QueryResponse(
                id=query.id,
                question=query.question,
                answer=query.answer,
                citations=citations,
                confidence_score=rag_result.get("confidence_score"),
                query_type=query.query_type,
                created_at=query.created_at
            )
        except Exception as db_err:
            logger.error(f"DB save failed: {db_err}")
            # Return without saving
            temp_id = int(datetime.now().timestamp() * 1000)
            return QueryResponse(
                id=temp_id,
                question=query_data.question,
                answer=rag_result.get("answer", "No answer generated"),
                citations=citations,
                confidence_score=rag_result.get("confidence_score"),
                query_type=query_data.query_type,
                created_at=datetime.now()
            )
            
    except Exception as e:
        # Simple error - no complex formatting
        error_str = str(e) if e else "Unknown error"
        logger.error(f"Query failed: {error_str}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {error_str}"
        )


@router.get("", response_model=List[QueryResponse])
async def list_queries(
    case_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant),
    skip: int = 0,
    limit: int = 50
):
    """List queries"""
    user_id, tenant_id = user_tenant
    
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    queries = db.query(Query).filter(
        Query.case_id == case_id,
        Query.user_id == user_id
    ).order_by(Query.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for query in queries:
        citations = []
        if query.citations:
            try:
                citations = [Citation(**c) for c in json.loads(query.citations)]
            except:
                pass
        
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
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get a query"""
    user_id, tenant_id = user_tenant
    
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query or query.user_id != user_id:
        raise HTTPException(status_code=404, detail="Query not found")
    
    case = db.query(Case).filter(
        Case.id == query.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Query not found")
    
    citations = []
    if query.citations:
        try:
            citations = [Citation(**c) for c in json.loads(query.citations)]
        except:
            pass
    
    return QueryResponse(
        id=query.id,
        question=query.question,
        answer=query.answer,
        citations=citations,
        confidence_score=json.loads(query.confidence_score) if query.confidence_score else None,
        query_type=query.query_type,
        created_at=query.created_at
    )


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query(
    query_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Delete a single query"""
    user_id, tenant_id = user_tenant
    
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Verify user owns the query
    if query.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this query")
    
    # Verify case belongs to user and tenant
    case = db.query(Case).filter(
        Case.id == query.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Clear source_query_id in case notes that reference this query
    db.query(CaseNote).filter(CaseNote.source_query_id == query_id).update(
        {CaseNote.source_query_id: None},
        synchronize_session=False
    )
    
    db.delete(query)
    db.commit()
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_queries(
    case_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Delete all queries for a case"""
    user_id, tenant_id = user_tenant
    
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get all query IDs that will be deleted
    query_ids = db.query(Query.id).filter(
        Query.case_id == case_id,
        Query.user_id == user_id
    ).all()
    query_ids = [q[0] for q in query_ids]
    
    # Clear source_query_id in case notes that reference these queries
    if query_ids:
        db.query(CaseNote).filter(CaseNote.source_query_id.in_(query_ids)).update(
            {CaseNote.source_query_id: None},
            synchronize_session=False
        )
    
    # Now delete the queries
    db.query(Query).filter(
        Query.case_id == case_id,
        Query.user_id == user_id
    ).delete(synchronize_session=False)
    
    db.commit()
    return None
