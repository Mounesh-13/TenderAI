import os
import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLogEntry, AuditTrail
from app.models.db_models import DBAuditLog
from app.config import settings

class AuditService:
    def __init__(self, audit_dir: str = settings.AUDIT_DIR):
        self.audit_dir = audit_dir
        self.log_file = os.path.join(self.audit_dir, "audit_trail.json")
        if not os.path.exists(self.audit_dir):
            os.makedirs(self.audit_dir)

    async def log_action(
        self, 
        db: Session,
        action: str, 
        user: str, 
        changes: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> DBAuditLog:
        """
        Logs an action to both the database and an append-only JSON file.
        """
        db_entry = DBAuditLog(
            action=action,
            user=user,
            timestamp=datetime.utcnow(),
            changes=changes,
            document_id=document_id
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        # File-based append-only JSON log
        log_entry = {
            "timestamp": db_entry.timestamp.isoformat(),
            "action": action,
            "user": user,
            "changes": changes,
            "document_id": document_id
        }

        # We append to the file. For a true JSON log, usually it's one JSON object per line (JSONL)
        # or we read/write the whole array (less efficient). 
        # Requirement says "append-only JSON log", so JSONL is the industry standard for this.
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return db_entry

    async def get_audit_trail(self, db: Session, document_id: Optional[str] = None) -> AuditTrail:
        query = db.query(DBAuditLog)
        if document_id:
            query = query.filter(DBAuditLog.document_id == document_id)
        
        logs = query.order_by(DBAuditLog.timestamp).all()
        
        history = [
            AuditLogEntry(
                timestamp=log.timestamp,
                action=log.action,
                user=log.user,
                changes=log.changes,
                document_id=log.document_id
            ) for log in logs
        ]
        
        return AuditTrail(logs=history)

audit_service = AuditService()
