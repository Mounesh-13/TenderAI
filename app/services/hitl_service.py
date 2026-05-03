import os
import json
from typing import List
from sqlalchemy.orm import Session
from app.models.hitl import HITLReview, HITLReviewRequest, Correction
from app.models.evaluation import EvaluationResult
from app.models.db_models import DBHITLReview, DBDocument
from app.services.audit_service import audit_service
from datetime import datetime
import asyncio
from app.config import settings

class HITLService:
    def __init__(self, eval_dir: str = settings.EVALUATION_DIR, hitl_dir: str = settings.HITL_DIR):
        self.eval_dir = eval_dir
        self.hitl_dir = hitl_dir
        if not os.path.exists(self.hitl_dir):
            os.makedirs(self.hitl_dir)

    async def get_evaluation_for_review(self, document_id: str) -> EvaluationResult:
        eval_path = os.path.join(self.eval_dir, f"{document_id}.json")
        if not os.path.exists(eval_path):
            raise FileNotFoundError(f"Evaluation for document {document_id} not found.")

        with open(eval_path, "r") as f:
            eval_data = json.load(f)
            return EvaluationResult(**eval_data)

    async def submit_review(self, db: Session, request: HITLReviewRequest) -> HITLReview:
        original_eval = await self.get_evaluation_for_review(request.document_id)
        await asyncio.sleep(1)

        # Apply corrections to calculate final overall score if provided
        final_overall_score = original_eval.overall_score
        if request.corrections:
            correction_map = {c.requirement_id: c for c in request.corrections}
            final_scores = []
            for crit in original_eval.criteria_scores:
                if crit.requirement_id in correction_map:
                    final_scores.append(correction_map[crit.requirement_id].corrected_score)
                else:
                    final_scores.append(crit.score)
            final_overall_score = sum(final_scores) / len(final_scores) if final_scores else 0.0

        # Save to DB
        db_review = DBHITLReview(
            document_id=request.document_id,
            reviewer_id=request.reviewer_id,
            decision=request.decision,
            reason=request.reason,
            corrections=[c.model_dump() for c in request.corrections],
            original_evaluation=original_eval.model_dump(),
            final_overall_score=final_overall_score,
            reviewed_at=datetime.utcnow(),
            status="completed"
        )
        db.add(db_review)

        # Update Document state
        db_doc = db.query(DBDocument).filter(DBDocument.id == request.document_id).first()
        if db_doc:
            db_doc.status = "completed"
            db_doc.final_verdict = request.decision
            db_doc.expert_reviewer_id = request.reviewer_id

        db.commit()
        db.refresh(db_review)

        # Log to Audit Trail
        await audit_service.log_action(
            db=db,
            document_id=request.document_id,
            action="HITL_REVIEW",
            actor=request.reviewer_id,
            status="SUCCESS",
            payload={
                "decision": request.decision,
                "reason": request.reason,
                "changes": [c.model_dump() for c in request.corrections]
            }
        )

        review_result = HITLReview(
            document_id=request.document_id,
            reviewer_id=request.reviewer_id,
            decision=request.decision,
            reason=request.reason,
            corrections=request.corrections,
            original_evaluation=original_eval,
            final_overall_score=final_overall_score,
            reviewed_at=db_review.reviewed_at,
            status="completed"
        )

        # Still maintaining file-based for backup
        output_path = os.path.join(self.hitl_dir, f"{request.document_id}.json")
        with open(output_path, "w") as f:
            f.write(review_result.model_dump_json())

        return review_result

hitl_service = HITLService()
