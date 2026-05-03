from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileMetadata(BaseModel):
    filename: str
    content_type: str
    size: int
    file_type: str  # digital_pdf, scanned_pdf, image, docx, unknown
    pages: int
    quality_score: float
    upload_timestamp: datetime = datetime.now()
    document_id: Optional[str] = None
    status: str = "uploaded"

class UploadResponse(BaseModel):
    message: str
    metadata: FileMetadata
