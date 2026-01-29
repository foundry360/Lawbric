"""
Case management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Tuple

from app.core.database import get_db
from app.core.auth import get_current_user_and_tenant, get_current_user_id
from app.models.case import Case, CaseNote, CaseNoteVersion
from app.models.user import User
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseNoteCreate, CaseNoteUpdate, CaseNoteResponse, CaseNoteVersionResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Create a new case"""
    user_id, tenant_id = user_tenant
    
    case = Case(
        name=case_data.name,
        case_number=case_data.case_number,
        description=case_data.description,
        created_by=user_id,
        tenant_id=tenant_id
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    logger.info(f"Case created: {case.id} by user {user_id} in tenant {tenant_id}")
    return case


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant),
    skip: int = 0,
    limit: int = 100
):
    """List all cases created by the current user (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    # Users only see cases they created
    cases = db.query(Case).filter(
        Case.tenant_id == tenant_id,
        Case.created_by == user_id,
        Case.is_active == True
    ).offset(skip).limit(limit).all()
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get a specific case (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    # Users can only access cases they created
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Update a case (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    # Users can only update cases they created
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = case_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Delete (deactivate) a case (user-isolated within tenant)"""
    user_id, tenant_id = user_tenant
    
    # Users can only delete cases they created
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.is_active = False
    db.commit()
    return None


# Case Notes Endpoints
@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_case_note(
    case_id: int,
    note_data: CaseNoteCreate,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Create a case note from AI query or manual entry"""
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Validate title is provided
    if not note_data.title or not note_data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    
    case_note = CaseNote(
        case_id=case_id,
        user_id=user_id,
        title=note_data.title.strip(),
        content=note_data.content,
        source_query_id=note_data.source_query_id,
        note_type=note_data.note_type or "ai_generated",
        privilege_tag=note_data.privilege_tag,
        is_non_authoritative=note_data.is_non_authoritative if note_data.is_non_authoritative is not None else False,
        source_document_links=note_data.source_document_links
    )
    db.add(case_note)
    db.commit()
    db.refresh(case_note)
    
    logger.info(f"Case note created: {case_note.id} for case {case_id} by user {user_id}")
    return case_note


@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_case_notes(
    case_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """List all notes for a case"""
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get all notes for this case (exclude archived notes)
    notes = db.query(CaseNote).filter(
        CaseNote.case_id == case_id,
        CaseNote.is_archived == False
    ).order_by(CaseNote.created_at.desc()).all()
    
    return notes


@router.get("/{case_id}/notes/{note_id}", response_model=CaseNoteResponse)
async def get_case_note(
    case_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get a specific case note"""
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    note = db.query(CaseNote).filter(
        CaseNote.id == note_id,
        CaseNote.case_id == case_id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Case note not found")
    
    return note


@router.put("/{case_id}/notes/{note_id}", response_model=CaseNoteResponse)
async def update_case_note(
    case_id: int,
    note_id: int,
    note_data: CaseNoteUpdate,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Update a case note and save version history"""
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    note = db.query(CaseNote).filter(
        CaseNote.id == note_id,
        CaseNote.case_id == case_id,
        CaseNote.user_id == user_id  # Users can only edit their own notes
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Case note not found")
    
    # Create version snapshot before updating
    # Get the next version number
    max_version = db.query(CaseNoteVersion).filter(
        CaseNoteVersion.note_id == note_id
    ).count()
    
    version = CaseNoteVersion(
        note_id=note_id,
        version_number=max_version + 1,
        title=note.title,
        content=note.content,
        privilege_tag=note.privilege_tag,
        is_non_authoritative=note.is_non_authoritative,
        edited_by=user_id,
        change_summary=note_data.change_summary
    )
    db.add(version)
    
    # Update the note
    update_data = note_data.dict(exclude_unset=True, exclude={'change_summary'})
    for field, value in update_data.items():
        setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    
    logger.info(f"Case note updated: {note_id} by user {user_id}, version {version.version_number}")
    return note


@router.post("/{case_id}/notes/{note_id}/archive", response_model=CaseNoteResponse)
async def archive_case_note(
    case_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Archive a case note (soft delete - immutable for blockchain)"""
    from datetime import datetime
    
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    note = db.query(CaseNote).filter(
        CaseNote.id == note_id,
        CaseNote.case_id == case_id,
        CaseNote.user_id == user_id,  # Users can only archive their own notes
        CaseNote.is_archived == False  # Can't archive an already archived note
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Case note not found or already archived")
    
    # Create version snapshot before archiving
    # Get the next version number
    max_version = db.query(CaseNoteVersion).filter(
        CaseNoteVersion.note_id == note_id
    ).count()
    
    version = CaseNoteVersion(
        note_id=note_id,
        version_number=max_version + 1,
        title=note.title,
        content=note.content,
        privilege_tag=note.privilege_tag,
        is_non_authoritative=note.is_non_authoritative,
        edited_by=user_id,
        change_summary="Note archived - immutable state for blockchain"
    )
    db.add(version)
    
    # Archive the note (soft delete)
    note.is_archived = True
    note.archived_at = datetime.now()
    
    db.commit()
    db.refresh(note)
    
    logger.info(f"Case note archived: {note_id} by user {user_id}, version {version.version_number} created")
    return note


@router.get("/{case_id}/notes/{note_id}/versions", response_model=List[CaseNoteVersionResponse])
async def get_case_note_versions(
    case_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    user_tenant: Tuple[int, int] = Depends(get_current_user_and_tenant)
):
    """Get version history for a case note"""
    user_id, tenant_id = user_tenant
    
    # Verify case access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == tenant_id,
        Case.created_by == user_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Verify note exists and belongs to the case
    note = db.query(CaseNote).filter(
        CaseNote.id == note_id,
        CaseNote.case_id == case_id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Case note not found")
    
    # Get all versions ordered by version number descending (newest first)
    versions = db.query(CaseNoteVersion).filter(
        CaseNoteVersion.note_id == note_id
    ).order_by(CaseNoteVersion.version_number.desc()).all()
    
    return versions

