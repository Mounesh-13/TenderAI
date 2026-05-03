from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Entity(BaseModel):
    text: str
    label: str  # e.g., ORG, DATE, MONEY, REQUIREMENT
    start_char: int
    end_char: int

class Requirement(BaseModel):
    id: str
    description: str
    priority: str  # e.g., Mandatory, Desirable
    category: str  # e.g., Technical, Financial, Legal

class TenderCriterion(BaseModel):
    id: str
    type: str  # FINANCIAL / TECHNICAL / COMPLIANCE
    description: str
    threshold: Optional[str] = None
    comparator: Optional[str] = None

class NLPAnalysisResult(BaseModel):
    document_id: str
    entities: List[Entity]
    requirements: List[Requirement]
    summary: str
    analyzed_at: datetime = datetime.now()

class NLPRequest(BaseModel):
    document_id: str
