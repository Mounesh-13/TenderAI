from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.hitl import HITLReview, HITLReviewRequest
from app.models.evaluation import EvaluationResult
from app.services.hitl_service import hitl_service
from app.database import get_db
from app.models.db_models import DBDocument
from typing import List

router = APIRouter()

@router.get("/review-items", response_model=List[dict])
async def get_review_items(db: Session = Depends(get_db)):
    """
    GET /review-items: Returns documents that require manual review.
    """
    docs = db.query(DBDocument).filter(DBDocument.status == "processed").all()
    return [{"id": d.id, "filename": d.filename, "status": d.status} for d in docs]

@router.post("/review", response_model=HITLReview)
async def submit_human_review(request: HITLReviewRequest, db: Session = Depends(get_db)):
    """
    POST /review: Submits an expert decision and reason.
    """
    try:
        # Note: Audit logging is handled inside hitl_service.submit_review
        return await hitl_service.submit_review(db, request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HITL Review submission failed: {str(e)}")
