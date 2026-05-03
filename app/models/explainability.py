from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EvidenceChainItem(BaseModel):
    criterion_id: str
    criterion_text: str
    extracted_value: str
    comparison_result: str  # e.g., PASS, FAIL, REVIEW
    source_page: int
    summary: str  # Human-readable chain: "Criterion → Extracted (Page) → Result"

class DocumentEvidenceChain(BaseModel):
    document_id: str
    chains: List[EvidenceChainItem]
    generated_at: datetime = datetime.now()
