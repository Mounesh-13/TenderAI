from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.evaluation import EvaluationResult

class BidderComparisonItem(BaseModel):
    document_id: str
    filename: str
    overall_score: float
    status: str
    verdict: Optional[str] = None
    criteria_breakdown: Dict[str, float] # criterion_id -> score

class ComparisonReport(BaseModel):
    tender_id: str
    tender_filename: str
    generated_at: datetime = datetime.now()
    bidders: List[BidderComparisonItem]
    ranking: List[str] # List of document_ids in order of score
