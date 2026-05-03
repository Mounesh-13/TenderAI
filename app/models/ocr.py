from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OCRPage(BaseModel):
    page_number: int
    text: str
    confidence: float

class OCRResult(BaseModel):
    document_id: str
    pages: List[OCRPage]
    total_pages: int
    processed_at: datetime = datetime.now()
    engine: str

class OCRRequest(BaseModel):
    document_id: str
