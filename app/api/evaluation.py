from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationResult, EvaluationRequest
from app.services.evaluation_engine_service import evaluation_engine_service
from app.services.audit_service import audit_service
from app.database import get_db

router = APIRouter()

@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_tender(request: EvaluationRequest, db: Session = Depends(get_db)):
    try:
        result = await evaluation_engine_service.evaluate_bidder(request.document_id)
        
        # Log to Audit Layer
        await audit_service.log_action(
            db=db,
            action="BIDDER_EVALUATED",
            user="System",
            document_id=request.document_id,
            changes={"overall_score": result.overall_score, "engine": result.evaluator_engine}
        )
        
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
