from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models.evaluation import EvaluationResult
from app.models.explainability import DocumentEvidenceChain

class DocumentReport(BaseModel):
    document_id: str
    filename: str
    status: str
    overall_score: float
    evaluation: EvaluationResult
    evidence_chain: DocumentEvidenceChain
    generated_at: datetime = datetime.now()

class DashboardSummary(BaseModel):
    total_documents: int
    processed_count: int
    pending_review: int
    recent_reports: List[Dict[str, Any]]
