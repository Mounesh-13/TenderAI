from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.audit import AuditTrail
from app.services.audit_service import audit_service
from app.database import get_db

router = APIRouter()

@router.get("/trail/{document_id}", response_model=AuditTrail)
async def get_document_audit_trail(document_id: str, db: Session = Depends(get_db)):
    try:
        return await audit_service.get_audit_trail(db, document_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit trail: {str(e)}")
