from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.nlp import NLPAnalysisResult, NLPRequest, TenderCriterion
from app.services.nlp_service import nlp_service
from app.services.criteria_extraction_service import criteria_extraction_service
from app.services.bidder_entity_service import bidder_entity_service
from app.services.audit_service import audit_service
from app.database import get_db
from typing import List, Any, Dict

router = APIRouter()

@router.post("/analyze", response_model=NLPAnalysisResult)
async def analyze_tender(request: NLPRequest, db: Session = Depends(get_db)):
    try:
        result = await nlp_service.analyze_document(request.document_id)
        
        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="NLP_ANALYZED",
            user="System",
            document_id=request.document_id,
            changes={"entity_count": len(result.entities), "requirement_count": len(result.requirements)}
        )
        
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP Analysis failed: {str(e)}")

@router.post("/extract-criteria", response_model=List[TenderCriterion])
async def extract_tender_criteria(request: NLPRequest, db: Session = Depends(get_db)):
    try:
        # 1. Get OCR text
        from app.services.ocr_service import ocr_service
        ocr_result = await ocr_service.process_document(db, request.document_id)
        full_text = " ".join([page.text for page in ocr_result.pages])

        # 2. Run 3-Pass Pipeline with DB persistence
        result = await criteria_extraction_service.extract_criteria(db, request.document_id, full_text)
        
        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="CRITERIA_EXTRACTED",
            user="System",
            document_id=request.document_id,
            changes={"criteria_count": len(result)}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Criteria Extraction failed: {str(e)}")

@router.post("/extract-bidder-entities", response_model=Dict[str, Any])
async def extract_bidder_entities(request: NLPRequest, db: Session = Depends(get_db)):
    try:
        # 1. Get OCR text
        from app.services.ocr_service import ocr_service
        ocr_result = await ocr_service.process_document(db, request.document_id)
        full_text = " ".join([page.text for page in ocr_result.pages])

        # 2. Run Bidder Extraction
        result = await bidder_entity_service.extract_and_normalize(full_text, request.document_id)
        
        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="BIDDER_ENTITIES_EXTRACTED",
            user="System",
            document_id=request.document_id,
            changes={"org_count": len(result["organizations"]), "money_count": len(result["money"])}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bidder Entity Extraction failed: {str(e)}")
