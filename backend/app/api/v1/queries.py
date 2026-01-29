"""
Query endpoints for AI-powered legal analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant, get_current_user_id
from app.core.config import settings
from app.models.case import Case, Query, Document
from app.schemas.case import QueryRequest, QueryResponse, Citation
from app.services.rag_service import RAGService
from app.services.risk_engine import RiskEngine
from app.utils.audit import log_immutable_audit
from typing import Tuple
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

rag_service = RAGService()


@router.post("", response_model=QueryResponse)
async def create_query(
    query_data: QueryRequest,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Ask a question about case documents (tenant-isolated)"""
    user_id, tenant_id = user_tenant
    
    # Verify case exists, belongs to tenant, and was created by the current user
    case = db.query(Case).filter(
        Case.id == query_data.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Risk assessment
    if settings.RISK_ENABLED:
        try:
            risk_engine = RiskEngine(
                profile_a_max=settings.RISK_PROFILE_A_MAX,
                profile_b_max=settings.RISK_PROFILE_B_MAX,
                profile_c_max=settings.RISK_PROFILE_C_MAX
            )
            
            # Get sample document text from case for sensitivity detection
            # Use first processed document's text that was uploaded by the current user
            sample_doc = db.query(Document).filter(
                Document.case_id == query_data.case_id,
                Document.status == "processed",
                Document.uploaded_by == user_id
            ).first()
            
            sample_text = sample_doc.extracted_text if sample_doc and sample_doc.extracted_text else ""
            
            risk_score = risk_engine.assess_risk(
                text=sample_text,
                prompt=query_data.question,
                action="POST /api/v1/queries",
                document_metadata={"case_id": query_data.case_id}
            )
            
            # Immutable logging for Profile C only
            if risk_score.requires_logging:
                # For queries, we may not have a specific document, so use case_id as document_id fallback
                doc_id = str(sample_doc.id) if sample_doc else str(query_data.case_id)
                log_immutable_audit(
                    db=db,
                    user_id=str(user_id),
                    action="query_submission",
                    document_id=doc_id,
                    risk_score={
                        "total_score": risk_score.total_score,
                        "profile": risk_score.governance_profile.value,
                        "pii_detected": risk_score.pii_detected,
                        "legal_signals": risk_score.legal_signals,
                        "intent_risk": risk_score.intent_risk,
                        "data_sensitivity_score": risk_score.data_sensitivity_score
                    },
                    metadata={"question": query_data.question, "case_id": query_data.case_id},
                    case_id=str(query_data.case_id)
                )
        except Exception as e:
            logger.warning(f"Risk assessment failed for query: {e}", exc_info=True)
            # Continue with query even if risk assessment fails
    
    # Query RAG service with tenant isolation
    result = rag_service.query(
        question=query_data.question,
        case_id=query_data.case_id,
        tenant_id=tenant_id,
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
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant),
    skip: int = 0,
    limit: int = 50
):
    """List queries for a case (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    # Verify case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Users only see queries they created for their own cases
    queries = db.query(Query).filter(
        Query.case_id == case_id,
        Query.user_id == user_id
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
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get a specific query (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Verify query was created by the current user
    if query.user_id != user_id:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Verify query's case belongs to tenant and was created by the current user
    case = db.query(Case).filter(
        Case.id == query.case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
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

