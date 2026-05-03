from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.models.ingestion import UploadResponse
from app.services.ingestion_service import ingestion_service
from app.services.audit_service import audit_service
from app.database import get_db
from app.models.db_models import DBDocument

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_tender_document(
    file: UploadFile = File(...), 
    doc_type: str = "bidder", 
    parent_tender_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Validate file type (PDF, DOCX, Images)
    allowed_extensions = [".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    try:
        metadata = await ingestion_service.save_file(file)
        
        # Save to Documents table
        db_doc = DBDocument(
            id=metadata.document_id,
            filename=metadata.filename,
            content_type=metadata.content_type,
            size=metadata.size,
            file_type=metadata.file_type,
            pages=metadata.pages,
            quality_score=metadata.quality_score,
            status=metadata.status,
            doc_type=doc_type,
            parent_tender_id=parent_tender_id
        )
        db.add(db_doc)
        db.commit()

        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="DOCUMENT_UPLOADED",
            user="System/User",
            document_id=metadata.document_id,
            changes={"filename": metadata.filename, "file_type": metadata.file_type}
        )

        return UploadResponse(
            message="File uploaded and classified successfully",
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
