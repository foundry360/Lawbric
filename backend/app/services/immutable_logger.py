"""
Immutable logging service for Profile C (high-risk) actions only
"""

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import logging
from sqlalchemy.orm import Session

from app.models.audit import ImmutableAuditLog

logger = logging.getLogger(__name__)


class ImmutableLogger:
    """Immutable logging service for Profile C actions only"""
    
    def __init__(self, storage_backend: str = "database"):
        """
        Initialize immutable logger
        
        Args:
            storage_backend: Storage backend type (currently only "database" supported)
        """
        self.storage_backend = storage_backend
    
    def log_action(
        self,
        db: Session,
        user_id: str,
        action: str,
        document_id: str,
        risk_score: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None
    ) -> str:
        """
        Create immutable log entry for Profile C actions
        
        Args:
            db: Database session
            user_id: User ID performing the action
            action: Action type (e.g., "document_access", "document_delete")
            document_id: Document ID being accessed/modified
            risk_score: Risk assessment details
            metadata: Additional metadata
            case_id: Optional case ID
        
        Returns:
            log_entry_id: Unique identifier for the log entry
        """
        log_entry_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "document_id": document_id,
            "risk_score": risk_score,
            "metadata": metadata or {},
        }
        
        if case_id:
            log_entry_data["case_id"] = case_id
        
        # Create hash for immutability verification
        log_hash = self._create_hash(log_entry_data)
        
        # Store in immutable storage
        log_entry_id = self._store_log(
            db=db,
            user_id=user_id,
            action=action,
            document_id=document_id,
            case_id=case_id,
            risk_score=risk_score,
            metadata=metadata,
            log_hash=log_hash
        )
        
        logger.info(f"Immutable log created: {log_entry_id} for Profile C action")
        return log_entry_id
    
    def _create_hash(self, log_entry: Dict[str, Any]) -> str:
        """Create SHA-256 hash of log entry for immutability"""
        # Remove hash field if present for hashing
        entry_copy = {k: v for k, v in log_entry.items() if k != "hash"}
        entry_json = json.dumps(entry_copy, sort_keys=True)
        return hashlib.sha256(entry_json.encode()).hexdigest()
    
    def _store_log(
        self,
        db: Session,
        user_id: str,
        action: str,
        document_id: str,
        log_hash: str,
        risk_score: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None
    ) -> str:
        """
        Store log entry in immutable storage (append-only database table)
        
        Args:
            db: Database session
            user_id: User ID
            action: Action type
            document_id: Document ID
            log_hash: SHA-256 hash of log entry
            risk_score: Risk assessment details
            metadata: Additional metadata
            case_id: Optional case ID
        
        Returns:
            log_entry_id: Database ID of the log entry
        """
        # Convert document_id and case_id to integers if they're numeric strings
        # Handle both UUID strings and integer IDs
        doc_id_int = None
        case_id_int = None
        
        try:
            if document_id and not isinstance(document_id, int):
                # Check if it's a UUID (contains dashes) or numeric
                if '-' not in str(document_id):
                    doc_id_int = int(document_id)
        except (ValueError, TypeError):
            pass
        
        try:
            if case_id and not isinstance(case_id, int):
                if '-' not in str(case_id):
                    case_id_int = int(case_id)
        except (ValueError, TypeError):
            pass
        
        # Store risk score and metadata as JSON
        risk_score_json = json.dumps(risk_score)
        metadata_json = json.dumps(metadata) if metadata else None
        
        immutable_log = ImmutableAuditLog(
            user_id=user_id,
            case_id=case_id_int,
            document_id=doc_id_int,
            action=action,
            resource_type="document",
            resource_id=doc_id_int,
            details=json.dumps({
                "risk_score": risk_score,
                "metadata": metadata or {},
                "log_hash": log_hash
            }),
            log_hash=log_hash
        )
        
        db.add(immutable_log)
        db.commit()
        db.refresh(immutable_log)
        
        return str(immutable_log.id)
    
    def verify_log_integrity(self, db: Session, log_entry_id: int) -> bool:
        """
        Verify log entry hasn't been tampered with
        
        Args:
            db: Database session
            log_entry_id: Log entry ID to verify
        
        Returns:
            True if hash matches, False if tampered
        """
        log_entry = db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.id == log_entry_id
        ).first()
        
        if not log_entry:
            return False
        
        # Reconstruct log entry data (excluding hash)
        log_entry_data = {
            "timestamp": log_entry.created_at.isoformat() if log_entry.created_at else None,
            "user_id": str(log_entry.user_id) if log_entry.user_id else None,
            "action": log_entry.action,
            "document_id": str(log_entry.document_id) if log_entry.document_id else None,
        }
        
        # Parse details to get risk_score
        if log_entry.details:
            try:
                details = json.loads(log_entry.details)
                log_entry_data["risk_score"] = details.get("risk_score", {})
                log_entry_data["metadata"] = details.get("metadata", {})
            except json.JSONDecodeError:
                pass
        
        # Recalculate hash
        recalculated_hash = self._create_hash(log_entry_data)
        
        # Compare with stored hash
        return recalculated_hash == log_entry.log_hash






