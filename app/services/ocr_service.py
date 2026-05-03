import os
import json
import asyncio
from datetime import datetime
from typing import List

from app.models.ocr import OCRResult, OCRPage
from app.config import settings
from app.models.db_models import DBDocument
from sqlalchemy.orm import Session
from loguru import logger

# Extraction Libraries
import pdfplumber
import pytesseract
from PIL import Image, ImageOps, ImageFilter

class OCRService:
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR, output_dir: str = settings.OCR_DIR):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Configure Tesseract path if provided in settings
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    async def process_document(self, db: Session, document_id: str) -> OCRResult:
        """
        Processes a document based on its type (Digital PDF, Scanned PDF, Image, etc.)
        """
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not db_doc:
            raise FileNotFoundError(f"Document {document_id} not found in database.")

        file_ext = os.path.splitext(db_doc.filename)[1].lower()
        file_path = os.path.join(self.upload_dir, f"{document_id}{file_ext}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Physical file for document {document_id} not found at {file_path}")

        logger.info(f"Processing OCR for {document_id} (Type: {db_doc.file_type})")

        pages = []
        
        if db_doc.file_type == "digital_pdf":
            pages = self._extract_digital_pdf(file_path)
        elif db_doc.file_type == "scanned_pdf":
            # For scanned PDFs, in a real system we might use pdf2image then tesseract
            # For this prototype, we'll use pdfplumber's basic image extraction or a simplified flow
            # Simplifying: Treat first page as an image if it's scanned
            pages = self._extract_scanned_pdf(file_path)
        elif db_doc.file_type == "image":
            pages = [self._extract_image(file_path, page_num=1)]
        elif db_doc.file_type == "docx":
            # For docx, we just extract text using python-docx (already in reqs)
            pages = self._extract_docx(file_path)
        else:
            logger.warning(f"Unsupported file type for OCR: {db_doc.file_type}")

        result = OCRResult(
            document_id=document_id,
            pages=pages,
            total_pages=len(pages),
            processed_at=datetime.utcnow(),
            engine="TenderAI-OCR-v1"
        )

        # Persistence
        output_path = os.path.join(self.output_dir, f"{document_id}.json")
        with open(output_path, "w") as f:
            f.write(result.model_dump_json())

        return result

    def _extract_digital_pdf(self, file_path: str) -> List[OCRPage]:
        pages = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append(OCRPage(
                        page_number=i + 1,
                        text=text,
                        confidence=1.0  # Digital extraction is highly reliable
                    ))
        except Exception as e:
            logger.error(f"Failed digital PDF extraction: {str(e)}")
        return pages

    def _extract_scanned_pdf(self, file_path: str) -> List[OCRPage]:
        # NOTE: Real scanned PDF OCR requires converting pages to images first (e.g., via pdf2image)
        # To keep it simple without heavy dependencies like poppler, we attempt basic extraction
        # or log a limitation.
        logger.info("Scanned PDF detected. Attempting Tesseract OCR (requires poppler/pdf2image for full implementation).")
        # Placeholder: For this prototype, we'll extract images embedded in the PDF if any
        # or just return a mock with a note.
        return [OCRPage(page_number=1, text="[Scanned PDF content requires OCR processing]", confidence=0.0)]

    def _extract_image(self, file_path: str, page_num: int = 1) -> OCRPage:
        try:
            with Image.open(file_path) as img:
                # Preprocessing
                processed_img = self._preprocess_image(img)
                
                # OCR
                text = pytesseract.image_to_string(processed_img)
                
                # Mock confidence (Tesseract can provide it via get_data, but keeping it simple)
                return OCRPage(
                    page_number=page_num,
                    text=text,
                    confidence=0.8
                )
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            return OCRPage(page_number=page_num, text="", confidence=0.0)

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        # Grayscale
        img = img.convert('L')
        # Thresholding (Basic binary threshold)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        return img

    def _extract_docx(self, file_path: str) -> List[OCRPage]:
        # Simplified: Extract all text from docx as one page or split by paragraph
        from docx import Document
        pages = []
        try:
            doc = Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            pages.append(OCRPage(page_number=1, text=full_text, confidence=1.0))
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
        return pages

ocr_service = OCRService()
