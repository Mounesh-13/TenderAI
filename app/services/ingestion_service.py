import os
import shutil
import uuid
from datetime import datetime
from fastapi import UploadFile
from app.models.ingestion import FileMetadata
from app.config import settings

# Optional imports for classification
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from PIL import Image
except ImportError:
    Image = None

class IngestionService:
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def save_file(self, file: UploadFile) -> FileMetadata:
        document_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        saved_filename = f"{document_id}{file_ext}"
        file_path = os.path.join(self.upload_dir, saved_filename)

        # Temporary save to analyze
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)
        
        # Classification Logic
        file_type, pages, quality_score = self._classify_file(file_path, file_ext)

        metadata = FileMetadata(
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            file_type=file_type,
            pages=pages,
            quality_score=quality_score,
            document_id=document_id,
            upload_timestamp=datetime.now(),
            status="uploaded"
        )
        
        return metadata

    def _classify_file(self, file_path: str, ext: str):
        file_type = "unknown"
        pages = 1
        quality_score = 0.0

        if ext == ".pdf":
            file_type, pages, quality_score = self._analyze_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            file_type, pages, quality_score = self._analyze_docx(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            file_type, pages, quality_score = self._analyze_image(file_path)
        
        return file_type, pages, quality_score

    def _analyze_pdf(self, file_path: str):
        if not PdfReader:
            return "digital_pdf", 1, 0.5 # Fallback
        
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            text_content = ""
            # Check first 3 pages for text layer
            for i in range(min(num_pages, 3)):
                text_content += reader.pages[i].extract_text() or ""
            
            if len(text_content.strip()) > 50:
                return "digital_pdf", num_pages, 1.0
            else:
                return "scanned_pdf", num_pages, 0.7
        except Exception:
            return "scanned_pdf", 1, 0.4

    def _analyze_docx(self, file_path: str):
        if not Document:
            return "docx", 1, 0.8
        
        try:
            doc = Document(file_path)
            # docx doesn't easily give page count without rendering, 
            # we estimate based on paragraphs or use a placeholder
            pages = max(1, len(doc.paragraphs) // 20) 
            return "docx", pages, 0.9
        except Exception:
            return "docx", 1, 0.5

    def _analyze_image(self, file_path: str):
        if not Image:
            return "image", 1, 0.6
        
        try:
            with Image.open(file_path) as img:
                # Basic quality heuristic based on resolution
                width, height = img.size
                quality = min(1.0, (width * height) / (2000 * 2000))
                return "image", 1, round(quality, 2)
        except Exception:
            return "image", 1, 0.3

ingestion_service = IngestionService()
