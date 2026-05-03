from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.ocr import OCRResult, OCRRequest
from app.services.ocr_service import ocr_service
from app.services.audit_service import audit_service
from app.database import get_db

router = APIRouter()

@router.post("/process", response_model=OCRResult)
async def process_ocr(request: OCRRequest, db: Session = Depends(get_db)):
    try:
        # Check if file exists in uploads (logic would be here)
        result = await ocr_service.process_document(db, request.document_id)
        
        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="OCR_PROCESSED",
            user="System",
            document_id=request.document_id,
            changes={"engine": result.engine, "total_pages": result.total_pages}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Processing failed: {str(e)}")
