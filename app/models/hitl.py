from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.evaluation import EvaluationResult, CriterionScore

class Correction(BaseModel):
    requirement_id: str
    corrected_score: float
    corrected_status: str
    expert_comment: str  # The "reason" for this specific correction

class HITLReview(BaseModel):
    document_id: str
    reviewer_id: str
    decision: str  # e.g., ELIGIBLE, NOT_ELIGIBLE
    reason: str    # Global reason for the decision
    corrections: List[Correction]
    original_evaluation: EvaluationResult
    final_overall_score: float
    reviewed_at: datetime = datetime.now()
    status: str = "completed"

class HITLReviewRequest(BaseModel):
    document_id: str
    reviewer_id: str
    decision: str  # ELIGIBLE or NOT_ELIGIBLE
    reason: str    # The expert's reason
    corrections: List[Correction] = []
