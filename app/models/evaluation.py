from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Evidence(BaseModel):
    requirement_id: str
    text_snippet: str
    page_number: int
    confidence_score: float

class CriterionScore(BaseModel):
    requirement_id: str
    score: float  # 0.0 to 1.0
    status: str  # e.g., Compliant, Partially Compliant, Non-Compliant
    reasoning: str
    evidence: List[Evidence]

class EvaluationResult(BaseModel):
    document_id: str
    overall_score: float
    criteria_scores: List[CriterionScore]
    evaluated_at: datetime = datetime.now()
    evaluator_engine: str

class EvaluationRequest(BaseModel):
    document_id: str
