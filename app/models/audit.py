from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class AuditLogEntry(BaseModel):
    timestamp: datetime = datetime.now()
    action: str  # e.g., EVALUATION, REVIEWER_ACTION
    user: str    # mock or real user ID
    changes: Optional[Dict[str, Any]] = None # Key details/diffs
    document_id: Optional[str] = None # Linking to document

class AuditTrail(BaseModel):
    logs: List[AuditLogEntry]
